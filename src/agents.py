import os
import openai

from pathlib import Path
from dotenv import load_dotenv

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage

from langchain.prompts import (
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
        self, name: str, model: str, temperature: float, parser: dict, prompt: Path
    ) -> None:
        self.__name: str = name

        self.character: str = self.__load_agent_prompt(prompt)
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
    # Implementation of the conversation between two agents. agent1 must be the agent that returns the final results
    # TODO: Make agent 1 the agent that returns the final results
    def __init__(self, agent1: Agent, agent2: Agent, start_query: str, max_turns: int = 5) -> None:
        self.agent1: Agent = agent1
        self.agent2: Agent = agent2
        self.max_turns: int = max_turns

        self.current_turn: int = 0
        self.current_agent = agent1
        self.current_query = start_query

        self.answer = None
        self.accepted = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.accepted == False and self.current_turn < self.max_turns:

            response = self.current_agent.answer(self.current_query, verbose=True)
            response = parse_response(response, self.current_agent.parser)

            self.accepted = response["accepted"] if type(response) == dict and self.current_agent == self.agent2 else self.accepted
            self.current_query = response["text"] if type(response) == dict else response

            return_values = (self.current_agent.name, self.current_query) # save now before updating self.current_agent

            self.current_turn = self.current_turn + 1 if self.current_agent == self.agent2 else self.current_turn
            self.current_agent = self.agent2 if self.current_agent == self.agent1 else self.agent1

            return return_values

        else:
            raise StopIteration



class HumanConversationWrapper:
    def __init__(self, agent1: Agent, max_turns: int = 10) -> None:
        self.agent1: Agent = agent1
        self.max_turns: int = max_turns
        self.current_turn: int = 0

        self.answer = None
        self.accepted = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.accepted == False and self.current_turn == 0:
            self.current_turn += 1
            return (self.agent1.name, f"Hello, my name is {self.agent1.name}. Me and my team are here to build custom web-applications based on your specific requirements. What project can we assist you with today?")

        elif self.accepted == False and self.current_turn < self.max_turns:
            ai_response_txt = self.agent1.answer(self.answer, verbose=True)
            ai_response = parse_response(ai_response_txt, self.agent1.parser)
            self.accepted, message = ai_response["accepted"], ai_response["text"]
            self.current_turn += 1

            if self.accepted == True:
                message = "Thank you for specifying your requirements. We will start working on your project now! Here's a quick summary of your requirements: <br><br>" + message

            return (self.agent1.name, message)

        else:
            raise StopIteration