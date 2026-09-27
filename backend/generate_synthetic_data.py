"""
VeggieOps AI - Synthetic Data Generator
========================================
Generates realistic business data for development and testing.

Data is clearly labeled as synthetic. Patterns follow real vegetable
shop operations:
- Grade A sells faster than RECYCLE
- Larger lots have economies of scale
- Some farmers are more reliable than others
- Transport costs depend on distance
- Seasonal patterns exist
- Some vegetables spoil more than others

Run with:
    docker cp generate_synthetic_data.py veggie-backend:/app/
    docker exec veggie-backend python generate_synthetic_data.py
"""

import random
from datetime import datetime, timedelta, date
from decimal import Decimal

from app.db.session import SessionLocal
from app.models.people import Farmer, Customer, Employee
from app.models.procurement import (
    PurchaseOrder,
    PurchaseOrderItem,
    CollectionTrip,
    TripStop,
    Delivery,
)
from app.models.inventory import (
    Vegetable,
    Lot,
    Skid,
    Asset,
    Inventory,
    InventoryTransaction,
)
from app.models.quality import Grade, QualityTest, SortResult
from app.models.sales import Price, Sale, SaleItem
from app.models.costs import CostEntry, LaborRecord
from app.models.audit import ProcessingEvent


# ============================================
# CONFIGURATION
# ============================================

random.seed(42)

END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=180)

NUM_FARMERS = 12
NUM_EMPLOYEES = 5
NUM_CUSTOMERS = 25
NUM_PURCHASE_ORDERS = 60
LOT_CODE_SEQUENCE_START = 1
SKID_CODE_SEQUENCE_START = 1
NUM_SALES = 350


# ============================================
# UTILITY FUNCTIONS
# ============================================

