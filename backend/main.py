from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.ingestion import router as ingestion_router
from backend.api.routes.query import router as query_router
from backend.api.routes.schema import router as schema_router

app = FastAPI(title="NLP Query Engine - Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router, prefix="/api/ingest", tags=["ingest"])
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(schema_router, prefix="/api", tags=["schema"])

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
