from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os, uuid

from backend.services.schema_discovery import SchemaDiscovery
from backend.services.document_processor import DocumentProcessor

router = APIRouter()
schema_discovery = SchemaDiscovery()
doc_processor = DocumentProcessor()

@router.post("/database")
async def connect_database(connection_string: str = Form(...)):
    try:
        schema = schema_discovery.analyze_database(connection_string)
        return {"ok": True, "schema": schema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/documents")
async def upload_documents(files: list[UploadFile] = File(...)):
    saved_paths = []
    os.makedirs("sample_data/uploads", exist_ok=True)
    for f in files:
        filename = f.filename
        dest = os.path.join("sample_data/uploads", str(uuid.uuid4()) + "_" + filename)
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)
        saved_paths.append(dest)
    doc_processor.process_documents(saved_paths)
    return {"ok": True, "uploaded": len(saved_paths)}

@router.get("/status")
async def ingestion_status():
    return {"status": "idle"}