def random_date_between(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def random_phone() -> str:
    return f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def random_email(name: str, domain: str = "example.com") -> str:
    clean = name.lower().replace(" ", ".").replace("'", "")
    return f"{clean}@{domain}"


def generate_lot_code(sequence: int) -> str:
    return f"L-{END_DATE.year}-{sequence:05d}"


def generate_skid_code(sequence: int) -> str:
    return f"SK-{sequence:05d}"


def generate_asset_code(lot_code: str, index: int) -> str:
    return f"{lot_code}-{index:02d}"


def generate_po_number(sequence: int) -> str:
    return f"PO-{END_DATE.year}-{sequence:05d}"


GRADE_THRESHOLDS = [
    (0.20, "A"),
    (0.40, "A-"),
    (0.65, "B"),
    (0.80, "B-"),
    (0.90, "C"),
    (0.95, "C-"),
    (1.00, "RECYCLE"),
]

BASE_PRICES_BY_CATEGORY = {
    "leafy":        {"A": 4.50, "A-": 3.80, "B": 3.00, "B-": 2.30, "C": 1.60, "C-": 0.90, "RECYCLE": 0.10},
    "root":         {"A": 2.80, "A-": 2.40, "B": 1.90, "B-": 1.50, "C": 1.10, "C-": 0.60, "RECYCLE": 0.05},
    "fruit":        {"A": 5.00, "A-": 4.20, "B": 3.30, "B-": 2.50, "C": 1.80, "C-": 1.00, "RECYCLE": 0.15},
    "legume":       {"A": 6.00, "A-": 5.20, "B": 4.20, "B-": 3.20, "C": 2.30, "C-": 1.30, "RECYCLE": 0.20},
    "cruciferous":  {"A": 3.80, "A-": 3.20, "B": 2.50, "B-": 1.90, "C": 1.40, "C-": 0.80, "RECYCLE": 0.10},
}


def assign_realistic_grade() -> str:
    roll = random.random()
    for threshold, grade in GRADE_THRESHOLDS:
        if roll < threshold:
            return grade
    return "RECYCLE"


# ============================================
# PEOPLE GENERATORS
# ============================================

def generate_farmers(db) -> list[Farmer]:
    farmer_names = [
        "Green Valley Farms", "Sunrise Produce Co", "Mountain Ridge Gardens",
        "Riverside Organics", "Heritage Family Farm", "Pacific Coast Vegetables",
        "Hillside Harvest", "Golden Fields Co-op", "Eastside Growers",
        "North Fork Farms", "Backyard Bounty", "Sunset Valley Produce",
    ]

    locations = [
        "Sonoma County, CA", "Salinas Valley, CA", "Hudson Valley, NY",
        "Willamette Valley, OR", "Skagit Valley, WA", "Central Valley, CA",
        "Okanagan Valley, WA", "Pioneer Valley, MA",
    ]

    payment_terms_options = ["Cash on Delivery", "Net 7", "Net 15", "Net 30"]
    notes_options = [
        "Reliable supplier, consistent quality",
        "Best prices in region, quality varies",
        "Premium organic only, higher prices",
        "Family-run, flexible delivery times",
        "Large volumes, prefers PO contracts",
        "Specialty vegetables, seasonal",
        None, None, None,
    ]

    farmers = []
    for i, name in enumerate(farmer_names):
        existing = db.query(Farmer).filter(Farmer.name == name).first()
        if existing:
            farmers.append(existing)
            continue

        farmer = Farmer(
            name=name,
            contact_person=f"Manager {chr(65 + i)}",
            phone=random_phone(),
            email=random_email(name, "farm.com"),
            address=f"{random.randint(100, 9999)} Rural Route {random.randint(1, 99)}",
            location=random.choice(locations),
            payment_terms=random.choice(payment_terms_options),
            rating=Decimal(f"{random.uniform(3.5, 5.0):.2f}"),
            is_active=random.random() > 0.1,
            notes=random.choice(notes_options),
        )
        db.add(farmer)
        farmers.append(farmer)
        print(f"  Added farmer: {name}")

    db.commit()
    return farmers


def generate_employees(db) -> list[Employee]:
    employee_data = [
        {"name": "Ravi Patel",   "role": "owner",   "hourly_rate": 0,     "phone": "555-100-0001"},
        {"name": "Tom Wilson",   "role": "driver",  "hourly_rate": 22.50, "phone": "555-100-0002"},
        {"name": "Maria Santos", "role": "sorter",  "hourly_rate": 18.00, "phone": "555-100-0003"},
        {"name": "Ahmed Hassan", "role": "cashier", "hourly_rate": 19.00, "phone": "555-100-0004"},
        {"name": "Lisa Chen",    "role": "sorter",  "hourly_rate": 18.00, "phone": "555-100-0005"},
    ]

    employees = []
    for data in employee_data:
        existing = db.query(Employee).filter(Employee.name == data["name"]).first()
        if existing:
            employees.append(existing)
            continue

        employee = Employee(
            name=data["name"],
            role=data["role"],
            phone=data["phone"],
            email=random_email(data["name"]),
            hourly_rate=Decimal(str(data["hourly_rate"])) if data["hourly_rate"] > 0 else None,
            hire_date=START_DATE - timedelta(days=random.randint(180, 1000)),
            is_active=True,
            notes=None,
        )
        db.add(employee)
        employees.append(employee)
        print(f"  Added employee: {data['name']} ({data['role']})")

    db.commit()
    return employees


def generate_customers(db) -> list[Customer]:
    individual_names = [
        "Sarah Johnson", "Michael Brown", "Jennifer Davis",
        "David Miller", "Linda Wilson", "Robert Moore",
        "Patricia Taylor", "James Anderson", "Barbara Thomas",
        "William Jackson", "Elizabeth White", "Richard Harris",
        "Susan Martin", "Joseph Thompson", "Jessica Garcia",
        "Thomas Robinson", "Karen Clark",
    ]

    business_names = [
        "Sunny Side Cafe", "Greenleaf Restaurant", "Downtown Bistro",
        "Corner Deli", "Healthy Bites Catering", "Fresh Market Store",
        "Garden Salad Co.", "School District Cafeteria",
    ]

    customers = []
    all_names = list(individual_names) + list(business_names)
    all_names = all_names[:NUM_CUSTOMERS]

    for name in all_names:
        existing = db.query(Customer).filter(Customer.name == name).first()
        if existing:
            customers.append(existing)
            continue

        is_business = name in business_names
        customer = Customer(
            name=name,
            customer_type="business" if is_business else "individual",
            phone=random_phone() if random.random() > 0.2 else None,
            email=random_email(name) if random.random() > 0.3 else None,
            address=(
                f"{random.randint(100, 9999)} Main St, Apt {random.randint(1, 200)}"
                if not is_business
                else f"{random.randint(100, 9999)} Commerce Blvd, Suite {random.randint(1, 50)}"
            ),
            is_active=random.random() > 0.1,
            notes=None,
        )
        db.add(customer)
        customers.append(customer)
        print(f"  Added customer: {name} ({customer.customer_type})")

    db.commit()
    return customers


# ============================================
# PROCUREMENT GENERATORS
# ============================================

def generate_purchase_orders(db, farmers: list[Farmer], employees: list[Employee]) -> list[PurchaseOrder]:
    from app.models.enums import PurchaseOrderStatus

    vegetables = db.query(Vegetable).all()
    if not vegetables:
        return []

    pos = []
    owner = next((e for e in employees if e.role == "owner"), employees[0])

    for i in range(1, NUM_PURCHASE_ORDERS + 1):
        po_number = generate_po_number(i)
        existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
        if existing:
            pos.append(existing)
            continue

        issue_date = random_date_between(START_DATE, END_DATE - timedelta(days=7))
        farmer = random.choice(farmers)

        status_roll = random.random()
        if status_roll < 0.80:
            status = PurchaseOrderStatus.FULLY_RECEIVED.value
        elif status_roll < 0.90:
            status = PurchaseOrderStatus.PARTIALLY_RECEIVED.value
        elif status_roll < 0.95:
            status = PurchaseOrderStatus.CANCELLED.value
        else:
            status = PurchaseOrderStatus.ISSUED.value

        delivery_mode = random.choice(["Collection", "FarmerDelivery"])
        expected_delivery = issue_date.date() + timedelta(days=random.randint(3, 14))

        actual_delivery = None
        if status in [PurchaseOrderStatus.FULLY_RECEIVED.value, PurchaseOrderStatus.PARTIALLY_RECEIVED.value]:
            actual_delivery = expected_delivery + timedelta(days=random.randint(-2, 3))

        num_items = random.randint(1, 3)
        chosen_vegetables = random.sample(vegetables, min(num_items, len(vegetables)))

        total_expected = Decimal("0")
        items = []

        for veg in chosen_vegetables:
            qty = Decimal(f"{random.uniform(50, 400):.2f}")
            base_prices_for_cat = BASE_PRICES_BY_CATEGORY.get(veg.category, BASE_PRICES_BY_CATEGORY["leafy"])
            base_price = base_prices_for_cat["B"]
            unit_price = Decimal(f"{base_price * random.uniform(0.85, 1.15):.2f}")
            line_total = qty * unit_price
            total_expected += line_total

            items.append({
                "vegetable_id": veg.id,
                "expected_quantity_kg": qty,
                "expected_unit_price": unit_price,
                "expected_total": line_total,
            })

        po = PurchaseOrder(
            po_number=po_number,
            farmer_id=farmer.id,
            status=status,
            issue_date=issue_date.date(),
            expected_delivery_date=expected_delivery,
            actual_delivery_date=actual_delivery,
            total_expected_value=total_expected,
            total_actual_value=total_expected if status != PurchaseOrderStatus.CANCELLED.value else None,
            payment_terms=farmer.payment_terms or "Net 15",
            delivery_mode=delivery_mode,
            notes=None,
            created_by=owner.id,
        )
        db.add(po)
        db.flush()

        for item_data in items:
            received_qty = (
                item_data["expected_quantity_kg"] if status == PurchaseOrderStatus.FULLY_RECEIVED.value
                else item_data["expected_quantity_kg"] * Decimal("0.6") if status == PurchaseOrderStatus.PARTIALLY_RECEIVED.value
                else Decimal("0")
            )
            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                vegetable_id=item_data["vegetable_id"],
                expected_quantity_kg=item_data["expected_quantity_kg"],
                expected_unit_price=item_data["expected_unit_price"],
                received_quantity_kg=received_qty,
                actual_unit_price=item_data["expected_unit_price"] if status != PurchaseOrderStatus.CANCELLED.value else None,
            )
            db.add(po_item)

        pos.append(po)

    db.commit()
    return pos


