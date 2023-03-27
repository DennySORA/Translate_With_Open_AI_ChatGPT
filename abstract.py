from abc import ABC, abstractmethod


class TranslateEngineBase(ABC):
    @abstractmethod
    def __init__(self, key: str, *args, **kwargs):
        pass

    @abstractmethod
    def translate(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def count_token(self, content: str) -> int:
        pass

    @abstractmethod
    def create_messages(self, *args, **kwargs) -> list[dict[str, str]]:
        pass


class FileEngineBase(ABC):
    @abstractmethod
    def __init__(self, engine: TranslateEngineBase, *args, **kwargs):
        pass

    @abstractmethod
    def translate(self):
        pass
