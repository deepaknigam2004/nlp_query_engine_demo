from fastapi import APIRouter
from backend.services.schema_discovery import SchemaDiscovery

router = APIRouter()

@router.get("/schema")
async def get_schema():
    return SchemaDiscovery.current_schema or {}
