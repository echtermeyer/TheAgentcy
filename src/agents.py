import os
import openai

from pathlib import Path
from dotenv import load_dotenv

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage

from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

from src.utils import *

load_dotenv()
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")


class Agent:
    def __init__(
        self,
        config: dict,
        root: Path,
    ) -> None:
        self.root: Path = root

        self.__name: str = config["name"]
        self.__varname: str = config["varname"]

        self.__character: str = self.__load_agent_character()
        self.__templates: dict = self.__load_prompt_templates(config["prompts"])
        self.__languages: str = self.__load_agent_language()

        self.__chain: LLMChain = self.__setup_chain(
            config["model"], config["temperature"]
        )
        self.__parser: dict = config["parser"]

    @property
    def name(self) -> str:
        return self.__name

    @property
    def varname(self) -> str:
        return self.__varname

    @property
    def languages(self) -> str:
        return self.__languages

    @property
    def parser(self):
        return self.__parser

    def __load_agent_language(self) -> str:
        if self.__varname == "orchestrator":
            return

        role = self.__varname.split("_")[0]
        if role == "database":
            return "sql"
        elif role == "backend":
            return "python"
        elif role == "frontend":
            return "html/css/javascript"

    def __load_agent_character(self) -> str:
        with open(self.root / f"src/characters/{self.__varname}.txt", "r") as f:
            agent_character = f.read()

        return agent_character

    def __load_prompt_templates(self, prompt_paths: dict) -> dict:
        return {
            key: open(self.root / prompt_path, "r").read()
            for key, prompt_path in prompt_paths.items()
        }

    def __setup_chain(self, model: str, temperature: float) -> LLMChain:
        llm = ChatOpenAI(
            model_name=model,
            temperature=temperature,
        )

        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(self.__character),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{message}"),
            ]
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        return LLMChain(llm=llm, prompt=prompt, verbose=False, memory=memory)

    def get_prompt_text(self, key: str) -> str:
        return self.__templates[key]

    def inject_message(self, text: str, kind: str = "human") -> None:
        if kind == "human":
            message = HumanMessage(content=text)
        elif kind == "ai":
            message = AIMessage(content=text)
        elif kind == "system":
            message = SystemMessage(content=text)
        else:
            raise ValueError(
                "This message type is not supported. Use one of ['human', 'ai', 'system']"
            )

        self.__chain.memory.chat_memory.add_message(message)

    # TODO: use invoke instead
    def answer(self, message: str, verbose=False):
        answer = self.__chain.run({"message": message})

        if verbose:
            print(f"\033[34m{self.name}:\033[0m {answer}")

        return answer


class HumanConversationWrapper:
    def __init__(
        self,
        agent1: Agent,
        system_message: str,
        conversation_task: str,
        max_turns: int = 10,
    ) -> None:
        self.agent1: Agent = agent1

        self.max_turns: int = max_turns
        self.current_turn: int = 0

        self.__user_response = None
        self.__accepted = False

        # Inject task system message and create prompt template for human conversation
        self.agent1.inject_message(system_message, kind="system")
        self.prompt_template = PromptTemplate.from_template(conversation_task)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__accepted == False and self.current_turn == 0:
            self.current_turn += 1
            return (
                self.agent1.name,
                f"Hello, my name is Santiago. Me and my team are here to build custom web-applications based on your specific requirements. What project can we assist you with today?",
            )

        elif self.__accepted == False and self.current_turn < self.max_turns:
            # Insert user response into prompt template
            prompt = self.prompt_template.format(user_response=self.__user_response)

            ai_response_txt = self.agent1.answer(prompt, verbose=True)
            ai_response = parse_message(ai_response_txt, self.agent1.parser)
            self.__accepted, message = ai_response["accepted"], ai_response["text"]
            self.current_turn += 1

            if self.__accepted == True:
                message = (
                    "Thank you for specifying your requirements. We will start working on your project now! Here's a quick summary of your requirements: <br><br>"
                    + message
                )

            return (self.agent1.name, message)

        else:
            raise StopIteration

    def set_user_response(self, user_response: str) -> None:
        self.__user_response = user_response

    def is_accepted(self) -> bool:
        return self.__accepted


# # Depreciated but kept for nostalgic reasons
# class ConversationWrapper:
#     def __init__(
#         self,
#         agent1: Agent,
#         agent2: Agent,
#         requirements: str,
#         agent1_template: str,
#         agent2_template: str,
#         kickoff: str,
#         docker_sandbox,
#         docker_dependencies,
#         max_turns: int = 5,
#     ) -> None:
#         self.agent1: Agent = agent1
#         self.agent2: Agent = agent2

#         self.requirements: str = requirements

#         self.agent1_template = PromptTemplate.from_template(agent1_template)
#         self.agent2_template = PromptTemplate.from_template(agent2_template)

#         kickoff = PromptTemplate.from_template(kickoff)
#         kickoff = kickoff.format(language=agent1.languages, requirements=requirements)

#         self.docker_sandbox = docker_sandbox
#         self.docker_dependencies = docker_dependencies

#         self.last_message_agent1: str = None
#         self.last_message_agent2: str = kickoff

#         self.max_turns: int = max_turns
#         self.accepted: bool = False

#         self.current_turn: int = 0
#         self.current_agent: Agent = agent1

#     def __iter__(self):
#         return self

#     def __next__(self):
#         if self.accepted == False and self.current_turn < self.max_turns:
#             if self.current_turn == 0 and self.current_agent == self.agent1:
#                 # handle first turn. use start_query which is the last_message_agent2
#                 current_query = self.last_message_agent2
#             else:
#                 # handle following turns
#                 if self.current_agent == self.agent1:
#                     current_query = self.agent1_template.format(
#                         feedback=self.last_message_agent2,
#                         language=self.agent1.languages,
#                     )
#                 else:
#                     # run code in docker
#                     if self.docker_sandbox is not None:
#                         docker_container = self.docker_sandbox.trigger_execution_pipeline(
#                             self.last_message_agent1,
#                             dependencies=self.docker_dependencies
#                             )

#                         docker_logs = """
#                         These are the last few log statements
#                         that one gets when running the code
#                         in a dedicated docker container:
#                         """ + docker_container.logs(tail=10).decode("utf-8")
#                         x = docker_container.logs(tail=10).decode("utf-8").replace("\n", "")
#                     else:
#                         docker_logs = ""

#                     current_query = self.agent2_template.format(
#                         code=self.last_message_agent1,
#                         docker_logs=docker_logs
#                     )

#             response = self.current_agent.answer(current_query, verbose=True)
#             response = parse_response(response, self.current_agent.parser)

#             # Can be dict [tester or documenter] or code [dev]
#             message = response["text"] if type(response) == dict else response

#             if type(response) == dict and self.current_agent == self.agent2:
#                 self.accepted = response["accepted"]

#             if self.current_agent == self.agent1:
#                 self.last_message_agent1 = message
#             else:
#                 self.last_message_agent2 = message

#             # save now before updating self.current_agent
#             return_values = (
#                 self.current_agent.name,
#                 message,
#             )

#             if self.current_agent == self.agent2:
#                 self.current_turn += 1

#             self.current_agent = (
#                 self.agent2 if self.current_agent == self.agent1 else self.agent1
#             )

#             return return_values

#         else:
#             raise StopIteration
