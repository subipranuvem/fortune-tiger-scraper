import gzip
import json
import time
from http import HTTPStatus
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
    game_url: str = (
        "https://m.pgsoft-games.com/126/index.html?l=pt&ot=ca7094186b309ee149c55c8822e7ecf2&btt=2&from=https://pgdemo.asia/&language=pt-BR&__refer=m.pg-redirect.net&or=static.pgsoft-games.com"
    )

    def __init__(
        self,
        image_recognizer: ScraperImageRecognizer,
    ):
        self._image_recognizer = image_recognizer

    def scrape_data(
        self,
        subscribers: List[FortuneTigerSubscriber],
    ) -> None:
        try:
            driver = self._create_webdriver()
            is_game_blocked = True
            while is_game_blocked:
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
                    print("Game is blocked")
                    driver.quit()
                    driver = self._create_webdriver()
            self._click_turbo_button(game)
            have_balance = True
            while have_balance:
                self._click_bet_button(game)
                is_able_to_play = False
                while not is_able_to_play:
                    is_able_to_play = (
                        self._image_recognizer.check_if_is_enabled_to_play(
                            screenshot=game.take_screenshot()
                        )
                    )
                    if not is_able_to_play:
                        print("waiting to play ...")
                        time.sleep(0.5)
                self._notify_subscribers(driver, subscribers)
                balance = self._image_recognizer.get_balance(
                    screenshot=game.take_screenshot()
                )
                print(f"actual balance: {balance}")
                have_balance = balance > 0
        except Exception as e:
            print("Ocorreu um erro:", e)
        finally:
            if driver is not None:
                driver.quit()

    def _create_webdriver(self) -> webdriver.Remote:
        chrome_options = uc.ChromeOptions()
        driver = webdriver.Chrome(
            options=chrome_options,
        )
        driver.scopes = [".*api.pg-demo.com/game-api/fortune-tiger/v2/.*"]
        driver.set_window_size(1920, 1080)
        return driver

    def _click_start_button(self, driver: webdriver.Remote) -> None:
        start_button = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='__startedButton']/div")
            )
        )
        start_button.click()

    def _find_game_canvas(self, driver: webdriver.Remote) -> WebElement:
        game_canvas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//canvas[@id='GameCanvas']"))
        )
        return game_canvas

    def _raise_bet(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        for i in range(0, 15):
            game.action_chains.move_to_element_with_offset(
                game.game_canvas,
                randrange(int((x / 100) * 20), int((x / 100) * 25)),
                randrange(int((y / 100) * 40), int((y / 100) * 45)),
            ).click().perform()
        time.sleep(0.5)

    def _click_turbo_button(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 38), int((x / 100) * 41)) * -1,
            randrange(int((y / 100) * 36), int((y / 100) * 39)),
        ).click().perform()
        time.sleep(1)

    def _click_bet_button(self, game: FortuneTigerGame) -> None:
        x = game.game_canvas_width
        y = game.game_canvas_height
        game.action_chains.move_to_element_with_offset(
            game.game_canvas,
            randrange(int((x / 100) * 0), int((x / 100) * 3)) * -1,
            randrange(int((y / 100) * 36), int((y / 100) * 39)),
        ).click().perform()

    def _notify_subscribers(
        self, driver: webdriver.Remote, subscribers: List[FortuneTigerSubscriber]
    ) -> None:
        try:
            request = driver.requests[-1]
            response = request.response
            if response.status_code != HTTPStatus.OK or "Spin" not in request.path:
                return None
            if "gzip" not in response.headers.get("content-encoding"):
                return None
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
            )
            fortune_tiger_data = FortuneTigerData(
                request=fortune_tiger_request,
                response=fortune_tiger_response,
            )
            for subscriber in subscribers:
                subscriber.process_data(data=fortune_tiger_data)
        except Exception as e:
            print(e)
        finally:
            # cleaning the requests
            del driver.requests

    def _check_if_game_is_blocked(self, game: FortuneTigerGame) -> bool:
        try:
            bet_value = self._image_recognizer.get_bet_value(
                screenshot=game.take_screenshot()
            )
            expected_value = 4500
            return bet_value != expected_value
        except Exception as e:
            print(e)
            return True
