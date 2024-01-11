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
        self, name: str, model: str, temperature: float, parser: dict, character: Path
    ) -> None:
        self.__name: str = name

        self.character: str = self.__load_agent_prompt(character)
        self.chain: LLMChain = self.__setup_chain(model, temperature)
        self.parser: dict = parser

    @property
    def name(self):
        return self.__name

    def __load_agent_prompt(self, prompt: Path) -> str:
        with open(prompt, "r") as f:
            agent_prompt = f.read()

        return agent_prompt

    def __setup_chain(self, model: str, temperature: float) -> LLMChain:
        llm = ChatOpenAI(
            model_name=model,
            temperature=temperature,
        )

        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(self.character),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{message}"),
            ]
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        return LLMChain(llm=llm, prompt=prompt, verbose=False, memory=memory)

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

        self.chain.memory.chat_memory.add_message(message)

    def answer(self, message: str, verbose=False):
        answer = self.chain.run({"message": message})

        if verbose:
            print(f"\033[34m{self.name}:\033[0m {answer}")

        return answer


class ConversationWrapper:
    def __init__(
        self,
        agent1: Agent,
        agent2: Agent,
        start_query: str,
        approver: Agent,
        max_turns: int = 5,
    ) -> None:
        self.agent1: Agent = agent1
        self.agent2: Agent = agent2
        self.approver: Agent = approver

        self.last_message_agent1: str = None
        self.last_message_agent2: str = start_query

        self.max_turns: int = max_turns
        self.accepted = False
        self.current_turn: int = 0
        self.current_agent = agent1

    def __iter__(self):
        return self

    def __next__(self):
        if self.accepted == False and self.current_turn < self.max_turns:
            current_query = (
                self.last_message_agent2
                if self.current_agent == self.agent1
                else self.last_message_agent1
            )
            response = self.current_agent.answer(current_query, verbose=True)
            response = parse_response(response, self.current_agent.parser)

            # Can be dict [tester or documenter] or code [dev]
            message = response["text"] if type(response) == dict else response

            self.accepted = (
                response["accepted"]
                if type(response) == dict and self.current_agent == self.approver
                else self.accepted
            )
            self.last_message_agent1 = (
                message
                if self.current_agent == self.agent1
                else self.last_message_agent1
            )
            self.last_message_agent2 = (
                message
                if self.current_agent == self.agent2
                else self.last_message_agent2
            )

            # save now before updating self.current_agent
            return_values = (
                self.current_agent.name,
                message,
            )

            self.current_turn = (
                self.current_turn + 1
                if self.current_agent == self.agent2
                else self.current_turn
            )
            self.current_agent = (
                self.agent2 if self.current_agent == self.agent1 else self.agent1
            )

            return return_values

        else:
            raise StopIteration


class HumanConversationWrapper:
    def __init__(
        self,
        agent1: Agent,
        task_system: str,
        task_conversation: str,
        max_turns: int = 10,
    ) -> None:
        self.agent1: Agent = agent1
        self.max_turns: int = max_turns
        self.current_turn: int = 0

        self.__user_response = None
        self.__accepted = False

        # Inject task system message and create prompt template for human conversation
        self.agent1.inject_message(task_system, kind="system")
        self.prompt_template = PromptTemplate.from_template(task_conversation)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__accepted == False and self.current_turn == 0:
            self.current_turn += 1
            return (
                self.agent1.name,
                f"Hello, my name is {self.agent1.name}. Me and my team are here to build custom web-applications based on your specific requirements. What project can we assist you with today?",
            )

        elif self.__accepted == False and self.current_turn < self.max_turns:
            # Insert user response into prompt template
            prompt = self.prompt_template.format(user_response=self.__user_response)

            ai_response_txt = self.agent1.answer(prompt, verbose=True)
            ai_response = parse_response(ai_response_txt, self.agent1.parser)
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
