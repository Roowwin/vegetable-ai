"""
Shared Enums
============
Python enums used across multiple models.

Using enums instead of raw strings gives us:
- Type safety (typos caught at import time)
- Autocomplete in IDEs
- Clear documentation of allowed values
"""

import enum


class PurchaseOrderStatus(str, enum.Enum):
    """Lifecycle states of a purchase order."""
    DRAFT = "Draft"
    ISSUED = "Issued"
    ACKNOWLEDGED = "Acknowledged"
    PARTIALLY_RECEIVED = "PartiallyReceived"
    FULLY_RECEIVED = "FullyReceived"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class LotStatus(str, enum.Enum):
    """Lifecycle states of a lot."""
    REGISTERED = "Registered"
    SKIDDED = "Skidded"
    SORTED = "Sorted"
    TESTED = "Tested"
    GRADED = "Graded"
    IN_INVENTORY = "InInventory"
    ON_SALE = "OnSale"
    PARTIALLY_SOLD = "PartiallySold"
    FULLY_SOLD = "FullySold"
    DISCOUNTED = "Discounted"
    CLOSED = "Closed"
    RECYCLED = "Recycled"


class AssetStatus(str, enum.Enum):
    """Status of an individual asset/item."""
    REGISTERED = "Registered"
    IN_INVENTORY = "InInventory"
    ON_SALE = "OnSale"
    SOLD = "Sold"
    DISCOUNTED = "Discounted"
    RECYCLED = "Recycled"
    WRITTEN_OFF = "WrittenOff"


class InventoryTransactionType(str, enum.Enum):
    """Types of stock movements."""
    RECEIVED = "Received"        # Added to inventory
    SOLD = "Sold"                # Removed via sale
    ADJUSTMENT = "Adjustment"    # Manual correction (damage, loss)
    TRANSFER = "Transfer"        # Moved between locations
    RETURNED = "Returned"        # Customer return


class SaleStatus(str, enum.Enum):
    """Status of a sale transaction."""
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"


class UnitType(str, enum.Enum):
    """How a product is sold."""
    KG = "kg"
    PIECE = "piece"
    HALF = "half"
    QUARTER = "quarter"
    BUNCH = "bunch"
    CRATE = "crate"
    CUSTOM = "custom"


class CostCategory(str, enum.Enum):
    """Categories of costs."""
    ACQUISITION = "Acquisition"
    TRANSPORT = "Transport"
    PROCESSING = "Processing"
    STORAGE = "Storage"
    SELLING = "Selling"
    WASTE = "Waste"
    OVERHEAD = "Overhead"


class AllocationMethod(str, enum.Enum):
    """How a shared cost is distributed across items."""
    FIXED_PER_LOT = "FixedPerLot"
    WEIGHT_BASED = "WeightBased"
    COUNT_BASED = "CountBased"
    TIME_BASED = "TimeBased"
    VOLUME_BASED = "VolumeBased"


class ProcessingEventType(str, enum.Enum):
    """Types of events in the audit log."""
    LOT_REGISTERED = "LotRegistered"
    SKID_REGISTERED = "SkidRegistered"
    ASSET_REGISTERED = "AssetRegistered"
    SORT_COMPLETED = "SortCompleted"
    TEST_COMPLETED = "TestCompleted"
    GRADE_ASSIGNED = "GradeAssigned"
    INVENTORY_ADJUSTED = "InventoryAdjusted"
    PRICE_SET = "PriceSet"
    SALE_RECORDED = "SaleRecorded"
    COST_RECORDED = "CostRecorded"
    STATUS_CHANGED = "StatusChanged"


class ForecastTargetType(str, enum.Enum):
    """What a forecast predicts."""
    SALES_VOLUME = "SalesVolume"
    REVENUE = "Revenue"
    PROFIT = "Profit"
    DEMAND = "Demand"
    WASTE = "Waste"
    DAYS_TO_SELLOUT = "DaysToSellout"


class AIToolCallStatus(str, enum.Enum):
    """Status of an AI tool invocation."""
    SUCCESS = "Success"
    FAILED = "Failed"
    TIMEOUT = "Timeout"
    REJECTED = "Rejected"  # Failed validation or authorization
