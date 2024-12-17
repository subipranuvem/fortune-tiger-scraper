from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class Screenshot(BaseModel):
    image_bytes: bytes = Field()
    width: int = Field(gt=1)
    height: int = Field(gt=1)
    extension: str = Field(min_length=1)


class ScraperImageRecognizer(ABC):
    @abstractmethod
    def get_bet_value(screenshot: Screenshot) -> int:
        """
        Get the value of the bet given the screenshot
        :param Screenshot: Game screenshot in PNG format.
        :return: The bet amount in brazilian cents (centavos).
        """
        pass

    @abstractmethod
    def get_balance(self, screenshot: Screenshot) -> int:
        """
        Get the value of  given the screenshot
        :param Screenshot: Game screenshot in PNG format.
        :return: The current balance in brazilian cents (centavos).
        """
        pass

    @abstractmethod
    def check_if_is_enabled_to_play(self, screenshot: Screenshot) -> bool:
        """
        Get the value of  given the screenshot
        :param Screenshot: Game screenshot in PNG format.
        :return: A bool indicating wheter the game is enabled or not to play.
        """
