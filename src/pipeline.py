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
                    parser=agent["parser"],
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
        # print("PLAIN TASKS: "+ tasks)
        tasks = extract_json(tasks, [("database",str),("backend", str),("frontend",str)])
        

        # Start database development
        conv2 = ConversationWrapper(self.database_dev, self.database_test)
        code_database_str = conv2.start("These are the requirements: "+tasks["database"]+' '+output_format('sql', True))  
        
        # code_database = extract_code(code_database_str, 'sql') # do something with the code. code is now extraced in agents.py. however not complely plain there becaus langague is in string

        # Documentation for database
        conv3 = ConversationWrapper(self.database_doc, self.database_test)
        starter = f"""
        Write down questions you need to know in order to create an detailed documentation for the
        database layer of the application. The project you are working on is about: {tasks['database']}.
        """
        documentation_database = conv3.start(starter)
        self.orchestrator.inject_message(str(documentation_database), kind="human")

        # Start backend development
        conv4 = ConversationWrapper(self.backend_dev, self.backend_test)
        code_backend_str = conv4.start("These are the requirements: "+tasks["backend"]+' '+output_format('python', True))  
        # code_backend = extract_code(code_backend_str, 'python') # do something with the code

        # Documentation for backend
        conv5 = ConversationWrapper(self.backend_doc, self.backend_test)
        starter = f"""
        Beginn by aksing some questions you need to know in order to create an excellent and detailed documentation for the 
        backend layer of the application. The project you are working on is about: {tasks['backend']}.
        """
        documentation_backend = conv5.start(starter)
        self.orchestrator.inject_message(str(documentation_backend), kind="human") 
        # Start backend development
        conv6 = ConversationWrapper(self.frontend_dev, self.frontend_test)
        code_frontend_str = conv6.start("These are the requirements: "+tasks["database"]+output_format('html',True)+"Do this aswell for the 'css' and 'javascript' code.")  # do something with the code
        # code_frontend_html = extract_code(code_frontend_str, 'html')
        # code_frontend_css = extract_code(code_frontend_str, 'css')
        # code_frontend_js = extract_code(code_frontend_str, 'javascript') 
        # code extraction now in agents.py. however there code is written into one long string for conversation with comment about language

        # Documentation for backend
        conv7 = ConversationWrapper(self.frontend_doc, self.frontend_test)
        starter = f"""
        Beginn by aksing some questions you need to know in order to create an excellent and detailed documentation for the
        frontend layer of the application. The project you are working on is about: {tasks['frontend']}.
        """

        documentation_frontend = conv7.start(starter)
        self.orchestrator.inject_message(str(documentation_frontend), kind="human")
