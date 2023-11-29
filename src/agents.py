class Agent:
    def __init__(self, name: str) -> None:
        self.__name = name

    @property
    def name(self):
        return self.__name
