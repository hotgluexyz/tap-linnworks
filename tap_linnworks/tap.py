"""Linnworks tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_linnworks import streams


class TapLinnworks(Tap):
    """Linnworks tap class."""

    name = "tap-linnworks"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
            required=True
        ),
        th.Property(
            "application_id",
            th.StringType,
            required=True,
            secret=True,
            description="Application ID",
        ),
        th.Property(
            "application_secret",
            th.StringType,
            required=True,
            secret=True,
            description="Application Secret",
        ),
        th.Property(
            "installation_token",
            th.StringType,
            required=True,
            secret=True,
            description="Application Installation Token",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.LinnworksStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.OpenOrders(self),
            streams.ProcessedOrders(self)
        ]


if __name__ == "__main__":
    TapLinnworks.cli()
