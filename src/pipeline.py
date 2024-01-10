from src.agents import Agent, HumanConversationWrapper, ConversationWrapper
from PySide6.QtCore import QObject, Signal, QThread, QCoreApplication
from pathlib import Path
from src.utils import *
import random
import json


class Pipeline(QObject):
    to_gui_signal = Signal(str, str, bool)  # For communication with GUI thread

    def __init__(self, command_line_args):
        super().__init__()
        self._input = None
        self._pause_execution = False
        
        self.root = Path(__file__).parent.parent
        self.description = command_line_args.description
        self.fast_forward = command_line_args.fast_forward
        self.__setup_agents()
 
    def __transmit_to_gui(self, sender, message, is_question=False):
        self.to_gui_signal.emit(sender, message, is_question) # send signal to gui thread
        self._pause_execution = True
        while self._pause_execution: # sleep until gui thread has responded
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
                    prompt=self.root / f"src/characters/{agent['varname']}.txt",
                ),
            )

    def start(self) -> None:
        """Start developing process"""

        # 0a. Conversation: User & Orchestrator - Retrieve and understand requirements from user
        if self.fast_forward == "no":
            conv1 = HumanConversationWrapper(self.orchestrator)
            for ai_message in conv1:
                sender, message = ai_message
                if not conv1.accepted:
                    user_response = self.__transmit_to_gui(sender=sender, message=message, is_question=True)
                    conv1.answer = user_response
                else:
                    self.__transmit_to_gui(sender=sender, message=message)

        # 0b. Orchestrator devises tasks for database, backend & frontend devs based on user requirements
        with open(self.root / "src/prompts/po_tasks.txt", "r") as f:
            prompt = f.read()

        if self.fast_forward == "yes":  # if user interacton is skipped, use a random predefined use case
            with open(self.root / "src/example_websites/summaries.json") as f:
                summaries = json.load(f)
                summary = random.choice(list(summaries.values()))
                self.__transmit_to_gui(sender="You", message=summary)
                prompt = f"Forget everything I've said before and focus on the following. {summary} TASK: {prompt}"
        
        tasks = self.orchestrator.answer(prompt)
        print(tasks)
        tasks = extract_json(
            tasks, [("database", str), ("backend", str), ("frontend", str)]
        )
        print("tasks: ", tasks)

        self.develop("database", tasks)
        self.develop("backend", tasks)
        self.develop("frontend", tasks)

    def develop(self, layer, tasks):
        developer, tester, documenter = getattr(self, layer + "_dev"), getattr(self, layer + "_test"), getattr(self, layer + "_doc") # get agents for layer

        # 1a. Delegation: Orchestrator & Dev - Layer Dev receives tasks from Orchestrator
        message = f"<span style='color: blue;'>@{developer.name}</span>, please develop the {layer} for the application. Here are the requirements: {tasks['database']}"
        self.__transmit_to_gui(sender=self.orchestrator.name, message=message)

        # 1b. Conversation: Dev & Tester
        format = developer.parser["fields"][0]  # TODO: Needs to be adjusted for Frontend dev (multiple formats)
        start_query = f"These are the requirements: {tasks[layer]} {output_format(format, True)}"
        conv2 = ConversationWrapper(developer, tester, start_query, approver=tester)
        for ai_message in conv2:
            sender, message = ai_message
            self.__transmit_to_gui(sender=sender, message=message)

        final_code = conv2.last_message_agent1 # TODO: Use code

        # 1c. Conversation: Documenter & Tester
        start_query = f"""
        The project you are working on is about: {tasks[layer]}. Here is the final code created by the developer: '{final_code}'. Please ask as many clarifying question as you need in order to create an excellent and detailed documentation for the
        {layer} of the application. 
        """
        print("start_query: ", start_query)
        conv3 = ConversationWrapper(documenter, tester, start_query, approver=documenter)
        for ai_message in conv3:
            sender, message = ai_message
            self.__transmit_to_gui(sender=sender, message=message)

        final_documentation = conv2.last_message_agent1        
        self.orchestrator.inject_message(str(final_documentation), kind="human") # add documentation to orchestrators memory / chat history



        # TODO: Improve Conversation between Doc & Tester. Tester is bad at answering questions (change prompting).
        # TODO: DynamicModel.validate_json often fails when validating documentation 
        # TODO: GUI code formatting
