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

    def create_collection(self) -> bool:
        existing_collections = self.database.list_collection_names()
        if self._config.collection_name not in existing_collections:
            self.database.create_collection(self._config.collection_name)
            self.collection = self.database[self._config.collection_name]

            self.collection.create_index([("game_id", 1)])
            self.collection.create_index([("bet_profit", 1)])
            self.collection.create_index([("bet_amount", 1)])
            self.collection.create_index([("win_amount", 1)])
            self.collection.create_index([("current_balance", 1)])
            self.collection.create_index([("response.date", 1)])

            self.collection.create_index([("game_id", -1)])
            self.collection.create_index([("bet_profit", -1)])
            self.collection.create_index([("bet_amount", -1)])
            self.collection.create_index([("win_amount", -1)])
            self.collection.create_index([("current_balance", -1)])
            self.collection.create_index([("response.date", -1)])

    def close(self) -> None:
        if self.client:
            self.client.close()