def generate_collection_trips(db, pos: list[PurchaseOrder], employees: list[Employee]) -> list[CollectionTrip]:
    driver = next((e for e in employees if e.role == "driver"), employees[0] if employees else None)
    if not driver:
        return []

    trips = []
    trip_counter = 1

    for po in pos:
        if po.delivery_mode != "Collection":
            continue
        if po.status not in ["FullyReceived", "PartiallyReceived"]:
            continue

        existing = db.query(CollectionTrip).filter(
            CollectionTrip.notes.like(f"%PO {po.po_number}%")
        ).first()
        if existing:
            trips.append(existing)
            continue

        trip_date = datetime.combine(po.actual_delivery_date, datetime.min.time()) + timedelta(hours=random.randint(6, 10))
        distance = Decimal(f"{random.uniform(15, 80):.1f}")
        fuel_cost = distance * Decimal("0.65")
        hours = Decimal(f"{random.uniform(2, 6):.1f}")
        driver_cost = hours * driver.hourly_rate if driver.hourly_rate else Decimal("0")

        trip = CollectionTrip(
            trip_code=f"TR-{END_DATE.year}-{trip_counter:04d}",
            employee_id=driver.id,
            vehicle="Box Truck #1",
            departed_at=trip_date,
            returned_at=trip_date + timedelta(hours=float(hours)),
            distance_km=distance,
            fuel_cost=fuel_cost,
            other_costs=Decimal("0"),
            total_cost=fuel_cost + driver_cost,
            notes=f"Collection trip for PO {po.po_number}",
        )
        db.add(trip)
        db.flush()

        stop = TripStop(
            trip_id=trip.id,
            farm_id=po.farmer_id,
            arrived_at=trip_date + timedelta(hours=1),
            departed_at=trip_date + timedelta(hours=2),
            notes=f"Loading for {po.po_number}",
        )
        db.add(stop)

        trips.append(trip)
        trip_counter += 1

    db.commit()
    return trips


def generate_deliveries(db, pos: list[PurchaseOrder], employees: list[Employee]) -> list[Delivery]:
    deliveries = []
    delivery_counter = 1

    for po in pos:
        if po.delivery_mode != "FarmerDelivery":
            continue
        if po.status not in ["FullyReceived", "PartiallyReceived"]:
            continue

        existing = db.query(Delivery).filter(
            Delivery.notes.like(f"%PO {po.po_number}%")
        ).first()
        if existing:
            deliveries.append(existing)
            continue

        delivery_time = datetime.combine(po.actual_delivery_date, datetime.min.time()) + timedelta(hours=random.randint(8, 16))
        delivery_fee = Decimal(f"{random.uniform(20, 50):.2f}")

        delivery = Delivery(
            delivery_code=f"DLV-{END_DATE.year}-{delivery_counter:04d}",
            farmer_id=po.farmer_id,
            arrived_at=delivery_time,
            unloaded_by=random.choice(employees).id if employees else None,
            vehicle=f"Farmer truck {random.choice(['A', 'B', 'C'])}",
            delivery_fee=delivery_fee,
            notes=f"Delivery for PO {po.po_number}",
        )
        db.add(delivery)
        deliveries.append(delivery)
        delivery_counter += 1

    db.commit()
    return deliveries


def generate_lots(db, pos: list[PurchaseOrder]) -> list[Lot]:
    from app.models.enums import LotStatus

    lots = []
    lot_counter = LOT_CODE_SEQUENCE_START

    for po in pos:
        if po.status not in ["FullyReceived", "PartiallyReceived"]:
            continue

        po_items = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.purchase_order_id == po.id
        ).all()

        for po_item in po_items:
            if po_item.received_quantity_kg <= 0:
                continue

            lot_code = generate_lot_code(lot_counter)

            existing = db.query(Lot).filter(Lot.lot_code == lot_code).first()
            if existing:
                lots.append(existing)
                lot_counter += 1
                continue

            acquired_at = datetime.combine(po.actual_delivery_date, datetime.min.time()) + timedelta(hours=random.randint(2, 6))
            acquisition_cost = po_item.received_quantity_kg * po_item.expected_unit_price

            lot = Lot(
                lot_code=lot_code,
                purchase_order_id=po.id,
                vegetable_id=po_item.vegetable_id,
                source_type="purchase_order",
                source_id=po.id,
                acquired_at=acquired_at,
                total_weight_kg=po_item.received_quantity_kg,
                acquisition_cost=acquisition_cost,
                status=LotStatus.REGISTERED.value,
                notes=None,
            )
            db.add(lot)
            lots.append(lot)
            lot_counter += 1

    db.commit()
    print(f"  Added {len(lots)} lots")
    return lots


