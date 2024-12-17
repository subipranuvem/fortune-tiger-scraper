from model.data import FortuneTigerData
from repository.fortune_tiger_interface import FortuneTigerRepository


class RepositorySubscriber:

    repository: FortuneTigerRepository

    def __init__(self, repository: FortuneTigerRepository):
        self.repository = repository

    def process_data(self, data: FortuneTigerData):
        inserted_id = self.repository.save_data(data)
        print(inserted_id)
