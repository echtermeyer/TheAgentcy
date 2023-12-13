import json

from pathlib import Path

from src.utils import *
from src.agents import Agent, HumanConversationWrapper, ConversationWrapper


class Pipeline:
    def __init__(self, description: str = None) -> None:
        self.description = description
        self.root = Path(__file__).parent.parent

        self.__setup_agents()

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
                    prompt=self.root / f"src/characters/{agent['varname']}.txt",
                ),
            )

    def start(self) -> None:
        """Start developing process"""

        # Retrieve and understand requirements from user
        conv1 = HumanConversationWrapper(self.orchestrator)
        conv1.start()

        # Create tasks for database, backend & frontend
        with open(self.root / "src/prompts/po_tasks.txt", "r") as f:
            prompt = f.read()

        tasks = self.orchestrator.answer(prompt)
        tasks = extract_json_from_str(tasks)

        # Start database development
        conv2 = ConversationWrapper(self.database_dev, self.database_test)
        code_database = conv2.start(tasks["database"])  # do something with the code

        # Documentation for database
        conv3 = ConversationWrapper(self.database_doc, self.database_test)
        starter = f"""
        Write down questions you need to know in order to create an excellent and detailed documentation for the
        database layer of the application. The project you are working on is about: {tasks['database']}.
        """
        documentation_database = conv3.start(starter)
        self.orchestrator.inject_message(documentation_database, kind="human")

        # Start backend development
        conv4 = ConversationWrapper(self.backend_dev, self.backend_test)
        code_database = conv4.start(tasks["backend"])  # do something with the code

        # Documentation for backend
        conv5 = ConversationWrapper(self.backend_doc, self.backend_test)
        starter = f"""
        Write down questions you need to know in order to create an excellent and detailed documentation for the 
        backend layer of the application. The project you are working on is about: {tasks['backend']}.
        """
        documentation_backend = conv5.start(starter)
        self.orchestrator.inject_message(documentation_backend, kind="human")

        # Start backend development
        conv6 = ConversationWrapper(self.frontend_dev, self.frontend_test)
        code_database = conv6.start(tasks["database"])  # do something with the code

        # Documentation for backend
        conv7 = ConversationWrapper(self.frontend_doc, self.frontend_test)
        starter = f"""
        Write down questions you need to know in order to create an excellent and detailed documentation for the
        database layer of the application. The project you are working on is about: {tasks['database']}.
        """
        documentation_frontend = conv7.start(starter)
        self.orchestrator.inject_message(documentation_frontend, kind="human")
