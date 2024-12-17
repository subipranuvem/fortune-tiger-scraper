from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from model.data import FortuneTigerData
from repository.fortune_tiger_interface import FortuneTigerRepository


class MongoConfig(BaseModel):
    connection_string: str
    database_name: str
    collection_name: str


# MongoDB Repository Implementation


class MongoRepository(FortuneTigerRepository):
    _config: MongoConfig

    def __init__(self, config: MongoConfig):
        self._config = config
        self.client: MongoClient = MongoClient(
            config.connection_string, serverSelectionTimeoutMS=5000
        )
        self.database = self.client[config.database_name]
        self.collection = self.database[config.collection_name]

    def save_data(self, data: FortuneTigerData) -> str:
        """
        Save a document to the MongoDB collection.
        """
        document = data.model_dump(mode="json")
        result = self.collection.insert_one(document)
        return str(result.inserted_id)  # Return the inserted document's ID

    def ping(self) -> bool:
        """
        Check if the MongoDB server is reachable.
        """
        try:
            self.client.admin.command("ping")  # Ping the MongoDB server
            return True
        except ServerSelectionTimeoutError:
            return False
