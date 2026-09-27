"""
Pydantic Schemas Package
========================
Request and response models for the API.
"""

# Common
from app.schemas.common import (
    PaginatedResponse,
    ErrorResponse,
    ImageInfo,
    ImageSource,
    PaginationParams,
    TimestampMixin,
)

# Vegetable
from app.schemas.vegetable import (
    VegetableBase, VegetableCreate, VegetableUpdate, VegetableRead, VegetableListItem,
)

# Farmer
from app.schemas.farmer import (
    FarmerBase, FarmerCreate, FarmerUpdate, FarmerRead, FarmerListItem, FarmerPerformance,
)

# Customer
from app.schemas.customer import (
    CustomerBase, CustomerCreate, CustomerUpdate, CustomerRead, CustomerListItem, CustomerStats,
)

# Employee
from app.schemas.employee import (
    EmployeeBase, EmployeeCreate, EmployeeUpdate, EmployeeRead, EmployeeListItem,
)

# Grade
from app.schemas.grade import (
    GradeBase, GradeCreate, GradeUpdate, GradeRead, GradeListItem,
)

# Lot
from app.schemas.lot import (
    LotBase, LotCreate, LotUpdate, LotRead, LotListItem, LotProfitLoss, CostBreakdown,
)

# Sale
from app.schemas.sale import (
    SaleBase, SaleCreate, SaleUpdate, SaleRead, SaleListItem,
    SaleItemBase, SaleItemCreate, SaleItemRead, SalesSummary,
)

# Inventory
from app.schemas.inventory import (
    InventoryBase, InventoryCreate, InventoryUpdate, InventoryRead, InventoryListItem,
    InventoryTransactionBase, InventoryTransactionCreate, InventoryTransactionRead,
    InventoryTransactionListItem,
)

# Purchase Order
from app.schemas.purchase_order import (
    PurchaseOrderBase, PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderRead,
    PurchaseOrderListItem,
    POItemBase, POItemCreate, POItemRead,
)

# Dashboard
from app.schemas.dashboard import (
    KPISummary, TimeSeriesPoint, RevenueTimeSeries, SalesVolumeTimeSeries,
    GradeDistribution, VegetableBreakdown, SupplierPerformance,
    DashboardData, DashboardAlert,
    ForecastPoint, ForecastResponse,
)
