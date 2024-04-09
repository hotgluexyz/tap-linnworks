"""REST client handling, including LinnworksStream base class."""

from __future__ import annotations

import sys
import requests
from pendulum import parse
from datetime import timedelta
from typing import Any, Callable, Iterable

from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator
from singer_sdk.streams import RESTStream
from singer_sdk.authenticators import APIKeyAuthenticator

if sys.version_info >= (3, 9):
    import importlib.resources as importlib_resources
else:
    import importlib_resources

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]

class LinnworksStream(RESTStream):
    """Linnworks stream class."""

    @property
    def url_base(self) -> str:
        return "https://eu-ext.linnworks.net/api"

    records_jsonpath = "$[*]"
    next_page_token_jsonpath = "$.next_page"

    @property
    def authenticator(self):
        if self._tap.api_key == "":
            body = {
                "Token": self.config.get("installation_token"),
                "ApplicationId": self.config.get("application_id"),
                "ApplicationSecret": self.config.get("application_secret")
            }
            response = requests.post(
                "https://api.linnworks.net/api/Auth/AuthorizeByApplication",
                json=body
            )
            response.raise_for_status()
            self._tap.api_key = response.json()["Token"]

        return APIKeyAuthenticator.create_for_stream(
            self, key="Authorization", value=self._tap.api_key, location="header"
        )

    @property
    def http_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_next_page_token(self, response, previous_token):
        actual_page = response.json().get("PageNumber")
        total_pages = response.json().get("TotalPages")

        if actual_page < total_pages:
            return actual_page + 1

        return None

    def get_url_params(
        self,
        context: dict | None,  # noqa: ARG002
        next_page_token: Any | None,  # noqa: ANN401
    ) -> dict[str, Any]:
        params = {}
        if self.name == "stock_item_images":
            params['inventoryItemId'] = context.get("ItemId")
        return params

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def get_starting_time(self, context):
        start_date = self.config.get("start_date")
        if start_date:
            start_date = parse(self.config.get("start_date"))
        rep_key = self.get_starting_timestamp(context)

        if rep_key is None:
            return start_date

        return rep_key + timedelta(seconds=1)

# Possible products endpoint: https://eu-ext.linnworks.net/api/Stock/GetStockItemsFull
