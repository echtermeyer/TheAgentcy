import os
import openai

from pathlib import Path
from dotenv import load_dotenv

from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
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
        self.config: dict = config

        self.__name: str = config["name"]
        self.__varname: str = config["varname"]

        self.__character: str = self.__load_agent_character()
        self.__templates: dict = self.__load_prompt_templates(config["prompts"])
        self.__languages: str = self.__load_agent_language()

        self._chain: LLMChain = self.__setup_chain(
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
        if self.config["model"] == "gpt-4-vision-preview":
            llm = ChatOpenAI(
                model_name=model,
                temperature=temperature,
                max_tokens=500, 
            )
        else:
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

        # memory = ConversationBufferMemory(
        #     memory_key="chat_history", return_messages=True
        # )
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", return_messages=True, k=2
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

        self._chain.memory.chat_memory.add_message(message)

    def answer(self, message: str, use_vision=False):
        # Take screenshot etc if we're using vision
        if use_vision:
            image_path = take_screenshot()
            image_base64 = encode_image(image_path)

            message = HumanMessage(
                content=[
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                            # "detail": "auto",
                        },
                    },
                ]
            )

        answer = self._chain.invoke({"message": message})["text"]

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

            ai_response_txt = self.agent1.answer(prompt)
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