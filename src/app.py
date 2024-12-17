from typing import List

from repository.fortune_tiger_interface import FortuneTigerRepository
from repository.mongodb.repository import MongoConfig, MongoRepository
from scraper.image_recognizer import ScraperImageRecognizer, TikaImageRecognizer
from scraper.scraper import FortuneTigerScraper
from scraper.subscriber import FortuneTigerSubscriber, RepositorySubscriber


class App:
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
            print("repository is not reacheable")
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
