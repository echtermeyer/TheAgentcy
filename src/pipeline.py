import json

from pathlib import Path

from src.agents import Agent, ConversationWrapper


class Pipeline:
    def __init__(self, description: str) -> None:
        self.description = description
        print(self.description)
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
                    prompt=self.root / f"src/prompts/{agent['varname']}.txt",
                ),
            )

    def start(self) -> None:
        """Start developing process"""
        self._work(self.orchestrator, self.database_dev, kind="instruct")
        self._work(self.database_dev, self.database_test, kind="develop")
        self._work(self.database_test, self.database_doc, kind="explain")
        self._work(self.database_doc, self.orchestrator, kind="present")

    def _work(self, agent1: Agent, agent2: Agent, kind: str) -> str:
        print(f"{agent1.name} is working with {agent2.name}")

        conversation = ConversationWrapper(agent1, agent2, max_turns=2)

        if kind == "instruct":
            pass
        elif kind == "develop":
            conversation.start(self.description)
        elif kind == "explain":
            pass
        elif kind == "present":
            pass
        else:
            raise ValueError("Conversation is not supported")
