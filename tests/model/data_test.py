import pytest
from pydantic import ValidationError
from src.model.data import FortuneTigerRequest, FortuneTigerResponse


class TestFortuneTigerRequest:
    def test_valid_request(self):
        request_data = {
            "headers": {"Content-Type": "application/json"},
            "query_string": "key1=value1&key2=value2",
            "body": {"example": "data"},
            "method": "GET",
            "path": "/api/test",
            "host": "localhost",
            "url": "http://localhost/api/test",
        }
        request = FortuneTigerRequest(**request_data)

        assert request.headers == {"Content-Type": "application/json"}
        assert request.query_string == "key1=value1&key2=value2"
        assert request.query_string_map == {"key1": ["value1"], "key2": ["value2"]}
        assert request.body_format == "Form Value"

    def test_invalid_request_missing_fields(self):
        with pytest.raises(ValidationError):
            FortuneTigerRequest(
                headers={"Content-Type": "application/json"},
                query_string="key1=value1&key2=value2",
            )

    def test_query_string_map(self):
        request_data = {
            "headers": {"Content-Type": "application/json"},
            "query_string": "key=value1&key=value2",
            "body": {},
            "method": "GET",
            "path": "/api/test",
            "host": "localhost",
            "url": "http://localhost/api/test",
        }
        request = FortuneTigerRequest(**request_data)
        assert request.query_string_map == {"key": ["value1", "value2"]}

    def test_body_format_default(self):
        request_data = {
            "headers": {"Content-Type": "application/json"},
            "query_string": "",
            "body": {},
            "method": "GET",
            "path": "/api/test",
            "host": "localhost",
            "url": "http://localhost/api/test",
        }
        request = FortuneTigerRequest(**request_data)
        assert request.body_format == "Form Value"


class TestFortuneTigerResponse:
    def test_valid_response(self):
        response_data = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": {"success": True},
        }
        response = FortuneTigerResponse(**response_data)

        assert response.status_code == 200
        assert response.headers == {"Content-Type": "application/json"}
        assert response.body == {"success": True}

    def test_invalid_status_code(self):
        response_data = {
            "status_code": 99,
            "headers": {"Content-Type": "application/json"},
            "body": {"success": True},
        }
        with pytest.raises(ValidationError):
            FortuneTigerResponse(**response_data)

    def test_missing_fields(self):
        response_data = {
            "status_code": 200,
        }
        with pytest.raises(ValidationError):
            FortuneTigerResponse(**response_data)
