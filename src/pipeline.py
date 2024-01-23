import time
import json
import string
import random
import datetime

from typing import Union
from pathlib import Path
from langchain.prompts import PromptTemplate

from PySide6.QtCore import QObject, Signal, QThread, QCoreApplication

from src.utils import *
from src.agents import Agent, HumanConversationWrapper
from src.sandbox.instantiate import PythonSandbox, FrontendSandbox, DatabaseSandbox


class Pipeline(QObject):
    message_signal = Signal(str, str, bool)  # For communication with GUI thread
    animation_signal = Signal(str)  # layer, status, on/off

    def __init__(self, command_line_args, evaluate: bool = False):
        super().__init__()
        self._input = None
        self._pause_execution = False

        self.root = Path(__file__).parent.parent
        self.description = command_line_args.description
        self.fast_forward = command_line_args.fast_forward
        self.disable_gui = command_line_args.disable_gui
        self.evaulate = evaluate

        self.__metrics = self.__setup_metrics()
        self.__setup_agents()

    def __transmit_message_signal(self, sender, message, is_question=False):
        if self.disable_gui:
            print(f"\033[34m{sender}:\033[0m {message}")
            if is_question:
                terminal_input = input("\033[34mYour answer: \033[0m ")
                return terminal_input
        else:
            # send signal to gui thread
            self.message_signal.emit(sender, message, is_question)
            self._pause_execution = True
            while self._pause_execution:  # sleep until gui thread has responded
                QThread.msleep(100)
                QCoreApplication.processEvents()  # but check for incoming signals

            return self._input

    def __transmit_animation_signal(self, text):
        if self.disable_gui:
            print(f"\033[34mstatus\033[0m")
        else:
            self.animation_signal.emit(text)

    def receive_from_gui(self, input):
        self._input = input
        self._pause_execution = False

    def __setup_agents(self) -> None:
        """Create workforce using agents.json"""
        with open(self.root / "src/setup/agents.json", "r") as file:
            configs = json.load(file)

        for config in configs:
            setattr(
                self,
                config["varname"],
                Agent(
                    config=config,
                    root=self.root,
                ),
            )

    def __setup_metrics(self) -> dict:
        if self.evaulate:
            random.seed(0)
            
        return {
            "project_name": None,
            "time": 0,
            "turns_database": 0,
            "turns_backend": 0,
            "turns_frontend": 0,
            "working": 0,
            "human_feedback": 0,
        }

    def __add_metrics(self, key: str, value: Union[int, str]) -> None:
        self.__metrics[key] = value

    @property
    def metrics(self) -> None:
        return self.__metrics

    def __create_project_name(self, title: str = "Webapp") -> str:
        # Append 4 random chars at the end of the title, seperated by _
        return title + "_" + "".join(random.choices(string.ascii_lowercase, k=4))

    def start(self) -> None:
        """Start developing process"""
        # 0. Setup
        start_time = time.time()

        # 0a. Conversation: User & Orchestrator - Retrieve and understand requirements from user
        if not self.fast_forward:
            conversation_with_user = HumanConversationWrapper(self.orchestrator)

            for ai_message in conversation_with_user:
                sender, message = ai_message
                if not conversation_with_user.is_accepted():
                    user_response = self.__transmit_message_signal(
                        sender=sender, message=message, is_question=True
                    )
                    conversation_with_user.set_user_response(user_response)
                else:
                    self.__transmit_message_signal(sender=sender, message=message)

            self.title = self.__create_project_name()  # TODO: Use real project title
        else:
            # Randomly select a predefined use case and add it to the memory of the orchestrator if fast forward is enabled
            with open(self.root / "src/setup/summaries.json") as file:
                summaries = json.load(file)

            summary_key = random.choice(list(summaries.keys()))
            self.__add_metrics("project_name", summary_key)
            self.title = self.__create_project_name(summary_key)

            self.orchestrator.inject_message(summaries[summary_key], kind="ai")
            self.__transmit_message_signal(sender="You", message=summaries[summary_key])

        # 0b. Orchestrator devises tasks for database, backend & frontend devs based on user requirements
        prompt_task_derivation = self.orchestrator.get_prompt_text("task derivation")
        requirements = self.orchestrator.answer(prompt_task_derivation)
        requirements = parse_message(
            requirements,
            parser={
                "type": "json",
                "use_parser": True,
                "fields": "[('database', str), ('backend', str), ('frontend', str)]",
            },
        )

        docs = {}
        database_code, docs["database"] = self.develop("database", requirements, docs)
        backend_code, docs["backend"] = self.develop("backend", requirements, docs)
        frontend_code, docs["frontend"] = self.develop("frontend", requirements, docs)
        docs_as_string = "".join(
            [
                f"Here is the documentation for the {layer}: {doc}\n"
                for layer, doc in docs.items()
            ]
        )

        self.__transmit_animation_signal(f"{self.orchestrator.name} is typing")
        prompt_present_product = self.orchestrator.get_prompt_text("present product")
        prompt_present_product = prompt_present_product.format(docs=docs_as_string)
        final_message = self.orchestrator.answer(prompt_present_product)
        self.__transmit_message_signal(
            sender=self.orchestrator.name, message=final_message
        )

        # End of development process
        self.__add_metrics("time", int(time.time() - start_time))

    def develop(self, layer, requirements, docs):
        # Get agents for layer
        developer, tester, documenter = (
            getattr(self, layer + "_dev"),
            getattr(self, layer + "_test"),
            getattr(self, layer + "_doc"),
        )
        # Start corresponding docker container
        self.__transmit_animation_signal(f"Building docker container for {layer}")
        docker_sandbox = (
            DatabaseSandbox(self.title)
            if layer == "database"
            else PythonSandbox(self.title)
            if layer == "backend"
            else FrontendSandbox(self.title)
        )

        # 1a. Delegation: Orchestrator & Dev - Layer Dev receives tasks from Orchestrator
        # Only for UX purposes. No actual message is sent
        message = f"<span style='color: blue;'>@{developer.name}</span>, please develop the {layer} for the application. Here are the requirements: {requirements[layer]}"
        self.__transmit_message_signal(sender=self.orchestrator.name, message=message)

        # 1b. Conversation: Dev & Tester
        developer_kickoff = developer.get_prompt_text("kickoff")
        developer_followup = developer.get_prompt_text("followup")
        tester_first_check = tester.get_prompt_text("first check")
        tester_further_checks = tester.get_prompt_text("further checks")

        # Repeat the conversation until the tester accepts the code
        for turn in range(5):
            if turn == 0:
                prev_docs = "".join(
                    [
                        f"Here is the documentation for the {layer}: {doc}\n"
                        for layer, doc in docs.items()
                    ]
                )
                dev_query = developer_kickoff.format(
                    language=developer.languages,
                    requirements=requirements,
                    prev_docs=prev_docs,
                )
            else:
                dev_query = developer_followup.format(
                    feedback=tester_feedback, language=developer.languages
                )

            # Send query to dev agent
            self.__transmit_animation_signal(f"{developer.name} is typing")
            dev_code = developer.answer(dev_query, verbose=True)
            dev_code = parse_message(dev_code, developer.parser)
            self.__transmit_message_signal(sender=developer.name, message=dev_code)

            # Execute code in docker container
            docker_logs = ""
            if layer != "database":
                self.__transmit_animation_signal(f"Running code in {layer} container")
                dependencies = (
                    ["FastAPI", "uvicorn", "asyncpg", "pydantic", "pandas", "numpy"]
                    if layer == "backend"
                    else None
                )
                 # If the backend tester didnt accept the last backend code, reset the database container,
                # so that the amended backend code can be tested in a clean environment
                if turn != 0 and layer == "backend":
                    DatabaseSandbox(self.title)

                timestamp_execution = int(
                    time.mktime(datetime.datetime.now().timetuple())
                )

                docker_container = docker_sandbox.trigger_execution_pipeline(dev_code, dependencies)

                docker_logs = docker_container.logs(
                    since=timestamp_execution, tail=10
                ).decode("utf-8")

                if len(docker_logs) != 0:
                    docker_logs = "Docker container logs:\n" + docker_logs

                print("\n== DOCKER LOGS ==\n", docker_logs)
                
            # Send code and docker logs to tester agent
            # if layer is frontend, the tester need the documentation of the backend to check if the dev created one element for each api endpoint
            backend_docs = (
                f"This is the documentation for the backend: {docs['backend']}"
                if layer == "frontend"
                else ""
            )

            # Tester checks code
            tester_responses = []
            self.__transmit_animation_signal(f"{tester.name} is typing")

            # Make initial check
            prompt_first_check = tester_first_check.format(
                code=dev_code, 
                docker_logs=docker_logs, 
                backend_docs=backend_docs
            )
            tester_responses.append(tester.answer(prompt_first_check, verbose=True))

            # Make further checks. One API call for each set of 3 bugfixes.
            num_bugfixes = len(tester.bugfixes)
            for i in range(0, num_bugfixes, 3):
                bugfixes_subset_list = tester.bugfixes[i:min(i + 3, num_bugfixes)]
                bugfixes_subset_string = " ".join(bugfixes_subset_list)
                prompt_bugfix = tester_further_checks.format(
                    code=dev_code,
                    bugfixes=bugfixes_subset_string,
                )

                tester_responses.append(tester.answer(prompt_bugfix, verbose=True))
                
            tester_response_parsed = [parse_message(response, tester.parser) for response in tester_responses]

            if sum([response["accepted"] for response in tester_response_parsed]) == len(tester_response_parsed):
                tester_feedback = "The code ran without any errors and fulfills all requirements"
                self.__transmit_message_signal(sender=tester.name, message=tester_feedback)
                break

            else:
                tester_feedback = ""
                for response in tester_response_parsed:
                    if not response["accepted"]:
                        tester_feedback += response["text"] + "\n\n"
                self.__transmit_message_signal(sender=tester.name, message=tester_feedback)

            # Overwrite the turn metric with the new value
            self.__add_metrics(f"turns_{layer}", turn + 1)


        # 1c. Documenter creates documentation
        self.__transmit_animation_signal(f"{documenter.name} is typing")
        documentation_task = documenter.get_prompt_text("document")
        documentation_task = PromptTemplate.from_template(documentation_task)
        documentation_task = documentation_task.format(
            requirements=requirements[layer], kind=layer, code=dev_code
        )
        documentation = documenter.answer(documentation_task)
        self.__transmit_message_signal(sender=documenter.name, message=documentation)

        # Add documentation to orchestrators memory / chat history
        self.orchestrator.inject_message(str(documentation), kind="human")

        return (dev_code, documentation)