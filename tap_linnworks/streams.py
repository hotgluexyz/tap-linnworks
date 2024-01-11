"""Stream type classes for tap-linnworks."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from typing import Any

from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_linnworks.client import LinnworksStream

if sys.version_info >= (3, 9):
    import importlib.resources as importlib_resources
else:
    import importlib_resources


class OpenOrders(LinnworksStream):
    name = "open_orders"
    path = "/Orders/GetOpenOrders"
    primary_keys = ["NumOrderId"]
    replication_key = "ReceivedDate"
    records_jsonpath = "$.Data[*]"
    rest_method = "POST"

    schema = th.PropertiesList(
        th.Property("NumOrderId", th.IntegerType),
        th.Property("ReceivedDate", th.DateTimeType),
        th.Property("GeneralInfo", th.CustomType({"type": ["object", "string"]})),
        th.Property("ShippingInfo", th.CustomType({"type": ["object", "string"]})),
        th.Property("CustomerInfo", th.CustomType({"type": ["object", "string"]})),
        th.Property("TotalsInfo", th.CustomType({"type": ["object", "string"]})),
        th.Property("TaxInfo", th.CustomType({"type": ["object", "string"]})),
        th.Property("FolderName", th.CustomType({"type": ["array", "string"]})),
        th.Property("IsPostFilteredOut", th.BooleanType),
        th.Property("CanFulfil", th.BooleanType),
        th.Property("Fulfillment", th.CustomType({"type": ["object", "string"]})),
        th.Property("Items", th.CustomType({"type": ["array", "string"]})),
        th.Property("HasItems", th.BooleanType),
        th.Property("TotalItemsSum", th.IntegerType),
        th.Property("OrderId", th.StringType),
    ).to_dict()

    def parse_response(self, response):
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def post_process(self, row, context={}):
        row = super().post_process(row, context)
        row["ReceivedDate"] = row["GeneralInfo"]["ReceivedDate"]
        return row

    def prepare_request_payload(self, context: dict | None, next_page_token: Any | None) -> dict | None:
        start_date = self.get_starting_time(context)

        if next_page_token is None:
            next_page_token = 1

        return {
            "filters": {
                "DateFields": [
                {
                    "DateFrom": start_date.isoformat(),
                    "Type": "Range",
                    "FieldCode": "GENERAL_INFO_DATE"
                }
                ]
            },
            "entriesPerPage": 500,
            "pageNumber": next_page_token,
            "sorting": [
                {
                "FieldCode": "GENERAL_INFO_DATE",
                "Direction": "Descending"
                }
            ]
        }


class ProcessedOrders(LinnworksStream):
    name = "processed_orders"
    path = "/ProcessedOrders/SearchProcessedOrders"
    primary_keys = ["NumOrderId"]
    replication_key = "dProcessedOn"
    records_jsonpath = "$.ProcessedOrders.Data[*]"
    rest_method = "POST"

    schema = th.PropertiesList(
        th.Property("pkOrderID", th.StringType),
        th.Property("dReceivedDate", th.DateTimeType),
        th.Property("dProcessedOn", th.DateTimeType),
        th.Property("timeDiff", th.NumberType),
        th.Property("fPostageCost", th.IntegerType),
        th.Property("fTotalCharge", th.IntegerType),
        th.Property("PostageCostExTax", th.IntegerType),
        th.Property("Subtotal", th.IntegerType),
        th.Property("fTax", th.IntegerType),
        th.Property("TotalDiscount", th.IntegerType),
        th.Property("ProfitMargin", th.IntegerType),
        th.Property("CountryTaxRate", th.IntegerType),
        th.Property("nOrderId", th.IntegerType),
        th.Property("nStatus", th.IntegerType),
        th.Property("cCurrency", th.StringType),
        th.Property("PostalTrackingNumber", th.StringType),
        th.Property("cCountry", th.StringType),
        th.Property("Source", th.StringType),
        th.Property("PostalServiceName", th.StringType),
        th.Property("PostalServiceCode", th.StringType),
        th.Property("ReferenceNum", th.StringType),
        th.Property("SecondaryReference", th.StringType),
        th.Property("ExternalReference", th.StringType),
        th.Property("Address1", th.StringType),
        th.Property("Address2", th.StringType),
        th.Property("Address3", th.StringType),
        th.Property("Town", th.StringType),
        th.Property("Region", th.StringType),
        th.Property("BuyerPhoneNumber", th.StringType),
        th.Property("Company", th.StringType),
        th.Property("SubSource", th.StringType),
        th.Property("ChannelBuyerName", th.StringType),
        th.Property("AccountName", th.StringType),
        th.Property("cFullName", th.StringType),
        th.Property("cEmailAddress", th.StringType),
        th.Property("cPostCode", th.StringType),
        th.Property("dPaidOn", th.DateTimeType),
        th.Property("dCancelledOn", th.DateTimeType),
        th.Property("ItemWeight", th.IntegerType),
        th.Property("TotalWeight", th.IntegerType),
        th.Property("HoldOrCancel", th.BooleanType),
        th.Property("IsResend", th.BooleanType),
        th.Property("IsExchange", th.BooleanType),
        th.Property("TaxId", th.StringType),
        th.Property("FulfilmentLocationName", th.StringType)
    ).to_dict()

    def parse_response(self, response):
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def get_next_page_token(self, response, previous_token):
        root = response.json().get("ProcessedOrders")
        actual_page = root.get("PageNumber")
        total_pages = root.get("TotalPages")

        if actual_page < total_pages:
            return actual_page + 1

        return None

    def prepare_request_payload(self, context: dict | None, next_page_token: Any | None) -> dict | None:
        start_date = self.get_starting_time(context).isoformat()
        now = (datetime.now() + timedelta(days=1)).isoformat()

        if next_page_token is None:
            next_page_token = 1

        return {
            "request": {
                "PageNumber": 1,
                "ResultsPerPage": 500,
                "DateField": "processed",
                "FromDate": start_date,
                "ToDate": now,
                "SearchSorting": {
                    "SortField": "dProcessedOn",
                    "SortDirection": "DESC"
                },
            }
        }
