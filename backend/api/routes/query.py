from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.query_engine import QueryEngine

router = APIRouter()

class QueryPayload(BaseModel):
    query: str
    connection_string: str = None

_engine = None

def _get_engine(connection_string=None):
    global _engine
    if _engine is None:
        _engine = QueryEngine(connection_string=connection_string)
    return _engine

@router.post("/query")
async def process_query(payload: QueryPayload):
    engine = _get_engine(payload.connection_string)
    try:
        return engine.process_query(payload.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/query/history")
async def query_history():
    engine = _get_engine()
    return {"history": list(engine.cache.keys())}
