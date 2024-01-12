import json
import random

from pathlib import Path
from langchain.prompts import PromptTemplate

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
            # send signal to gui thread
            self.to_gui_signal.emit(sender, message, is_question)
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
                    user_response = self.__transmit_to_gui(
                        sender=sender, message=message, is_question=True
                    )
                    conversation_with_user.set_user_response(user_response)
                else:
                    self.__transmit_to_gui(sender=sender, message=message)
        else:
            # Randomly select a predefined use case and add it to the memory of the orchestrator if fast forward is enabled
            with open(self.root / "src/setup/summaries.json") as file:
                summaries = json.load(file)
                summary = random.choice(list(summaries.values()))

                self.orchestrator.inject_message(summary, kind="ai")
                self.__transmit_to_gui(sender="You", message=summary)

        # 0b. Orchestrator devises tasks for database, backend & frontend devs based on user requirements
        summarization_task = self.orchestrator.get_prompt_text("summarize")
        requirements = self.orchestrator.answer(summarization_task)
        requirements = extract_json(
            requirements, [("database", str), ("backend", str), ("frontend", str)]
        )

        self.develop("database", requirements)
        self.develop("backend", requirements)
        self.develop("frontend", requirements)

    def develop(self, layer, requirements):
        # Get agents for layer
        developer, tester, documenter = (
            getattr(self, layer + "_dev"),
            getattr(self, layer + "_test"),
            getattr(self, layer + "_doc"),
        )

        # 1a. Delegation: Orchestrator & Dev - Layer Dev receives tasks from Orchestrator
        # Only for UX purposes. No actual message is sent
        message = f"<span style='color: blue;'>@{developer.name}</span>, please develop the {layer} for the application. Here are the requirements: {requirements['database']}"
        self.__transmit_to_gui(sender=self.orchestrator.name, message=message)

        # 1b. Conversation: Dev & Tester
        developer_kickoff = developer.get_prompt_text("kickoff")
        developer_followup = developer.get_prompt_text("followup")
        tester_followup = tester.get_prompt_text("followup")

        # TODO: Output format to be adjusted for Frontend dev (multiple formats)
        
        conversation_dev_tester = ConversationWrapper(
            agent1=developer,
            agent2=tester,
            requirements=requirements[layer],
            kickoff=developer_kickoff,
            agent1_template=developer_followup,
            agent2_template=tester_followup,
        )
        for ai_message in conversation_dev_tester:
            sender, message = ai_message
            self.__transmit_to_gui(sender=sender, message=message)

        accepted_code = conversation_dev_tester.last_message_agent1  # TODO: Use code in containers, use traceback

        # 1c. Conversation: Documenter creates documentation
        documentation_task = documenter.get_prompt_text("document")
        documentation_task = PromptTemplate.from_template(documentation_task)
        documentation_task = documentation_task.format(
            requirements=requirements[layer], kind=layer, code=accepted_code
        )
        documentation = documenter.answer(documentation_task)

        self.__transmit_to_gui(sender=documenter.name, message=documentation)

        # Add documentation to orchestrators memory / chat history
        self.orchestrator.inject_message(str(documentation), kind="human")