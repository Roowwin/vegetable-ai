"""
Fix inventory.py to add location tracking fields.
Run once to update the model.
"""
import re

with open('/app/app/models/inventory.py', 'r') as f:
    content = f.read()

# Change 1: Add current_location_id to Lot class
old = '    status: Mapped[str] = mapped_column(String(32), default=LotStatus.REGISTERED.value, index=True)'
new = old + '''
    current_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), index=True
    )'''
if old in content and 'current_location_id' not in content:
    content = content.replace(old, new, 1)
    print('Added current_location_id to Lot')
else:
    print('Lot already has current_location_id OR pattern not found')

# Change 2: Add current_location_id to Asset class
old2 = '    status: Mapped[str] = mapped_column(String(32), default=AssetStatus.REGISTERED.value, index=True)'
new2 = old2 + '''
    current_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), index=True
    )'''
if old2 in content and content.count('current_location_id') < 2:
    content = content.replace(old2, new2, 1)
    print('Added current_location_id to Asset')
else:
    print('Asset already has current_location_id OR pattern not found')

# Change 3: Replace Inventory.location with location_id
old3 = '    location: Mapped[str] = mapped_column(String(60), default="Main Shop")'
new3 = '''    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), index=True
    )'''
if old3 in content:
    content = content.replace(old3, new3, 1)
    print('Replaced Inventory.location with location_id')
else:
    print('Inventory.location already replaced OR pattern not found')

with open('/app/app/models/inventory.py', 'w') as f:
    f.write(content)

print('Done!')
