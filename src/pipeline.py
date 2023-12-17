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
        code_database_str = conv2.start("These are the requirements: "+tasks["database"]+' '+output_format('sql', True))  
        code_database = extract_code(code_database_str, 'sql') # do something with the code

        # Documentation for database
        conv3 = ConversationWrapper(self.database_doc, self.database_test)
        starter = f"""
        Write down questions you need to know in order to create an detailed documentation for the
        database layer of the application. The project you are working on is about: {tasks['database']}.
        """
        documentation_database = conv3.start(starter)
        self.orchestrator.inject_message(documentation_database, kind="human") #QUESTION: what is this doing ??

        # Start backend development
        conv4 = ConversationWrapper(self.backend_dev, self.backend_test)
        code_backend_str = conv4.start("These are the requirements: "+tasks["backend"]+' '+output_format('python', True))  
        code_backend = extract_code(code_backend_str, 'python') # do something with the code

        #TODO: what about the error logs? they still need to be added to conversation at some point. 
        # In my opinon conversation starts too early. Backend Dev should first develop, then code is executed by us, then conversation with tester starts. 
        # Opposed to initial design the tester now has two "roles": testing and answering to the doc. Maybe define seperate role prompts?

        # Documentation for backend
        conv5 = ConversationWrapper(self.backend_doc, self.backend_test)
        starter = f"""
        Write down questions you need to know in order to create an excellent and detailed documentation for the 
        backend layer of the application. The project you are working on is about: {tasks['backend']}.
        """#TODO: maybe provide actual project description instead of task
        documentation_backend = conv5.start(starter)
        self.orchestrator.inject_message(documentation_backend, kind="human") #QUESTION: what is this doing ??
        #QUESTION: I am unsure when the code that is supposed to be documented enters this conversation? Is this missing?
        # Or is the idea that the tester alone can look at the code from prev. conversation and answers are generated this way?
        # Wouldn't we get much better answers if we just give the code to the doc aswell and do not do a conversation here?

        # Start backend development
        conv6 = ConversationWrapper(self.frontend_dev, self.frontend_test)
        code_frontend_str = conv6.start("These are the requirements: "+tasks["database"]+output_format('html',True)+"Do this aswell for the 'css' and 'javascript' code.")  # do something with the code
        code_frontend_html = extract_code(code_frontend_str, 'html')
        code_frontend_css = extract_code(code_frontend_str, 'css')
        code_frontend_js = extract_code(code_frontend_str, 'javascript')

        # Documentation for backend
        conv7 = ConversationWrapper(self.frontend_doc, self.frontend_test)
        starter = f"""
        Write down questions you need to know in order to create an excellent and detailed documentation for the
        frontend layer of the application. The project you are working on is about: {tasks['frontend']}.
        """ #TODO: maybe provide actual project description instead of task

        documentation_frontend = conv7.start(starter)
        self.orchestrator.inject_message(documentation_frontend, kind="human") #QUESTION: what is this doing ??
