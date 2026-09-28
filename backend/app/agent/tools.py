"""
AI Agent Tools
==============
Functions the AI can call to get real business data.

Each tool wraps a service method and provides:
- name: Short identifier
- description: What the tool does (AI reads this to decide when to use it)
- parameters: JSON schema for arguments
- function: The actual callable
"""

import json
from typing import Any, Callable
from dataclasses import dataclass


@dataclass
class Tool:
    """Definition of a tool the AI can call."""
    name: str
    description: str
    parameters: dict  # JSON Schema
    function: Callable


# Registry of all available tools
TOOL_REGISTRY: dict[str, Tool] = {}


def register_tool(
    name: str,
    description: str,
    parameters: dict,
):
    """Decorator to register a function as an AI tool."""
    def decorator(func: Callable) -> Callable:
        TOOL_REGISTRY[name] = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=func,
        )
        return func
    return decorator


# ============================================
# LOT TOOLS
# ============================================

@register_tool(
    name="get_lot",
    description="Get details about a specific lot by its code (e.g., 'L-2026-00001'). Returns lot status, weight, acquisition cost, and current location.",
    parameters={
        "type": "object",
        "properties": {
            "lot_code": {
                "type": "string",
                "description": "The lot code, e.g., 'L-2026-00070'"
            }
        },
        "required": ["lot_code"]
    }
)
def get_lot(lot_code: str) -> dict:
    """Get lot details by code."""
    from app.services.lot_service import LotService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = LotService(db)
        lot = service.get_by_code(lot_code)
        if not lot:
            return {"error": f"Lot {lot_code} not found"}
        return {
            "lot_code": lot.lot_code,
            "status": lot.status,
            "total_weight_kg": float(lot.total_weight_kg),
            "acquisition_cost": float(lot.acquisition_cost),
            "current_location_id": lot.current_location_id,
            "acquired_at": lot.acquired_at.isoformat(),
        }
    finally:
        db.close()


@register_tool(
    name="get_lot_pnl",
    description="Get the complete profit and loss breakdown for a lot. Returns costs (acquisition, transport, processing, storage, waste), revenue, gross/net profit, and margins. This is the most important tool for understanding lot profitability.",
    parameters={
        "type": "object",
        "properties": {
            "lot_code": {
                "type": "string",
                "description": "The lot code, e.g., 'L-2026-00070'"
            }
        },
        "required": ["lot_code"]
    }
)
def get_lot_pnl(lot_code: str) -> dict:
    """Get P&L breakdown for a lot."""
    from app.services.lot_service import LotService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = LotService(db)
        pnl = service.compute_lot_pnl(lot_code)
        if not pnl:
            return {"error": f"Lot {lot_code} not found or no sales yet"}
        return {
            "lot_code": pnl.lot_code,
            "vegetable_name": pnl.vegetable_name,
            "farmer_name": pnl.farmer_name,
            "total_cost": float(pnl.total_cost.total),
            "cost_per_kg": float(pnl.cost_per_kg),
            "total_revenue": float(pnl.total_revenue),
            "revenue_per_kg": float(pnl.revenue_per_kg),
            "sold_weight_kg": float(pnl.sold_weight_kg),
            "waste_kg": float(pnl.waste_kg),
            "waste_pct": float(pnl.waste_pct),
            "gross_profit": float(pnl.gross_profit),
            "gross_margin_pct": float(pnl.gross_margin_pct),
            "net_profit": float(pnl.net_profit),
            "net_margin_pct": float(pnl.net_margin_pct),
            "profit_per_kg": float(pnl.profit_per_kg),
        }
    finally:
        db.close()


@register_tool(
    name="list_lots",
    description="List lots with optional filters. Returns summary info for each lot. Use this when the user asks about multiple lots or wants a general overview.",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status: Registered, Skidded, Sorted, Tested, Graded, InInventory, OnSale, PartiallySold, FullySold, Closed"
            },
            "vegetable_id": {
                "type": "integer",
                "description": "Filter by vegetable ID (1-16)"
            },
            "limit": {
                "type": "integer",
                "description": "Max number of lots to return (default 20)"
            }
        },
        "required": []
    }
)
def list_lots(
    status: str | None = None,
    vegetable_id: int | None = None,
    limit: int = 20,
) -> dict:
    """List lots with filters."""
    from app.services.lot_service import LotService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = LotService(db)
        lots, total = service.list(
            limit=limit,
            status=status,
            vegetable_id=vegetable_id,
        )
        return {
            "total_matching": total,
            "returned": len(lots),
            "lots": [
                {
                    "lot_code": lot.lot_code,
                    "status": lot.status,
                    "weight_kg": float(lot.total_weight_kg),
                    "acquired_at": lot.acquired_at.isoformat(),
                }
                for lot in lots
            ]
        }
    finally:
        db.close()


