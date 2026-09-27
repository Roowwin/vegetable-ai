"""
API Package
===========
HTTP endpoint layer. Each module exports an APIRouter that gets
included in the main FastAPI app.

Pattern:
    router = APIRouter(prefix="/api/farmers", tags=["Farmers"])
    
    @router.get("")
    async def list_farmers(...):
        ...
"""
