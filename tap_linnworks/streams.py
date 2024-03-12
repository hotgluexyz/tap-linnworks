"""Stream type classes for tap-linnworks."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from typing import Any, Optional

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
        th.Property("NumOrderId", th.NumberType),
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
        th.Property("TotalItemsSum", th.NumberType),
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
        th.Property("fPostageCost", th.NumberType),
        th.Property("fTotalCharge", th.NumberType),
        th.Property("PostageCostExTax", th.NumberType),
        th.Property("Subtotal", th.NumberType),
        th.Property("fTax", th.NumberType),
        th.Property("TotalDiscount", th.NumberType),
        th.Property("ProfitMargin", th.NumberType),
        th.Property("CountryTaxRate", th.NumberType),
        th.Property("nOrderId", th.NumberType),
        th.Property("nStatus", th.NumberType),
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
        th.Property("ItemWeight", th.NumberType),
        th.Property("TotalWeight", th.NumberType),
        th.Property("HoldOrCancel", th.BooleanType),
        th.Property("IsResend", th.BooleanType),
        th.Property("IsExchange", th.BooleanType),
        th.Property("TaxId", th.StringType),
        th.Property("FulfilmentLocationName", th.StringType),
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
    
    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "processed_order_id": record["pkOrderID"],
        }

class ProcessedOrderDetails(LinnworksStream):
    name = "processed_order_details"
    path = "/Orders/GetOrdersById"
    primary_keys = ["OrderId"]
    replication_key = None
    records_jsonpath = "$.[*]"
    rest_method = "POST"    
    parent_stream_type = ProcessedOrders
    schema = th.PropertiesList(
        th.Property("OrderId", th.StringType),
        th.Property("NumOrderId", th.IntegerType),
        th.Property("Items", th.ArrayType(
            th.ObjectType(
                th.Property("ItemId", th.StringType),
                th.Property("ItemNumber", th.StringType),
                th.Property("SKU", th.StringType),
                th.Property("ItemSource", th.StringType),
                th.Property("Title", th.StringType),
                th.Property("Quantity", th.IntegerType),
                th.Property("CategoryName", th.StringType),
                th.Property("StockLevelsSpecified", th.BooleanType),
                th.Property("OnOrder", th.IntegerType),
                th.Property("Level", th.IntegerType),
                th.Property("AvailableStock", th.IntegerType),
                th.Property("PricePerUnit", th.NumberType),
                th.Property("UnitCost", th.NumberType),
                th.Property("DespatchStockUnitCost", th.NumberType),
                th.Property("Discount", th.NumberType),
                th.Property("Tax", th.NumberType),
                th.Property("TaxRate", th.NumberType),
                th.Property("Cost", th.NumberType),
                th.Property("CostIncTax", th.NumberType),
                th.Property("CompositeSubItems", th.ArrayType(th.ObjectType())),
                th.Property("IsService", th.BooleanType),
                th.Property("SalesTax", th.NumberType),
                th.Property("TaxCostInclusive", th.BooleanType),
                th.Property("PartShipped", th.BooleanType),
                th.Property("Weight", th.NumberType),
                th.Property("BarcodeNumber", th.StringType),
                th.Property("Market", th.IntegerType),
                th.Property("ChannelSKU", th.StringType),
                th.Property("ChannelTitle", th.StringType),
                th.Property("DiscountValue", th.NumberType),
                th.Property("HasImage", th.BooleanType),
                th.Property("AdditionalInfo", th.ArrayType(th.ObjectType())),
                th.Property("StockLevelIndicator", th.IntegerType),
                th.Property("ShippingCost", th.NumberType),
                th.Property("PartShippedQty", th.IntegerType),
                th.Property("BatchNumberScanRequired", th.BooleanType),
                th.Property("SerialNumberScanRequired", th.BooleanType),
                th.Property("BinRack", th.StringType),
                th.Property("BinRacks", th.ArrayType(
                    th.ObjectType(
                        th.Property("Quantity", th.IntegerType),
                        th.Property("BinRack", th.StringType),
                        th.Property("Location", th.StringType)
                    )
                )),
                th.Property("InventoryTrackingType", th.IntegerType),
                th.Property("isBatchedStockItem", th.BooleanType),
                th.Property("IsWarehouseManaged", th.BooleanType),
                th.Property("IsUnlinked", th.BooleanType),
                th.Property("StockItemIntId", th.IntegerType),
                th.Property("RowId", th.StringType),
                th.Property("OrderId", th.StringType),
                th.Property("StockItemId", th.StringType)
            )
        )),
        th.Property("Processed", th.BooleanType),
        th.Property("ProcessedDateTime", th.DateTimeType),
        th.Property("FulfilmentLocationId", th.StringType),
        th.Property("GeneralInfo", th.ObjectType(
                th.Property("Status", th.IntegerType),
                th.Property("LabelPrinted", th.BooleanType),
                th.Property("LabelError", th.StringType),
                th.Property("InvoicePrinted", th.BooleanType),
                th.Property("PickListPrinted", th.BooleanType),
                th.Property("IsRuleRun", th.BooleanType),
                th.Property("Notes", th.IntegerType),
                th.Property("PartShipped", th.BooleanType),
                th.Property("IsParked", th.BooleanType),
                th.Property("ReferenceNum", th.StringType),
                th.Property("SecondaryReference", th.StringType),
                th.Property("ExternalReferenceNum", th.StringType),
                th.Property("ReceivedDate", th.DateTimeType),
                th.Property("Source", th.StringType),
                th.Property("SubSource", th.StringType),
                th.Property("HoldOrCancel", th.BooleanType),
                th.Property("DespatchByDate", th.DateTimeType),
                th.Property("HasScheduledDelivery", th.BooleanType),
                th.Property("Location", th.StringType),
                th.Property("NumItems", th.IntegerType),
        )),
        th.Property("ShippingInfo", th.ObjectType(
                th.Property("Vendor", th.StringType),
                th.Property("PostalServiceId", th.StringType),
                th.Property("PostalServiceName", th.StringType),
                th.Property("TotalWeight", th.NumberType),
                th.Property("ItemWeight", th.NumberType),
                th.Property("PackageCategoryId", th.StringType),
                th.Property("PackageCategory", th.StringType),
                th.Property("PackageTypeId", th.StringType),
                th.Property("PackageType", th.StringType),
                th.Property("PostageCost", th.NumberType),
                th.Property("PostageCostExTax", th.NumberType),
                th.Property("TrackingNumber", th.StringType),
                th.Property("ManualAdjust", th.BooleanType),
        )),
        th.Property("CustomerInfo", th.ObjectType(
                th.Property("ChannelBuyerName", th.StringType),
                th.Property("Address", th.ObjectType(
                        th.Property("EmailAddress", th.StringType),
                        th.Property("Address1", th.StringType),
                        th.Property("Address2", th.StringType),
                        th.Property("Address3", th.StringType),
                        th.Property("Town", th.StringType),
                        th.Property("Region", th.StringType),
                        th.Property("PostCode", th.StringType),
                        th.Property("Country", th.StringType),
                        th.Property("FullName", th.StringType),
                        th.Property("Company", th.StringType),
                        th.Property("PhoneNumber", th.StringType),
                        th.Property("CountryId", th.StringType),
                )),
                th.Property("BillingAddress", th.ObjectType(
                        th.Property("EmailAddress", th.StringType),
                        th.Property("Address1", th.StringType),
                        th.Property("Address2", th.StringType),
                        th.Property("Address3", th.StringType),
                        th.Property("Town", th.StringType),
                        th.Property("Region", th.StringType),
                        th.Property("PostCode", th.StringType),
                        th.Property("Country", th.StringType),
                        th.Property("FullName", th.StringType),
                        th.Property("Company", th.StringType),
                        th.Property("PhoneNumber", th.StringType),
                        th.Property("CountryId", th.StringType),
                )),
            
        )),
        th.Property("TotalsInfo", th.ObjectType(
                th.Property("Subtotal", th.NumberType),
                th.Property("PostageCost", th.NumberType),
                th.Property("PostageCostExTax", th.NumberType),
                th.Property("Tax", th.NumberType),
                th.Property("TotalCharge", th.NumberType),
                th.Property("PaymentMethod", th.StringType),
                th.Property("PaymentMethodId", th.StringType),
                th.Property("ProfitMargin", th.NumberType),
                th.Property("TotalDiscount", th.NumberType),
                th.Property("Currency", th.StringType),
                th.Property("CountryTaxRate", th.NumberType),
                th.Property("ConversionRate", th.NumberType),
        )),
        th.Property("ExtendedProperties", th.ArrayType(th.ObjectType())),
        th.Property("FolderName", th.ArrayType(th.StringType)),
        th.Property("Notes", th.ArrayType(th.StringType))
    
    ).to_dict()

    def prepare_request_payload(self, context: dict | None, next_page_token: Any | None) -> dict | None:

        return {
            "pkOrderIds": [
                context["processed_order_id"]
            ]
        }

    def get_next_page_token(self, response, previous_token):
        return None