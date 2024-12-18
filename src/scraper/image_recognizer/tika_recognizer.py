import logging
import os
import re
from http import HTTPStatus
from io import BytesIO
from urllib.parse import urljoin

import requests
from PIL import Image, ImageChops, ImageStat

from scraper.image_recognizer.interface import ScraperImageRecognizer, Screenshot


class TikaImageRecognizer(ScraperImageRecognizer):
    _address: str
    _logger: logging.Logger

    def __init__(
        self, address: str, logger: logging.Logger = logging.getLogger(__name__)
    ):
        self._address = address
        self._logger = logger
        super().__init__()

    def get_bet_value(self, screenshot: Screenshot) -> int:
        image = Image.open(BytesIO(screenshot.image_bytes))
        pl = int((image.width / 2) - (image.width / 6))
        pr = int((image.width / 2) + (image.width / 6))
        pu = int(image.height * 0.78)
        pd = int(image.height * 0.83)
        crop_rectangle = (pl, pu, pr, pd)
        cropped_image = image.crop(crop_rectangle)
        # Have to resize the image because the original is small
        cropped_image = cropped_image.resize(
            (cropped_image.width * 4, cropped_image.height * 4)
        )
        img_byte_arr = BytesIO()
        cropped_image.save(img_byte_arr, format="PNG")
        cropped_image_bytes = img_byte_arr.getvalue()
        res = self._get_text_from_tika(payload=cropped_image_bytes)
        cropped_image.close()
        try:
            bet = int(res)
            return bet
        except Exception as e:
            self._logger.error(f"getting bet value: {e}")
            return 0

    def get_balance_in_cents(self, screenshot: Screenshot) -> int:
        try:
            image = Image.open(BytesIO(screenshot.image_bytes))
            pl = 0
            pr = int(image.width / 3) + 20  # 20 is an offset
            pu = int(image.height * 0.78)
            pd = int(image.height * 0.83)
            crop_rectangle = (pl, pu, pr, pd)
            cropped_image = image.crop(crop_rectangle)
            # Have to resize the image because the original is small
            cropped_image = cropped_image.resize(
                (cropped_image.width * 4, cropped_image.height * 4)
            )
            img_byte_arr = BytesIO()
            cropped_image.save(img_byte_arr, format="PNG")
            cropped_image_bytes = img_byte_arr.getvalue()
            res = self._get_text_from_tika(payload=cropped_image_bytes)
            cropped_image.close()
            balance = int(res)
            return balance
        except Exception as e:
            self._logger.error(f"getting balance: {e}")
            return 0

    def check_if_is_enabled_to_play(self, screenshot: Screenshot) -> bool:
        try:
            image = Image.open(BytesIO(screenshot.image_bytes))
            pl = int(image.width / 100 * 80)
            pr = int(image.width / 100 * 95)
            pu = int(image.height / 100 * 85)
            pd = int(image.height / 100 * 93)
            crop_rectangle = (pl, pu, pr, pd)
            cropped_image = image.crop(crop_rectangle)
            enabled_button_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "assets/enabled_button.png"
            )
            enabled_button_image = Image.open(enabled_button_path)
            cropped_image = cropped_image.resize(
                (enabled_button_image.width, enabled_button_image.height)
            )
            diff = ImageChops.difference(cropped_image, enabled_button_image)
            stat = ImageStat.Stat(diff)
            mean_diff = sum(stat.mean) / len(stat.mean)
            comparsing_threshold = 8
            is_similar = mean_diff < comparsing_threshold
            cropped_image.close()
            enabled_button_image.close()
            return is_similar
        except Exception as e:
            self._logger.error(f"checking game is enabled to play: {e}")
            return False

    def _get_text_from_tika(self, payload: bytes) -> str:
        url = urljoin(self._address, "/tika")
        headers = {
            "Accept": "text/plain",
            "Content-Type": "image/png",
            "X-Tika-PDFOcrStrategy": "ocr_only",
        }
        response = requests.request("PUT", url, headers=headers, data=payload)
        if response.status_code != HTTPStatus.OK:
            raise Exception(f"tika returned a {response.status_code} status code")
        cleaned_text = self._clean_chars(response.text)
        return cleaned_text

    def _clean_chars(self, extracted_text: str) -> str:
        only_digits_regex = r"[^\d]"
        cleaned_text = re.sub(only_digits_regex, "", extracted_text, 0, re.MULTILINE)
        return cleaned_text
