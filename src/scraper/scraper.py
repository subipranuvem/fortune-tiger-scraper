import gzip
import json
import time
from http import HTTPStatus
from logging import Logger, getLogger
from random import randrange
from typing import List
from urllib.parse import parse_qs

import seleniumwire.undetected_chromedriver as uc
from pydantic import BaseModel, ConfigDict
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

from model.data import FortuneTigerData, FortuneTigerRequest, FortuneTigerResponse
from scraper.balance_printer import BalancePrinter
from scraper.image_recognizer import ScraperImageRecognizer, Screenshot
from scraper.subscriber.interface import FortuneTigerSubscriber


class FortuneTigerGame(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    game_canvas: WebElement
    action_chains: ActionChains

    @property
    def game_canvas_width(self) -> int:
        return self.game_canvas.size["width"]

    @property
    def game_canvas_height(self) -> int:
        return self.game_canvas.size["height"]

    def take_screenshot(self) -> Screenshot:
        return Screenshot(
            image_bytes=self.game_canvas.screenshot_as_png,
            width=self.game_canvas_width,
            height=self.game_canvas_height,
            extension="png",
        )


class FortuneTigerScraper:
    _image_recognizer: ScraperImageRecognizer
    _logger: Logger
    game_url: str = (
        "https://m.pgsoft-games.com/126/index.html?l=pt&ot=ca7094186b309ee149c55c8822e7ecf2&btt=2&from=https://pgdemo.asia/&language=pt-BR&__refer=m.pg-redirect.net&or=static.pgsoft-games.com"
    )

    def __init__(
        self,
        image_recognizer: ScraperImageRecognizer,
        logger: Logger = getLogger(__name__),
    ):
        self._image_recognizer = image_recognizer
        self._logger = logger

    def scrape_data(
        self,
        subscribers: List[FortuneTigerSubscriber],
        headless: bool = True,
    ) -> None:
        try:
            driver = self._create_webdriver(headless)
            is_game_blocked = True
            while is_game_blocked:
                self._logger.info(f"accessing game url")
                driver.get(self.game_url)
                self._click_start_button(driver)
                game_canvas = self._find_game_canvas(driver)
                actions = ActionChains(driver)
                game = FortuneTigerGame(
                    game_canvas=game_canvas,
                    action_chains=actions,
                )
                self._raise_bet(game)
                is_game_blocked = self._check_if_game_is_blocked(game)
                if is_game_blocked:
                    self._logger.warning(f"game is blocked")
                    driver.quit()
                    driver = self._create_webdriver(headless)
            self._click_turbo_button(game)
            have_balance = True
            while have_balance:
                self._start_automate_bet(game)
                is_able_to_play = False
                while not is_able_to_play:
                    is_able_to_play = (
                        self._image_recognizer.check_if_is_enabled_to_play(
                            screenshot=game.take_screenshot()
                        )
                    )
                    if not is_able_to_play:
                        self._logger.info(f"waiting the game to play again")
                        time.sleep(1)
                self._notify_subscribers(driver, subscribers)
                balance_in_cents = self._image_recognizer.get_balance_in_cents(
                    screenshot=game.take_screenshot()
                )
                BalancePrinter.print_balance(self._logger, balance_in_cents)
                have_balance = balance_in_cents > 0
        except Exception as e:
            self._logger.error(f"error at scraper execution: {e}", exc_info=True)
        finally:
            if driver is not None:
                driver.close()
                driver.quit()

    def _create_webdriver(self, headless: bool) -> webdriver.Remote:
        chrome_options = uc.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(
            options=chrome_options,
        )
        driver.scopes = [".*api.pg-demo.com/game-api/fortune-tiger/v2/.*"]
        driver.set_window_size(1920, 1080)
        self._logger.info("creating a new webdriver")
        return driver

    def _click_start_button(self, driver: webdriver.Remote) -> None:
        self._logger.info(f"waiting to start button to render")
        start_button = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='__startedButton']/div")
            )
        )
        start_button.click()
        self._logger.info("start button clicked")

    def _find_game_canvas(self, driver: webdriver.Remote) -> WebElement:
        game_canvas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//canvas[@id='GameCanvas']"))
        )
        self._logger.info("game canvas found")
        return game_canvas

    def _raise_bet(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        self._logger.info("raising bet")
        for i in range(0, 15):
            game.action_chains.move_to_element_with_offset(
                game.game_canvas,
                randrange(int((x / 100) * 20), int((x / 100) * 25)),
                randrange(int((y / 100) * 40), int((y / 100) * 45)),
            ).click().perform()
        self._logger.info("bet raised")
        time.sleep(0.5)

    def _click_turbo_button(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 38), int((x / 100) * 41)) * -1,
            randrange(int((y / 100) * 36), int((y / 100) * 39)),
        ).click().perform()
        self._logger.info("clicked turbo button")
        time.sleep(1)

    def _start_automate_bet(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 38), int((x / 100) * 41)),
            randrange(int((y / 100) * 36), int((y / 100) * 39)),
        ).click().perform()
        self._logger.info("clicked auto button")
        time.sleep(1)
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 30), int((x / 100) * 35)) * -1,
            randrange(int((y / 100) * 27), int((y / 100) * 30)),
        ).click().perform()
        self._logger.info("clicked 10")
        time.sleep(1)
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 0), int((x / 100) * 5)),
            randrange(int((y / 100) * 37), int((y / 100) * 40)),
        ).click().perform()
        self._logger.info("starting auto bet")

    def _click_bet_button(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 0), int((x / 100) * 3)) * -1,
            randrange(int((y / 100) * 36), int((y / 100) * 39)),
        ).click().perform()
        self._logger.info("perform bet")

    def _notify_subscribers(
        self, driver: webdriver.Remote, subscribers: List[FortuneTigerSubscriber]
    ) -> None:
        try:
            self._logger.info("notifying subscribers")

            for request in driver.iter_requests():
                response = request.response
                if response.status_code != HTTPStatus.OK or "Spin" not in request.path:
                    continue
                if "gzip" not in response.headers.get("content-encoding"):
                    continue
                uncompressed_body = gzip.decompress(response.body)
                response_data = json.loads(uncompressed_body)
                fortune_tiger_request = FortuneTigerRequest(
                    body=parse_qs(request.body.decode()),
                    headers=dict(request.headers),
                    host=request.host,
                    method=request.method,
                    path=request.path,
                    url=request.url,
                    query_string=request.querystring,
                )
                fortune_tiger_response = FortuneTigerResponse(
                    headers=dict(response.headers),
                    status_code=response.status_code,
                    body=response_data,
                    date=response.date,
                )
                fortune_tiger_data = FortuneTigerData(
                    request=fortune_tiger_request,
                    response=fortune_tiger_response,
                )
                for subscriber in subscribers:
                    subscriber.process_data(data=fortune_tiger_data)
            self._logger.info("all subscribers notified")
        except Exception as e:
            self._logger.error(f"error at notifying subscribers: {e}")
        finally:
            del driver.requests
            self._logger.info("cleaning driver requests")

    def _check_if_game_is_blocked(self, game: FortuneTigerGame) -> bool:
        try:
            bet_value = self._image_recognizer.get_bet_value(
                screenshot=game.take_screenshot()
            )
            expected_value = 4500
            return bet_value != expected_value
        except Exception as e:
            self._logger.error(f"error at checking if the game is blocked: {e}")
            return True
