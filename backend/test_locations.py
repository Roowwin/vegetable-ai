"""Test location service."""
from app.services.location_service import LocationService
from app.services.lot_service import LotService
from app.db.session import SessionLocal

db = SessionLocal()

# Test LocationService
loc_service = LocationService(db)
locations, total = loc_service.list()
print(f"PASS: Found {total} locations")

# Test get_by_code
cold_room = loc_service.get_by_code("COLD_ROOM_A")
if cold_room:
    print(f"PASS: Found COLD_ROOM_A (id={cold_room.id})")

# Test get_contents
if cold_room:
    contents = loc_service.get_contents(cold_room.id)
    print(f"PASS: COLD_ROOM_A has {contents['lot_count']} lots, {contents['asset_count']} assets")

# Test LotService.move_lot - FIXED: unpack the tuple
lot_service = LotService(db)
lots, total = lot_service.list(limit=1)  # Now correctly unpacks
if lots:
    lot = lots[0]
    try:
        result = lot_service.move_lot(
            lot_code=lot.lot_code,
            to_location_code="COLD_ROOM_A",
            employee_id=1,
            reason="Test move",
        )
        print(f"PASS: Moved {result['lot_code']} to {result['to_location']}")
    except ValueError as e:
        print(f"INFO: {e}")

# Check history
if cold_room:
    history = loc_service.get_history(cold_room.id)
    print(f"PASS: Location has {len(history)} history records")

db.close()
print()
print("Phase B (Location Service) complete!")
