from typing import Dict
from urllib.parse import parse_qs

from pydantic import BaseModel, Field, computed_field


class FortuneTigerRequest(BaseModel):
    headers: Dict = Field()
    query_string: str = Field()
    body: Dict = Field()
    method: str = Field()
    path: str = Field()
    host: str = Field()
    url: str = Field()
    body_format: str = "Form Value"

    @computed_field
    @property
    def query_string_map(self) -> Dict:
        query_string_map = parse_qs(self.query_string)
        return query_string_map


class FortuneTigerResponse(BaseModel):
    status_code: int = Field(gt=100, lt=600)
    headers: Dict = Field()
    body: Dict = Field()


class FortuneTigerData(BaseModel):
    request: FortuneTigerRequest
    response: FortuneTigerResponse

    @computed_field
    @property
    def game_id(self) -> str:
        try:
            return self.request.body["atk"][0]
        except Exception as e:
            return 0

    @computed_field
    @property
    def bet_profit(self) -> int:
        try:
            return int(self.response.body["dt"]["si"]["np"])
        except Exception as e:
            return 0

    @computed_field
    @property
    def bet_amount(self) -> int:
        try:
            return int(self.response.body["dt"]["si"]["tb"])
        except Exception as e:
            return 0

    @computed_field
    @property
    def win_amount(self) -> int:
        try:
            return int(self.response.body["dt"]["si"]["tw"])
        except Exception as e:
            return 0
