import json
import random

from pathlib import Path
from langchain.prompts import PromptTemplate

from PySide6.QtCore import QObject, Signal, QThread, QCoreApplication

from src.utils import *
from src.agents import Agent, HumanConversationWrapper
from src.instantiate import PythonSandbox, FrontendSandbox, DatabaseSandbox


class Pipeline(QObject):
    message_signal = Signal(str, str, bool)  # For communication with GUI thread
    animation_signal = Signal(str) # layer, status, on/off

    def __init__(self, command_line_args):
        super().__init__()
        self._input = None
        self._pause_execution = False

        self.root = Path(__file__).parent.parent
        self.description = command_line_args.description
        self.fast_forward = command_line_args.fast_forward
        self.disable_gui = command_line_args.disable_gui
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

    def start(self) -> None:
        """Start developing process"""

        # 0a. Conversation: User & Orchestrator - Retrieve and understand requirements from user
        if not self.fast_forward:
            # Inject task system message and create prompt template for human conversation
            system_message = self.orchestrator.get_prompt_text("systemize")
            conversation_task = self.orchestrator.get_prompt_text("conversize")

            conversation_with_user = HumanConversationWrapper(
                self.orchestrator,
                system_message=system_message,
                conversation_task=conversation_task,
            )

            for ai_message in conversation_with_user:
                sender, message = ai_message
                if not conversation_with_user.is_accepted():
                    user_response = self.__transmit_message_signal(
                        sender=sender, message=message, is_question=True
                    )
                    conversation_with_user.set_user_response(user_response)
                else:
                    self.__transmit_message_signal(sender=sender, message=message)
        else:
            # Randomly select a predefined use case and add it to the memory of the orchestrator if fast forward is enabled
            with open(self.root / "src/setup/summaries.json") as file:
                summaries = json.load(file)
                summary = random.choice(list(summaries.values()))

                self.orchestrator.inject_message(summary, kind="ai")
                self.__transmit_message_signal(sender="You", message=summary)

        # 0b. Orchestrator devises tasks for database, backend & frontend devs based on user requirements
        summarization_task = self.orchestrator.get_prompt_text("summarize")
        requirements = self.orchestrator.answer(summarization_task)
        requirements = extract_json(
            requirements, [("database", str), ("backend", str), ("frontend", str)]
        )

        database_code, database_documentation = self.develop("database", requirements)
        backend_code, backend_documentation = self.develop("backend", requirements)
        frontend_code, frontend_documentation = self.develop("frontend", requirements)

        self.__transmit_animation_signal(f"{self.orchestrator.name} is typing")
        finale_prompt = self.orchestrator.get_prompt_text("finalize")
        final_message = self.orchestrator.answer(finale_prompt)
        user_response = self.__transmit_message_signal(sender=self.orchestrator.name, message=final_message)

    def develop(self, layer, requirements):
        # Get agents for layer
        developer, tester, documenter = (
            getattr(self, layer + "_dev"),
            getattr(self, layer + "_test"),
            getattr(self, layer + "_doc"),
        )
        # Start corresponding docker container
        self.__transmit_animation_signal(f"Building docker container for {layer}")
        docker_sandbox = DatabaseSandbox() if layer == "database" else PythonSandbox() if layer == "backend" else FrontendSandbox()

        # 1a. Delegation: Orchestrator & Dev - Layer Dev receives tasks from Orchestrator
        # Only for UX purposes. No actual message is sent
        message = f"<span style='color: blue;'>@{developer.name}</span>, please develop the {layer} for the application. Here are the requirements: {requirements[layer]}"
        self.__transmit_message_signal(sender=self.orchestrator.name, message=message)

        # 1b. Conversation: Dev & Tester
        developer_kickoff = developer.get_prompt_text("kickoff")
        developer_followup = developer.get_prompt_text("followup")
        tester_followup = tester.get_prompt_text("followup")

        for turn in range(5):
            if turn == 0:
                dev_query = developer_kickoff.format(language=developer.languages, requirements=requirements)
            else:
                dev_query = developer_followup.format(feedback=tester_message, language=developer.languages)

            # Send query to dev agent
            self.__transmit_animation_signal(f"{developer.name} is typing")
            dev_code = developer.answer(dev_query, verbose=True)
            dev_code = parse_response(dev_code, developer.parser)
            self.__transmit_message_signal(sender=developer.name, message=dev_code)
            
            # Execute code in docker container
            docker_logs = ""
            if layer != "database": 
                self.__transmit_animation_signal(f"running code in {layer} container")
                dependencies= ["FastAPI", "uvicorn", "asyncpg", "pydantic", "pandas", "numpy"] if layer == "backend" else None
                docker_container = docker_sandbox.trigger_execution_pipeline(dev_code, dependencies)
                prefix = "These are the last few log statements that one gets when running the code in a dedicated docker container:\n"
                if repr(docker_logs) != "''":
                    docker_logs = prefix + docker_container.logs(tail=10).decode("utf-8")

            # Send message, code and docker logs to tester agent
            tester_query = tester_followup.format(code=dev_code, docker_logs=docker_logs)
            self.__transmit_animation_signal(f"{tester.name} is typing")
            tester_message = tester.answer(tester_query, verbose=True)
            accepted, tester_message = parse_response(tester_message, tester.parser).values()
            self.__transmit_message_signal(sender=tester.name, message=tester_message)

            if accepted:
                break

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