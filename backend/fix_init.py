"""Add Location import to models __init__.py"""
content = open('/app/app/models/__init__.py', 'r').read()

if 'from app.models.location' not in content:
    content = 'from app.models.location import Location, LocationHistory\n' + content
    open('/app/app/models/__init__.py', 'w').write(content)
    print('Added Location import')
else:
    print('Location import already exists')
