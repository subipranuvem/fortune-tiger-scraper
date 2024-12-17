import logging
from typing import List

from repository.fortune_tiger_interface import FortuneTigerRepository
from repository.mongodb.repository import MongoConfig, MongoRepository
from scraper.image_recognizer import ScraperImageRecognizer, TikaImageRecognizer
from scraper.scraper import FortuneTigerScraper
from scraper.subscriber import FortuneTigerSubscriber, RepositorySubscriber

logging.basicConfig(encoding="utf-8", level=logging.INFO)


class App:
    _logger: logging.Logger

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        self._logger = logger

    def scrape(self) -> None:
        repository: FortuneTigerRepository = MongoRepository(
            MongoConfig(
                connection_string="mongodb://user:pass@localhost:27017/data?authSource=admin",
                database_name="data",
                collection_name="fortune_tiger_logs",
            )
        )
        is_repository_alive = repository.ping()
        if not is_repository_alive:
            self._logger.error("repository is not reacheable")
            return None
        subscribers: List[FortuneTigerSubscriber] = [RepositorySubscriber(repository)]
        image_recognizer: ScraperImageRecognizer = TikaImageRecognizer(
            address="http://localhost:9998"
        )

        scraper = FortuneTigerScraper(image_recognizer=image_recognizer)
        scraper.scrape_data(
            subscribers=subscribers,
        )


if __name__ == "__main__":
    app = App()
    app.scrape()
