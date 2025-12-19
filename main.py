import os
from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import openai
from supabase import create_client
from dotenv import load_dotenv
import datetime

load_dotenv()
app = FastAPI()
security = HTTPBearer()

openai.api_key = os.getenv("OPENAI_API_KEY")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_SECRET"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

class ContextPayload(BaseModel):
    context_source: str
    redact_pii: Optional[bool] = True

from fastapi import UploadFile, File, Form
from typing import Optional
import json

@app.post("/v1/harmonize")
async def harmonize(
    document: Optional[UploadFile] = File(None),
    payload: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key)
):
    # Default payload if none
    if payload:
        try:
            payload_dict = json.loads(payload)
        except:
            payload_dict = {"context_source": "none"}
    else:
        payload_dict = {"context_source": "none"}

    response = {
        "status": "success",
        "processing_time": "1.2s",
        "data": {
            "invoice_id": "INV-2025-001",
            "vendor_name": "Fast-Track Logistics LLC",
            "normalized_from": "Fast Track Logs Inc.",
            "financials": {"amount_billed": 1200.00, "currency": "USD"},
            "conflict_check": {
                "crm_match": False,
                "flag": "PRICE_MISMATCH",
                "crm_expected_price": 1000.00,
                "note": "Invoice exceeds PO amount by 20%"
            }
        },
        "audit_trail": {
            "source_file": document.filename if document else "none.pdf",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "extractor_version": "v1.0",
            "page_number": 1,
            "line_item_ref": 4
        }
    }
    return response

from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# Inside harmonize function, before return:
supabase.table("harmonized_records").insert({
    "data": response["data"],
    "audit": response["audit_trail"]
}).execute()

@app.delete("/v1/record/{record_id}")
async def delete_record(record_id: str, api_key: str = Depends(verify_api_key)):
    supabase.table("harmonized_records").delete().eq("id", record_id).execute()
    return {"status": "deleted"}