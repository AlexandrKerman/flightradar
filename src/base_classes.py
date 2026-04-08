from abc import ABC, abstractmethod


class BaseAPI(ABC):
    @abstractmethod
    async def set_box(self, country: str) -> None:
        pass

    @abstractmethod
    async def get_aeroplanes(self) -> list[dict]:
        pass


class BaseFile(ABC):
    @abstractmethod
    def update_data(self, data: list[dict]) -> None:
        pass

    @abstractmethod
    def add_aeroplane(self, aeroplane) -> None:
        pass

    @abstractmethod
    def delete_aeroplane(self, board_name) -> None:
        pass

    @abstractmethod
    def read_aeroplane(self) -> None:
        pass


class BaseAeroplane(ABC):
    @classmethod
    @abstractmethod
    def cast_to_aeroplane(cls, aeroplanes) -> list:
        pass
