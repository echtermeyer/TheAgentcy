import json
import random

from pathlib import Path

from PySide6.QtCore import QObject, Signal, QThread, QCoreApplication

from src.utils import *
from src.agents import Agent, HumanConversationWrapper, ConversationWrapper


class Pipeline(QObject):
    to_gui_signal = Signal(str, str, bool)  # For communication with GUI thread

    def __init__(self, command_line_args):
        super().__init__()
        self._input = None
        self._pause_execution = False

        self.root = Path(__file__).parent.parent
        self.description = command_line_args.description
        self.fast_forward = command_line_args.fast_forward
        self.disable_gui = command_line_args.disable_gui
        self.__setup_agents()

    def __transmit_to_gui(self, sender, message, is_question=False):
        if self.disable_gui:
            print(f"\033[34m{sender}:\033[0m {message}")
            if is_question:
                terminal_input = input("\033[34mYour answer: \033[0m ")
                return terminal_input

        else:
            self.to_gui_signal.emit(
                sender, message, is_question
            )  # send signal to gui thread
            self._pause_execution = True
            while self._pause_execution:  # sleep until gui thread has responded
                QThread.msleep(100)
                QCoreApplication.processEvents()  # but check for incoming signals

            return self._input

    def receive_from_gui(self, input):
        self._input = input
        self._pause_execution = False

    def __setup_agents(self) -> None:
        """Create workforce using agents.json"""
        with open(self.root / "src/setup/agents.json", "r") as file:
            config = json.load(file)

        for agent in config:
            setattr(
                self,
                agent["varname"],
                Agent(
                    name=agent["name"],
                    model=agent["model"],
                    temperature=agent["temperature"],
                    parser=agent["parser"],
                    character=self.root / f"src/characters/{agent['varname']}.txt",
                ),
            )

    def start(self) -> None:
        """Start developing process"""

        # 0a. Conversation: User & Orchestrator - Retrieve and understand requirements from user
        if not self.fast_forward:
            with open(self.root / "src/prompts/task_requirements_system.txt", "r") as f:
                task_requirements_system = f.read()

            with open(self.root / "src/prompts/task_requirements_conv.txt", "r") as f:
                task_requirements_conv = f.read()

            conversation_with_user = HumanConversationWrapper(
                self.orchestrator,
                task_requirements_system,
                task_requirements_conv,
            )

            for ai_message in conversation_with_user:
                sender, message = ai_message
                if not conversation_with_user.is_accepted():
                    user_response = self.__transmit_to_gui(
                        sender=sender, message=message, is_question=True
                    )
                    conversation_with_user.set_user_response(user_response)
                else:
                    self.__transmit_to_gui(sender=sender, message=message)

        # If user interacton is skipped, use a random predefined use case.
        # The predefined use case is added to the memory of the orchestrator.
        if self.fast_forward:
            with open(self.root / "src/setup/summaries.json") as f:
                summaries = json.load(f)
                summary = random.choice(list(summaries.values()))

                self.orchestrator.inject_message(summary, kind="ai")
                self.__transmit_to_gui(sender="You", message=summary) # TODO: @David, why not self.orchestrator instead of "You"?

        # 0b. Orchestrator devises tasks for database, backend & frontend devs based on user requirements
        with open(self.root / "src/prompts/task_requirements_summaries.txt", "r") as f:
            prompt = f.read()

        tasks = self.orchestrator.answer(prompt)
        tasks = extract_json(
            tasks, [("database", str), ("backend", str), ("frontend", str)]
        )

        self.develop("database", tasks)
        self.develop("backend", tasks)
        self.develop("frontend", tasks)

    def develop(self, layer, tasks):
        developer, tester, documenter = (
            getattr(self, layer + "_dev"),
            getattr(self, layer + "_test"),
            getattr(self, layer + "_doc"),
        )  # get agents for layer

        # 1a. Delegation: Orchestrator & Dev - Layer Dev receives tasks from Orchestrator
        message = f"<span style='color: blue;'>@{developer.name}</span>, please develop the {layer} for the application. Here are the requirements: {tasks['database']}"
        self.__transmit_to_gui(sender=self.orchestrator.name, message=message)

        # TODO: Needs to be adjusted for Frontend dev (multiple formats)
        # 1b. Conversation: Dev & Tester
        format = developer.parser["fields"][0]
        start_query = (
            f"These are the requirements: {tasks[layer]} {output_format(format, True)}"
        )
        conv2 = ConversationWrapper(developer, tester, start_query, approver=tester)
        for ai_message in conv2:
            sender, message = ai_message
            self.__transmit_to_gui(sender=sender, message=message)

        final_code = conv2.last_message_agent1  # TODO: Use code

        # 1c. Conversation: Documenter & Tester
        start_query = f"""
        The project you are working on is about: {tasks[layer]}. Here is the final code created by the developer: '{final_code}'. Please ask as many clarifying question as you need in order to create an excellent and detailed documentation for the
        {layer} of the application. 
        """
        conv3 = ConversationWrapper(
            documenter, tester, start_query, approver=documenter
        )
        for ai_message in conv3:
            sender, message = ai_message
            self.__transmit_to_gui(sender=sender, message=message)

        final_documentation = conv2.last_message_agent1
        self.orchestrator.inject_message(
            str(final_documentation), kind="human"
        )  # add documentation to orchestrators memory / chat history

        # TODO: Improve Conversation between Doc & Tester. Tester is bad at answering questions (change prompting).
        # TODO: DynamicModel.validate_json often fails when validating documentation
        # TODO: GUI code formatting
