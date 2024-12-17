from abc import ABC, abstractmethod

from model.data import FortuneTigerData


class FortuneTigerRepository(ABC):
    @abstractmethod
    def save_data(self, data: FortuneTigerData) -> str:
        """
        Save a document to the database.
        :param data: An instance of a Pydantic BaseModel containing the data to save.
        :return: The ID of the saved document.
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Check the connection to the database.
        :return: True if the database is reachable, False otherwise.
        """
        pass