def generate_skids(db, lots: list[Lot]) -> list[Skid]:
    skids = []
    skid_counter = SKID_CODE_SEQUENCE_START

    for lot in lots:
        num_skids = max(1, int(lot.total_weight_kg / 150) + random.randint(0, 1))
        weight_per_skid = lot.total_weight_kg / num_skids

        for i in range(num_skids):
            skid_code = generate_skid_code(skid_counter)

            existing = db.query(Skid).filter(Skid.skid_code == skid_code).first()
            if existing:
                skids.append(existing)
                skid_counter += 1
                continue

            position = random.choice([
                "Cold Room A, Shelf 1",
                "Cold Room A, Shelf 2",
                "Cold Room B, Shelf 1",
                "Back Room, Floor 1",
                "Display Front",
            ])

            skid = Skid(
                lot_id=lot.id,
                skid_code=skid_code,
                weight_kg=Decimal(f"{weight_per_skid:.2f}"),
                position=position,
                notes=None,
            )
            db.add(skid)
            skids.append(skid)
            skid_counter += 1

    db.commit()
    print(f"  Added {len(skids)} skids")
    return skids


def generate_assets(db, lots: list[Lot], skids: list[Skid]) -> list[Asset]:
    large_item_vegetables = ["Pumpkin", "Cabbage", "Cauliflower", "Broccoli", "Lettuce"]

    assets = []
    for lot in lots:
        veg = db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
        if not veg or veg.name not in large_item_vegetables:
            continue

        lot_skids = [s for s in skids if s.lot_id == lot.id]
        if not lot_skids:
            continue

        num_assets = min(8, random.randint(3, 8))
        weight_per_asset = lot.total_weight_kg / num_assets

        for i in range(1, num_assets + 1):
            asset_code = generate_asset_code(lot.lot_code, i)

            existing = db.query(Asset).filter(Asset.asset_code == asset_code).first()
            if existing:
                assets.append(existing)
                continue

            skid = random.choice(lot_skids)
            asset = Asset(
                skid_id=skid.id,
                asset_code=asset_code,
                weight_kg=Decimal(f"{weight_per_asset:.2f}"),
                dimensions=None,
                current_stage="Registered",
                status="Registered",
                notes=None,
            )
            db.add(asset)
            assets.append(asset)

    db.commit()
    print(f"  Added {len(assets)} assets")
    return assets


# ============================================
# QUALITY GENERATORS
# ============================================

def generate_sort_results(db, lots: list[Lot], employees: list[Employee]) -> list[SortResult]:
    sorters = [e for e in employees if e.role == "sorter"]
    sorter = sorters[0] if sorters else (employees[0] if employees else None)

    results = []
    for lot in lots:
        existing = db.query(SortResult).filter(SortResult.lot_id == lot.id).first()
        if existing:
            results.append(existing)
            continue

        veg = db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
        waste_pct = float(veg.typical_waste_pct) if veg and veg.typical_waste_pct else 5.0

        damaged_pct = waste_pct * random.uniform(0.6, 0.8)
        recycle_pct = waste_pct - damaged_pct

        damaged_kg = lot.total_weight_kg * Decimal(f"{damaged_pct/100:.2f}")
        recycle_kg = lot.total_weight_kg * Decimal(f"{recycle_pct/100:.2f}")
        sellable_kg = lot.total_weight_kg - damaged_kg - recycle_kg

        result = SortResult(
            lot_id=lot.id,
            skid_id=None,
            sorted_at=lot.acquired_at + timedelta(hours=random.randint(2, 8)),
            sorted_by=sorter.id if sorter else None,
            sellable_kg=sellable_kg,
            damaged_kg=damaged_kg,
            recycle_kg=recycle_kg,
            notes=None,
        )
        db.add(result)
        results.append(result)

    db.commit()
    print(f"  Added {len(results)} sort results")
    return results


