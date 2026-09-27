"""
Seed Reference Data
===================
Populates the database with standard reference values.

Run with:
    docker exec veggie-backend python seed.py
"""

from app.db.session import SessionLocal
from app.models.quality import Grade
from app.models.inventory import Vegetable


def seed_grades(db) -> None:
    """Insert the 7 standard grades in hierarchy order."""
    grades = [
        {"code": "A",        "name": "Premium",         "rank": 1, "is_recyclable": False},
        {"code": "A-",       "name": "Premium Minus",   "rank": 2, "is_recyclable": False},
        {"code": "B",        "name": "Standard",        "rank": 3, "is_recyclable": False},
        {"code": "B-",       "name": "Standard Minus",  "rank": 4, "is_recyclable": False},
        {"code": "C",        "name": "Economy",         "rank": 5, "is_recyclable": False},
        {"code": "C-",       "name": "Economy Minus",   "rank": 6, "is_recyclable": False},
        {"code": "RECYCLE",  "name": "Recycle",         "rank": 7, "is_recyclable": True},
    ]
    
    for grade_data in grades:
        existing = db.query(Grade).filter(Grade.code == grade_data["code"]).first()
        if not existing:
            grade = Grade(**grade_data)
            db.add(grade)
            print(f"  Added grade: {grade_data['code']} ({grade_data['name']})")
        else:
            print(f"  Grade exists: {grade_data['code']}")
    
    db.commit()


def seed_vegetables(db) -> None:
    """Insert common vegetables into the catalog."""
    vegetables = [
        # Leafy greens
        {"name": "Spinach",     "category": "leafy",  "default_unit_type": "kg",     "shelf_life_days": 5,  "typical_waste_pct": 8.0},
        {"name": "Lettuce",     "category": "leafy",  "default_unit_type": "piece",  "shelf_life_days": 7,  "typical_waste_pct": 6.0},
        {"name": "Kale",        "category": "leafy",  "default_unit_type": "kg",     "shelf_life_days": 7,  "typical_waste_pct": 7.0},
        {"name": "Cabbage",     "category": "leafy",  "default_unit_type": "piece",  "shelf_life_days": 14, "typical_waste_pct": 5.0},
        # Root vegetables
        {"name": "Carrots",     "category": "root",   "default_unit_type": "kg",     "shelf_life_days": 21, "typical_waste_pct": 4.0},
        {"name": "Potatoes",    "category": "root",   "default_unit_type": "kg",     "shelf_life_days": 30, "typical_waste_pct": 3.0},
        {"name": "Onions",      "category": "root",   "default_unit_type": "kg",     "shelf_life_days": 45, "typical_waste_pct": 3.0},
        {"name": "Beets",       "category": "root",   "default_unit_type": "kg",     "shelf_life_days": 14, "typical_waste_pct": 5.0},
        {"name": "Radishes",    "category": "root",   "default_unit_type": "kg",     "shelf_life_days": 10, "typical_waste_pct": 6.0},
        # Fruits
        {"name": "Tomatoes",    "category": "fruit",  "default_unit_type": "kg",     "shelf_life_days": 10, "typical_waste_pct": 7.0},
        {"name": "Cucumbers",   "category": "fruit",  "default_unit_type": "kg",     "shelf_life_days": 10, "typical_waste_pct": 5.0},
        {"name": "Peppers",     "category": "fruit",  "default_unit_type": "kg",     "shelf_life_days": 14, "typical_waste_pct": 6.0},
        {"name": "Pumpkin",     "category": "fruit",  "default_unit_type": "piece",  "shelf_life_days": 60, "typical_waste_pct": 3.0},
        # Others
        {"name": "Green Beans", "category": "legume", "default_unit_type": "kg",     "shelf_life_days": 7,  "typical_waste_pct": 8.0},
        {"name": "Broccoli",    "category": "cruciferous", "default_unit_type": "piece", "shelf_life_days": 10, "typical_waste_pct": 6.0},
        {"name": "Cauliflower", "category": "cruciferous", "default_unit_type": "piece", "shelf_life_days": 14, "typical_waste_pct": 5.0},
    ]
    
    for veg_data in vegetables:
        existing = db.query(Vegetable).filter(Vegetable.name == veg_data["name"]).first()
        if not existing:
            veg = Vegetable(**veg_data)
            db.add(veg)
            print(f"  Added vegetable: {veg_data['name']}")
        else:
            print(f"  Vegetable exists: {veg_data['name']}")
    
    db.commit()


def main():
    print("=" * 50)
    print("VeggieOps AI — Database Seeding")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        print("\n[1/2] Seeding grades...")
        seed_grades(db)
        
        print("\n[2/2] Seeding vegetables...")
        seed_vegetables(db)
        
        # Summary
        grade_count = db.query(Grade).count()
        veg_count = db.query(Vegetable).count()
        
        print("\n" + "=" * 50)
        print("Seeding complete!")
        print(f"  Grades in database: {grade_count}")
        print(f"  Vegetables in database: {veg_count}")
        print("=" * 50)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
