import os
import openai

from pathlib import Path
from dotenv import load_dotenv

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

load_dotenv()
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")


class Agent:
    def __init__(self, name: str, model: str, temperature: float, prompt: Path) -> None:
        self.__name: str = name

        self.character: str = self.__load_agent_prompt(prompt)
        self.chain: LLMChain = self.__setup_chain(model, temperature)

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

        return LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)

    def answer(self, message: str):
        return self.chain.run({"message": message})


class ConversationWrapper:
    def __init__(self, agent1: Agent, agent2: Agent, max_turns: int = 3) -> None:
        self.agent1: Agent = agent1
        self.agent2: Agent = agent2
        self.max_turns: int = max_turns

    def start(self, user_query: str):
        current_response = user_query
        for _ in range(self.max_turns):
            current_response = self.agent1.answer(current_response)
            current_response = self.agent2.answer(current_response)