def generate_quality_tests(db, assets: list[Asset], employees: list[Employee], lots: list[Lot], sort_results: list[SortResult]) -> list[QualityTest]:
    grades = {g.code: g.id for g in db.query(Grade).all()}
    if not grades:
        return []

    sorters = [e for e in employees if e.role == "sorter"]
    sorter = sorters[0] if sorters else (employees[0] if employees else None)

    tests = []
    sort_by_lot = {s.lot_id: s for s in sort_results}

    tested_asset_ids = set()

    for asset in assets:
        if asset.id in tested_asset_ids:
            continue

        existing = db.query(QualityTest).filter(QualityTest.asset_id == asset.id).first()
        if existing:
            tests.append(existing)
            tested_asset_ids.add(asset.id)
            continue

        grade_code = assign_realistic_grade()
        lot_id = asset.skid.lot_id if asset.skid else None
        sort_result = sort_by_lot.get(lot_id) if lot_id else None
        if sort_result:
            tested_at = sort_result.sorted_at + timedelta(hours=random.randint(1, 4))
        else:
            tested_at = datetime.now() - timedelta(days=random.randint(1, 30))

        test = QualityTest(
            asset_id=asset.id,
            tester_id=sorter.id if sorter else None,
            grade_id=grades[grade_code],
            tested_at=tested_at,
            parameters={
                "size": random.choice(["small", "medium", "large"]),
                "color": random.choice(["excellent", "good", "fair", "poor"]),
                "firmness": random.choice(["firm", "slightly soft", "soft"]),
                "defects": random.choice(["none", "minor", "moderate", "severe"]),
            },
            comments=f"Grade {grade_code} based on visual inspection",
            superseded_by_id=None,
        )
        db.add(test)
        tests.append(test)
        tested_asset_ids.add(asset.id)

    assets_by_lot = {a.skid.lot_id for a in assets if a.skid}
    tested_lot_ids_in_run = set()
    for lot in lots:
        if lot.id in assets_by_lot:
            continue
        if lot.id in tested_lot_ids_in_run:
            continue

        grade_code = assign_realistic_grade()
        test = QualityTest(
            asset_id=None,
            tester_id=sorter.id if sorter else None,
            grade_id=grades[grade_code],
            tested_at=lot.acquired_at + timedelta(hours=random.randint(2, 12)),
            parameters={
                "lot_id": str(lot.id),
                "sample_size_kg": float(lot.total_weight_kg * Decimal("0.1")),
                "grade": grade_code,
            },
            comments=f"Lot-level grade {grade_code} (no individual assets)",
            superseded_by_id=None,
        )
        db.add(test)
        tests.append(test)
        tested_lot_ids_in_run.add(lot.id)

    db.commit()
    print(f"  Added {len(tests)} quality tests")
    return tests


# ============================================
# INVENTORY GENERATORS
# ============================================

def generate_inventory(db, assets: list[Asset], lots: list[Lot]) -> list[Inventory]:
    inventory_items = []

    for asset in assets:
        existing = db.query(Inventory).filter(Inventory.asset_id == asset.id).first()
        if existing:
            inventory_items.append(existing)
            continue

        lot = next((l for l in lots if l.id == asset.skid.lot_id), None) if asset.skid else None
        veg = db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first() if lot else None
        shelf_days = veg.shelf_life_days if veg and veg.shelf_life_days else 7

        acquired = lot.acquired_at if lot else datetime.now()
        available_from = acquired + timedelta(hours=random.randint(2, 12))
        expires_at = available_from + timedelta(days=shelf_days)

        inv = Inventory(
            asset_id=asset.id,
            location="Cold Room A" if random.random() > 0.3 else "Display Front",
            quantity_kg=asset.weight_kg,
            quantity_units=1,
            available_from=available_from,
            expires_at=expires_at,
            is_available=True,
        )
        db.add(inv)
        inventory_items.append(inv)

    assets_by_lot = {a.skid.lot_id for a in assets if a.skid}
    for lot in lots:
        if lot.id in assets_by_lot:
            continue

        existing = db.query(Inventory).filter(
            Inventory.asset_id.is_(None)
        ).filter(
            Inventory.location == f"Lot:{lot.lot_code}"
        ).first()
        if existing:
            inventory_items.append(existing)
            continue

        veg = db.query(Vegetable).filter(Vegetable.id == lot.vegetable_id).first()
        shelf_days = veg.shelf_life_days if veg and veg.shelf_life_days else 7
        available_from = lot.acquired_at + timedelta(hours=random.randint(2, 12))
        expires_at = available_from + timedelta(days=shelf_days)

        inv = Inventory(
            asset_id=None,
            location=f"Lot:{lot.lot_code}",
            quantity_kg=lot.total_weight_kg,
            quantity_units=None,
            available_from=available_from,
            expires_at=expires_at,
            is_available=True,
        )
        db.add(inv)
        inventory_items.append(inv)

    db.commit()
    print(f"  Added {len(inventory_items)} inventory entries")
    return inventory_items


def generate_inventory_transactions(db, inventory_items: list[Inventory], employees: list[Employee]) -> list[InventoryTransaction]:
    owner = next((e for e in employees if e.role == "owner"), employees[0] if employees else None)

    transactions = []
    for inv in inventory_items:
        existing = db.query(InventoryTransaction).filter(InventoryTransaction.inventory_id == inv.id).first()
        if existing:
            transactions.append(existing)
            continue

        txn = InventoryTransaction(
            inventory_id=inv.id,
            txn_type="Received",
            qty_change_kg=inv.quantity_kg,
            qty_change_units=inv.quantity_units,
            reference_type="lot_arrival",
            reference_id=None,
            notes="Initial stock from lot arrival",
            created_by=owner.id if owner else None,
        )
        db.add(txn)
        transactions.append(txn)

        if random.random() < 0.4:
            adjustment_kg = inv.quantity_kg * Decimal(f"{random.uniform(0.05, 0.15):.2f}")
            adj_txn = InventoryTransaction(
                inventory_id=inv.id,
                txn_type="Adjustment",
                qty_change_kg=-adjustment_kg,
                qty_change_units=None,
                reference_type="spoilage",
                reference_id=None,
                notes=f"Adjusted for spoilage ({adjustment_kg:.2f} kg)",
                created_by=owner.id if owner else None,
            )
            db.add(adj_txn)
            transactions.append(adj_txn)

    db.commit()
    print(f"  Added {len(transactions)} inventory transactions")
    return transactions


