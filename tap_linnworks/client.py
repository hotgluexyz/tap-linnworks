"""REST client handling, including LinnworksStream base class."""

from __future__ import annotations

import sys
import requests
from pendulum import parse
from datetime import timedelta
from typing import Any, Callable, Iterable, Optional, List, cast

from tap_linnworks.authenticator import LinnworksAuthenticator
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

def _find_in_partitions_list(
    partitions: List[dict], state_partition_context: dict
) -> Optional[dict]:
    found = [
        partition_state
        for partition_state in partitions
        if partition_state["context"] == state_partition_context
    ]
    if len(found) > 1:
        raise ValueError(
            f"State file contains duplicate entries for partition: "
            "{state_partition_context}.\n"
            f"Matching state values were: {str(found)}"
        )
    if found:
        return cast(dict, found[0])

    return None


def get_state_if_exists(
    tap_state: dict,
    tap_stream_id: str,
    state_partition_context: Optional[dict] = None,
    key: Optional[str] = None,
) -> Optional[Any]:
    if "bookmarks" not in tap_state:
        return None
    if tap_stream_id not in tap_state["bookmarks"]:
        return None

    skip_incremental_partitions = [
        "processed_order_item_images",
        "processed_order_items",
        "processed_order_details",
    ]
    stream_state = tap_state["bookmarks"][tap_stream_id]
    if tap_stream_id in skip_incremental_partitions and "partitions" in stream_state:
        # stream_state["partitions"] = []
        partitions = stream_state["partitions"][len(stream_state["partitions"]) - 1][
            "context"
        ]
        stream_state["partitions"] = [{"context": partitions}]

    if not state_partition_context:
        if key:
            return stream_state.get(key, None)
        return stream_state
    if "partitions" not in stream_state:
        return None  # No partitions defined

    matched_partition = _find_in_partitions_list(
        stream_state["partitions"], state_partition_context
    )
    if matched_partition is None:
        return None  # Partition definition not present
    if key:
        return matched_partition.get(key, None)
    return matched_partition


def get_state_partitions_list(
    tap_state: dict, tap_stream_id: str
) -> Optional[List[dict]]:
    """Return a list of partitions defined in the state, or None if not defined."""
    return (get_state_if_exists(tap_state, tap_stream_id) or {}).get("partitions", None)
class LinnworksStream(RESTStream):
    """Linnworks stream class."""

    @property
    def url_base(self) -> str:
        return "https://eu-ext.linnworks.net/api"

    records_jsonpath = "$[*]"
    next_page_token_jsonpath = "$.next_page"

    @property
    def partitions(self) -> Optional[List[dict]]:
        #Suppress partitions
        result: List[dict] = []
        for partition_state in (
            get_state_partitions_list(self.tap_state, self.name) or []
        ):
            result.append(partition_state["context"])
        if result is not None and len(result) > 0:
            result = [result[len(result) - 1]]
        return result or None

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
        params = {}
        if self.name == "processed_order_item_images":
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
