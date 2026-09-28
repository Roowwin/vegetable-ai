"""
Seed Default Locations
======================
Populates the locations table with the shop's standard areas.
"""

from app.db.session import SessionLocal
from app.models.location import Location


DEFAULT_LOCATIONS = [
    {
        "code": "SORT_BENCH",
        "name": "Sort Bench",
        "location_type": "processing",
        "temperature_zone": "ambient",
        "notes": "Where vegetables are sorted and graded after arrival",
    },
    {
        "code": "TEST_BENCH",
        "name": "Quality Test Bench",
        "location_type": "processing",
        "temperature_zone": "ambient",
        "notes": "Where quality tests are performed",
    },
    {
        "code": "COLD_ROOM_A",
        "name": "Cold Room A (Leafy Greens)",
        "location_type": "storage",
        "temperature_zone": "refrigerated",
        "capacity_kg": 500.0,
        "notes": "For leafy greens, cruciferous vegetables",
    },
    {
        "code": "COLD_ROOM_B",
        "name": "Cold Room B (Fruits)",
        "location_type": "storage",
        "temperature_zone": "refrigerated",
        "capacity_kg": 500.0,
        "notes": "For fruits and other refrigerated items",
    },
    {
        "code": "DRY_STORAGE",
        "name": "Dry Storage",
        "location_type": "storage",
        "temperature_zone": "ambient",
        "capacity_kg": 1000.0,
        "notes": "For root vegetables, potatoes, onions",
    },
    {
        "code": "SALES_FLOOR",
        "name": "Sales Floor (Main Retail)",
        "location_type": "sales",
        "temperature_zone": "ambient",
        "notes": "Main retail display area",
    },
    {
        "code": "DISPLAY_FRONT",
        "name": "Front Display (Premium)",
        "location_type": "sales",
        "temperature_zone": "ambient",
        "notes": "Premium grade display at store front",
    },
    {
        "code": "WHOLESALE_AREA",
        "name": "Wholesale Area",
        "location_type": "wholesale",
        "temperature_zone": "ambient",
        "notes": "Bulk storage for wholesale customers",
    },
    {
        "code": "QUARANTINE",
        "name": "Quarantine Area",
        "location_type": "quarantine",
        "temperature_zone": "refrigerated",
        "notes": "For items with suspected quality issues",
    },
    {
        "code": "RECYCLE_BIN",
        "name": "Recycle Bin",
        "location_type": "disposal",
        "temperature_zone": "ambient",
        "notes": "Final destination for recycle-grade items",
    },
]


def main():
    print("=" * 60)
    print("VeggieOps AI - Seeding Locations")
    print("=" * 60)

    db = SessionLocal()
    try:
        for loc_data in DEFAULT_LOCATIONS:
            existing = db.query(Location).filter(Location.code == loc_data["code"]).first()
            if existing:
                print(f"  Exists: {loc_data['code']}")
                continue

            location = Location(**loc_data)
            db.add(location)
            print(f"  Added: {loc_data['code']} ({loc_data['name']})")

        db.commit()

        total = db.query(Location).count()
        print(f"\nTotal locations in database: {total}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
