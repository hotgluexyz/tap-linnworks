"""REST client handling, including LinnworksStream base class."""

from __future__ import annotations

import sys
import requests
from pendulum import parse
from datetime import timedelta
from typing import Any, Callable, Iterable

from authenticator import LinnworksAuthenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator  # noqa: TCH002
from singer_sdk.streams import RESTStream

if sys.version_info >= (3, 9):
    import importlib.resources as importlib_resources
else:
    import importlib_resources

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]

# TODO: Delete this is if not using json files for schema definition
SCHEMAS_DIR = importlib_resources.files(__package__) / "schemas"


class LinnworksStream(RESTStream):
    """Linnworks stream class."""

    @property
    def url_base(self) -> str:
        return "https://eu-ext.linnworks.net/api"

    records_jsonpath = "$[*]"
    next_page_token_jsonpath = "$.next_page"

    @property
    def authenticator(self) -> LinnworksAuthenticator:
        return LinnworksAuthenticator.create_for_stream(
            self,
            application_id=self.config.get("application_id"),
            application_secret=self.config.get("application_secret"),
            installation_token=self.config.get("installation_token"),
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
        return {}

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
