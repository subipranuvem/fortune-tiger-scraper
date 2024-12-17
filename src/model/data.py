from typing import Dict
from urllib.parse import parse_qs

from pydantic import BaseModel, Field


class FortuneTigerRequest(BaseModel):
    headers: Dict = Field()
    query_string: str = Field()
    body: Dict = Field()
    method: str = Field()
    path: str = Field()
    host: str = Field()
    url: str = Field()
    body_format: str = "Form Value"

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