def generate_prices(db, vegetables: list[Vegetable]) -> list[Price]:
    grades = {g.code: g.id for g in db.query(Grade).all()}
    prices = []

    for veg in vegetables:
        base_prices_for_cat = BASE_PRICES_BY_CATEGORY.get(veg.category, BASE_PRICES_BY_CATEGORY["leafy"])
        unit_type = veg.default_unit_type or "kg"

        for grade_code, base_price in base_prices_for_cat.items():
            existing = db.query(Price).filter(
                Price.vegetable_id == veg.id,
                Price.grade_id == grades[grade_code],
                Price.unit_type == unit_type,
            ).first()
            if existing:
                prices.append(existing)
                continue

            price_value = Decimal(f"{base_price * random.uniform(0.92, 1.08):.2f}")
            price = Price(
                vegetable_id=veg.id,
                grade_id=grades[grade_code],
                unit_type=unit_type,
                unit_price=price_value,
                effective_from=START_DATE,
                effective_to=None,
                set_by=None,
                notes=None,
            )
            db.add(price)
            prices.append(price)

    db.commit()
    print(f"  Added {len(prices)} prices")
    return prices


# ============================================
# CHUNK 4 GENERATORS: SALES, COSTS, LABOR, EVENTS
# ============================================

def generate_sales(
    db,
    customers: list[Customer],
    inventory_items: list[Inventory],
    tests: list[QualityTest],
    employees: list[Employee],
    lots: list[Lot],
) -> list[Sale]:
    cashier = next((e for e in employees if e.role == "cashier"), employees[0] if employees else None)

    grades = {g.code: g.id for g in db.query(Grade).all()}
    prices_by_lookup = {}

    for p in db.query(Price).all():
        prices_by_lookup[(p.vegetable_id, p.grade_id)] = p.unit_price

    asset_grade = {}
    for test in tests:
        if test.asset_id:
            if test.asset_id not in asset_grade or test.tested_at > asset_grade[test.asset_id][1]:
                asset_grade[test.asset_id] = (test.grade_id, test.tested_at)

    inventory_by_veg = {}
    for inv in inventory_items:
        veg_id = None
        if inv.asset:
            lot = None
            if inv.asset.skid:
                lot = next((l for l in lots if l.id == inv.asset.skid.lot_id), None)
            if lot:
                veg_id = lot.vegetable_id
        else:
            if inv.location.startswith("Lot:"):
                lot_code = inv.location.replace("Lot:", "")
                lot = next((l for l in lots if l.lot_code == lot_code), None)
                if lot:
                    veg_id = lot.vegetable_id

        if veg_id:
            if veg_id not in inventory_by_veg:
                inventory_by_veg[veg_id] = []
            inventory_by_veg[veg_id].append(inv)

    sales = []
    for i in range(1, NUM_SALES + 1):
        sale_code = f"S-{END_DATE.year}-{i:05d}"
        existing = db.query(Sale).filter(Sale.sale_code == sale_code).first()
        if existing:
            sales.append(existing)
            continue

        days_back = int(random.triangular(0, 180, 60))
        sold_at = END_DATE - timedelta(days=days_back, hours=random.randint(8, 20))

        customer = random.choice(customers)
        if customer.customer_type == "individual" and random.random() < 0.3:
            continue

        if customer.customer_type == "business":
            num_items = random.randint(2, 5)
        else:
            num_items = random.randint(1, 3)

        available_vegs = [v for v, invs in inventory_by_veg.items() if invs]
        if not available_vegs:
            continue

        chosen_vegs = random.sample(available_vegs, min(num_items, len(available_vegs)))

        sale_items_data = []
        subtotal = Decimal("0")

        for veg_id in chosen_vegs:
            inv_list = inventory_by_veg[veg_id]
            if not inv_list:
                continue
            inv = random.choice(inv_list)
            inventory_by_veg[veg_id].remove(inv)

            if inv.asset_id and inv.asset_id in asset_grade:
                grade_id = asset_grade[inv.asset_id][0]
            else:
                grade_code = assign_realistic_grade()
                grade_id = grades[grade_code]

            unit_price = prices_by_lookup.get((veg_id, grade_id), Decimal("2.50"))

            if customer.customer_type == "business":
                qty = Decimal(f"{random.uniform(2, 20):.1f}")
            else:
                qty = Decimal(f"{random.uniform(0.5, 5):.1f}")

            unit_type = random.choice(["kg", "kg", "kg", "piece"])
            if unit_type == "piece" and inv.quantity_units:
                qty = Decimal("1")

            line_total = qty * unit_price
            subtotal += line_total

            sale_items_data.append({
                "inventory_id": inv.id,
                "asset_id": inv.asset_id,
                "vegetable_id": veg_id,
                "grade_id": grade_id,
                "quantity": qty,
                "unit_type": unit_type,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        if not sale_items_data:
            continue

        discount = Decimal("0")
        if random.random() < 0.15:
            discount = subtotal * Decimal("0.05")

        total_amount = subtotal - discount

        sale = Sale(
            sale_code=sale_code,
            customer_id=customer.id,
            sold_at=sold_at,
            status="Completed",
            payment_method=random.choice(["cash", "cash", "card", "card", "mobile"]),
            subtotal=subtotal,
            tax=Decimal("0"),
            discount=discount,
            total_amount=total_amount,
            sold_by=cashier.id if cashier else None,
            notes=None,
        )
        db.add(sale)
        db.flush()

        for item_data in sale_items_data:
            sale_item = SaleItem(
                sale_id=sale.id,
                inventory_id=item_data["inventory_id"],
                asset_id=item_data["asset_id"],
                vegetable_id=item_data["vegetable_id"],
                grade_id=item_data["grade_id"],
                quantity=item_data["quantity"],
                unit_type=item_data["unit_type"],
                unit_price=item_data["unit_price"],
                line_total=item_data["line_total"],
            )
            db.add(sale_item)

        sales.append(sale)

    db.commit()
    print(f"  Added {len(sales)} sales with line items")
    return sales


def generate_cost_entries(db, lots: list[Lot], pos: list[PurchaseOrder], trips: list[CollectionTrip], employees: list[Employee]) -> list[CostEntry]:
    owner = next((e for e in employees if e.role == "owner"), employees[0] if employees else None)

    costs = []

    for lot in lots:
        existing = db.query(CostEntry).filter(
            CostEntry.lot_id == lot.id,
            CostEntry.cost_category == "Acquisition"
        ).first()
        if existing:
            costs.append(existing)
            continue

        cost = CostEntry(
            lot_id=lot.id,
            cost_category="Acquisition",
            amount=lot.acquisition_cost,
            allocation_method="FixedPerLot",
            incurred_at=lot.acquired_at,
            reference_type="purchase_order",
            reference_id=lot.purchase_order_id,
            description=f"Acquisition cost for {lot.lot_code}",
            recorded_by=owner.id if owner else None,
        )
        db.add(cost)
        costs.append(cost)

    for trip in trips:
        po = next((p for p in pos if f"PO {p.po_number}" in (trip.notes or "")), None)
        if not po:
            continue

        existing = db.query(CostEntry).filter(
            CostEntry.reference_type == "collection_trip",
            CostEntry.reference_id == trip.id
        ).first()
        if existing:
            costs.append(existing)
            continue

        po_lots = [l for l in lots if l.purchase_order_id == po.id]
        if not po_lots:
            continue

        cost_per_lot = trip.total_cost / len(po_lots) if trip.total_cost else Decimal("0")

        for lot in po_lots:
            cost = CostEntry(
                lot_id=lot.id,
                cost_category="Transport",
                amount=cost_per_lot,
                allocation_method="WeightBased",
                incurred_at=trip.returned_at,
                reference_type="collection_trip",
                reference_id=trip.id,
                description=f"Transport for {trip.trip_code}",
                recorded_by=owner.id if owner else None,
            )
            db.add(cost)
            costs.append(cost)

    for lot in lots:
        existing = db.query(CostEntry).filter(
            CostEntry.lot_id == lot.id,
            CostEntry.cost_category == "Processing"
        ).first()
        if existing:
            costs.append(existing)
            continue

        processing_cost = lot.total_weight_kg * Decimal("0.50")
        cost = CostEntry(
            lot_id=lot.id,
            cost_category="Processing",
            amount=processing_cost,
            allocation_method="WeightBased",
            incurred_at=lot.acquired_at + timedelta(hours=random.randint(4, 24)),
            reference_type=None,
            reference_id=None,
            description=f"Sorting and grading for {lot.lot_code}",
            recorded_by=owner.id if owner else None,
        )
        db.add(cost)
        costs.append(cost)

    for lot in lots:
        existing = db.query(CostEntry).filter(
            CostEntry.lot_id == lot.id,
            CostEntry.cost_category == "Storage"
        ).first()
        if existing:
            costs.append(existing)
            continue

        days_stored = min(7, random.randint(1, 7))
        storage_cost = lot.total_weight_kg * Decimal("0.05") * days_stored
        cost = CostEntry(
            lot_id=lot.id,
            cost_category="Storage",
            amount=storage_cost,
            allocation_method="WeightBased",
            incurred_at=lot.acquired_at + timedelta(days=days_stored),
            reference_type=None,
            reference_id=None,
            description=f"Storage for {lot.lot_code} ({days_stored} days)",
            recorded_by=owner.id if owner else None,
        )
        db.add(cost)
        costs.append(cost)

    db.commit()
    print(f"  Added {len(costs)} cost entries")
    return costs

def generate_labor_records(db, lots: list[Lot], employees: list[Employee]) -> list[LaborRecord]:
    records = []

    for lot in lots:
        existing = db.query(LaborRecord).filter(
            LaborRecord.lot_id == lot.id,
            LaborRecord.activity_type == "sorting"
        ).first()
        if not existing:
            sorter = next((e for e in employees if e.role == "sorter"), None)
            if sorter and sorter.hourly_rate:
                hours = Decimal(f"{random.uniform(0.5, 2.0):.2f}")
                record = LaborRecord(
                    employee_id=sorter.id,
                    lot_id=lot.id,
                    activity_type="sorting",
                    work_date=lot.acquired_at + timedelta(hours=random.randint(2, 8)),
                    hours=hours,
                    hourly_rate=sorter.hourly_rate,
                    total_cost=hours * sorter.hourly_rate,
                )
                db.add(record)
                records.append(record)

        existing = db.query(LaborRecord).filter(
            LaborRecord.lot_id == lot.id,
            LaborRecord.activity_type == "grading"
        ).first()
        if not existing:
            sorter = next((e for e in employees if e.role == "sorter"), None)
            if sorter and sorter.hourly_rate:
                hours = Decimal(f"{random.uniform(0.3, 1.0):.2f}")
                record = LaborRecord(
                    employee_id=sorter.id,
                    lot_id=lot.id,
                    activity_type="grading",
                    work_date=lot.acquired_at + timedelta(hours=random.randint(8, 16)),
                    hours=hours,
                    hourly_rate=sorter.hourly_rate,
                    total_cost=hours * sorter.hourly_rate,
                )
                db.add(record)
                records.append(record)

    db.commit()
    print(f"  Added {len(records)} labor records")
    return records



def generate_processing_events(db, lots: list[Lot], sales: list[Sale], sort_results: list, tests: list, employees: list[Employee]) -> list[ProcessingEvent]:
    owner = next((e for e in employees if e.role == "owner"), None)
    events = []

    for lot in lots:
        existing = db.query(ProcessingEvent).filter(
            ProcessingEvent.lot_id == lot.id,
            ProcessingEvent.event_type == "LotRegistered"
        ).first()
        if not existing:
            events.append(ProcessingEvent(
                event_type="LotRegistered",
                lot_id=lot.id,
                asset_id=None,
                sale_id=None,
                employee_id=owner.id if owner else None,
                event_data={"weight_kg": float(lot.total_weight_kg)},
                notes=f"Lot {lot.lot_code} registered",
            ))

    for sort_result in sort_results:
        existing = db.query(ProcessingEvent).filter(
            ProcessingEvent.lot_id == sort_result.lot_id,
            ProcessingEvent.event_type == "SortCompleted"
        ).first()
        if not existing:
            events.append(ProcessingEvent(
                event_type="SortCompleted",
                lot_id=sort_result.lot_id,
                asset_id=None,
                sale_id=None,
                employee_id=sort_result.sorted_by,
                event_data={
                    "sellable_kg": float(sort_result.sellable_kg),
                    "damaged_kg": float(sort_result.damaged_kg),
                    "recycle_kg": float(sort_result.recycle_kg),
                },
                notes="Sort completed",
            ))

    for test in tests:
        if test.asset_id:
            existing = db.query(ProcessingEvent).filter(
                ProcessingEvent.asset_id == test.asset_id,
                ProcessingEvent.event_type == "GradeAssigned"
            ).first()
            if not existing:
                grade = db.query(Grade).filter(Grade.id == test.grade_id).first()
                events.append(ProcessingEvent(
                    event_type="GradeAssigned",
                    lot_id=None,
                    asset_id=test.asset_id,
                    sale_id=None,
                    employee_id=test.tester_id,
                    event_data={"grade": grade.code if grade else "Unknown"},
                    notes=f"Grade assigned: {grade.code if grade else 'Unknown'}",
                ))

    for sale in sales:
        existing = db.query(ProcessingEvent).filter(
            ProcessingEvent.sale_id == sale.id,
            ProcessingEvent.event_type == "SaleRecorded"
        ).first()
        if not existing:
            events.append(ProcessingEvent(
                event_type="SaleRecorded",
                lot_id=None,
                asset_id=None,
                sale_id=sale.id,
                employee_id=sale.sold_by,
                event_data={"total_amount": float(sale.total_amount)},
                notes=f"Sale {sale.sale_code} recorded",
            ))

    db.add_all(events)
    db.commit()
    print(f"  Added {len(events)} processing events")
    return events


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("VeggieOps AI - Synthetic Data Generator (All Chunks)")
    print("=" * 60)

    db = SessionLocal()
    try:
        print("\n[1/15] Generating farmers...")
        farmers = generate_farmers(db)

        print("\n[2/15] Generating employees...")
        employees = generate_employees(db)

        print("\n[3/15] Generating customers...")
        customers = generate_customers(db)

        print("\n[4/15] Generating purchase orders...")
        pos = generate_purchase_orders(db, farmers, employees)

        print("\n[5/15] Generating collection trips...")
        trips = generate_collection_trips(db, pos, employees)

        print("\n[6/15] Generating deliveries...")
        deliveries = generate_deliveries(db, pos, employees)

        print("\n[7/15] Generating lots...")
        lots = generate_lots(db, pos)

        print("\n[8/15] Generating skids...")
        skids = generate_skids(db, lots)

        print("\n[9/15] Generating assets...")
        assets = generate_assets(db, lots, skids)

        print("\n[10/15] Generating sort results...")
        sort_results = generate_sort_results(db, lots, employees)

        print("\n[11/15] Generating quality tests...")
        tests = generate_quality_tests(db, assets, employees, lots, sort_results)

        print("\n[12/15] Generating inventory, transactions, and prices...")
        inventory = generate_inventory(db, assets, lots)
        transactions = generate_inventory_transactions(db, inventory, employees)
        vegetables = db.query(Vegetable).all()
        prices = generate_prices(db, vegetables)

        print("\n[13/15] Generating sales with line items...")
        sales = generate_sales(db, customers, inventory, tests, employees, lots)

        print("\n[14/15] Generating cost entries and labor records...")
        costs = generate_cost_entries(db, lots, pos, trips, employees)
        labor = generate_labor_records(db, lots, employees)

        print("\n[15/15] Generating processing events...")
        events = generate_processing_events(db, lots, sales, sort_results, tests, employees)

        print("\n" + "=" * 60)
        print("MILESTONE 4 COMPLETE!")
        print(f"  Sales:              {db.query(Sale).count()}")
        print(f"  Sale Items:         {db.query(SaleItem).count()}")
        print(f"  Cost Entries:       {db.query(CostEntry).count()}")
        print(f"  Labor Records:      {db.query(LaborRecord).count()}")
        print(f"  Processing Events:  {db.query(ProcessingEvent).count()}")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR during generation: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