# ============================================
# FARMER TOOLS
# ============================================

@register_tool(
    name="get_farmer_performance",
    description="Get performance metrics for a farmer including lots supplied, total purchase value, on-time delivery rate, fill rate, and grade distribution. Use this to evaluate supplier quality.",
    parameters={
        "type": "object",
        "properties": {
            "farmer_id": {
                "type": "integer",
                "description": "The farmer ID (1-12)"
            }
        },
        "required": ["farmer_id"]
    }
)
def get_farmer_performance(farmer_id: int) -> dict:
    """Get farmer performance metrics."""
    from app.services.farmer_service import FarmerService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = FarmerService(db)
        perf = service.get_performance(farmer_id)
        if not perf:
            return {"error": f"Farmer {farmer_id} not found"}
        return {
            "farmer_id": perf.farmer_id,
            "farmer_name": perf.farmer_name,
            "total_lots": perf.total_lots,
            "total_purchase_value": float(perf.total_purchase_value),
            "grade_distribution": perf.average_grade_distribution,
            "on_time_delivery_rate": perf.on_time_delivery_rate,
            "fill_rate": perf.fill_rate,
        }
    finally:
        db.close()


# ============================================
# INVENTORY TOOLS
# ============================================

@register_tool(
    name="get_inventory_value",
    description="Get the current total inventory value (at cost) and count of available items. Use this for 'how much inventory do we have?' questions.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_inventory_value() -> dict:
    """Get total inventory value."""
    from app.services.inventory_service import InventoryService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = InventoryService(db)
        value = service.get_total_value()
        items, total = service.list(is_available=True)
        return {
            "total_value": float(value),
            "available_items": total,
        }
    finally:
        db.close()


@register_tool(
    name="get_expiring_inventory",
    description="Get inventory items expiring within N days. Use for 'what's about to spoil?' questions.",
    parameters={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days to look ahead (default 7)"
            }
        },
        "required": []
    }
)
def get_expiring_inventory(days: int = 7) -> dict:
    """Get items expiring soon."""
    from app.services.inventory_service import InventoryService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = InventoryService(db)
        items = service.get_expiring_soon(days=days)
        return {
            "days": days,
            "count": len(items),
            "items": [
                {
                    "id": inv.id,
                    "location_id": inv.location_id,
                    "quantity_kg": float(inv.quantity_kg) if inv.quantity_kg else None,
                    "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
                }
                for inv in items
            ]
        }
    finally:
        db.close()


# ============================================
# DASHBOARD TOOLS
# ============================================

@register_tool(
    name="get_dashboard_summary",
    description="Get the complete dashboard data: KPIs (active lots, MTD revenue, MTD profit, inventory value, overdue POs), revenue trend, grade distribution, and top suppliers. Use for general 'how is the business doing?' questions.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_dashboard_summary() -> dict:
    """Get dashboard KPIs and charts."""
    from app.services.dashboard_service import DashboardService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        service = DashboardService(db)
        dashboard = service.get_dashboard()
        return {
            "kpis": {
                "active_lots": dashboard.kpis.active_lots,
                "total_lots": dashboard.kpis.total_lots,
                "open_purchase_orders": dashboard.kpis.open_purchase_orders,
                "overdue_purchase_orders": dashboard.kpis.overdue_purchase_orders,
                "total_revenue_mtd": float(dashboard.kpis.total_revenue_mtd),
                "total_profit_mtd": float(dashboard.kpis.total_profit_mtd),
                "profit_margin_mtd": float(dashboard.kpis.profit_margin_mtd),
                "average_grade_score": float(dashboard.kpis.average_grade_score),
                "waste_percentage_mtd": float(dashboard.kpis.waste_percentage_mtd),
                "inventory_value": float(dashboard.kpis.inventory_value),
                "low_stock_items": dashboard.kpis.low_stock_items,
            },
            "alerts_count": len(dashboard.alerts),
        }
    finally:
        db.close()


# ============================================
# TOOL DISCOVERY
# ============================================

def get_tools_for_ai() -> list[dict]:
    """Return all registered tools in the format the AI expects."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
        }
        for tool in TOOL_REGISTRY.values()
    ]


def call_tool(name: str, arguments: dict) -> Any:
    """Call a tool by name with the given arguments."""
    if name not in TOOL_REGISTRY:
        return {"error": f"Tool '{name}' not found"}
    tool = TOOL_REGISTRY[name]
    try:
        return tool.function(**arguments)
    except Exception as e:
        return {"error": str(e)}
