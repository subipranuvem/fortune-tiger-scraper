from abc import ABC, abstractmethod

from model.data import FortuneTigerData


class FortuneTigerSubscriber(ABC):
    @abstractmethod
    def process_data(self, data: FortuneTigerData):
        """
        Save a document to the database.
        :param data: An instance of a Pydantic BaseModel containing the data to save.
        :return: The ID of the saved document.
        """
        pass
