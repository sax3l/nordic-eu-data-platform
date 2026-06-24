# Orchestrator API — main.py
# FastAPI application for 0pt.app
# Start: uvicorn main:app --host 0.0.0.0 --port 8000

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid
import json
import os
import io
import csv
import asyncio
import redis.asyncio as redis
import psycopg2
import psycopg2.extras
import httpx

app = FastAPI(
    title="0pt.app API",
    description="SIAX Technology AB — Data Service Marketplace",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
security = HTTPBearer()

# ============================================================================
# MODELS
# ============================================================================

class OrderRequest(BaseModel):
    service_id: str
    parameters: dict = Field(default_factory=dict, description="Service-specific filters")
    output_format: Literal["csv", "json", "parquet", "excel", "api"] = "csv"
    urgency: Literal["standard", "priority", "express"] = "standard"

class EstimateRequest(BaseModel):
    service_id: str
    parameters: dict = Field(default_factory=dict)

class EstimateResponse(BaseModel):
    estimate_id: str
    service: str
    estimated_cost_low: float
    estimated_cost_high: float
    estimated_time_hours: float
    estimated_records_low: int
    estimated_records_high: int
    confidence_tier: str
    breakdown: dict
    valid_until: str

class AssistantQuery(BaseModel):
    query: str
    context: dict = Field(default_factory=dict)

class AssistantResponse(BaseModel):
    recommended_service: str
    confidence: float
    estimated_price: str
    estimated_time: str
    estimated_records: str
    explanation: str
    alternatives: list

class WebhookRequest(BaseModel):
    url: str
    events: list[str]
    secret: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    service_id: str
    status: str
    parameters: dict
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    estimated_time_minutes: Optional[int]
    actual_time_minutes: Optional[int]
    estimated_records: Optional[int]
    actual_records: Optional[int]
    confidence_score: Optional[float]
    output_format: str
    created_at: str
    updated_at: Optional[str]
    completed_at: Optional[str]

# ============================================================================
# SERVICE CATALOG (loaded from JSON — can be dynamic)
# ============================================================================

CATALOG = {
    "ICP_LEAD_LIST_SE": {
        "name": "ICP Lead List — Sweden",
        "category": "lead_gen",
        "base_price": 1995,
        "price_per_record": 1.50,
        "description": "Decision-maker contacts for Swedish companies",
        "filters": ["industry", "employees_min", "employees_max", "roles", "region"],
        "estimated_time_hours": 4,
        "complexity": 1.2,
    },
    "COMPANY_DB_SE": {
        "name": "Swedish Company Database",
        "category": "datasets",
        "base_price": 2995,
        "description": "All Swedish companies with board members, address, industry",
        "filters": ["industry", "employees_min", "employees_max", "region", "status"],
        "estimated_time_hours": 2,
        "complexity": 1.0,
    },
    "SINGLE_VEHICLE_LOOKUP": {
        "name": "Single Vehicle Lookup",
        "category": "vehicle",
        "base_price": 29,
        "description": "Vehicle registration data for one vehicle",
        "filters": ["registration_number", "country"],
        "estimated_time_hours": 0.02,
        "complexity": 1.0,
    },
    "SINGLE_COMPANY_DEEP": {
        "name": "Single Company Deep Enrichment",
        "category": "enrichment",
        "base_price": 99,
        "description": "Full company profile + all decision-makers",
        "filters": ["org_number", "country"],
        "estimated_time_hours": 0.5,
        "complexity": 1.5,
    },
    "MARKET_ANALYSIS_SE": {
        "name": "Market Analysis — Sweden",
        "category": "market_analysis",
        "base_price": 3995,
        "description": "Industry overview with trends, competitors, KPIs",
        "filters": ["industry", "region", "scope"],
        "estimated_time_hours": 8,
        "complexity": 3.0,
    },
    "PDF_STRUCTURE_BATCH": {
        "name": "PDF → Structured Data (100 docs)",
        "category": "document",
        "base_price": 1495,
        "description": "Extract structured data from 100 PDFs",
        "filters": ["document_type", "language", "output_schema"],
        "estimated_time_hours": 4,
        "complexity": 1.5,
    },
}

# ============================================================================
# AUTH
# ============================================================================

async def get_customer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate API key and return customer."""
    api_key = credentials.credentials
    customer_id = await redis_client.get(f"apikey:{api_key}")
    if not customer_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return customer_id.decode()

# ============================================================================
# ESTIMATE ENDPOINT
# ============================================================================

@app.post("/api/v1/estimates", response_model=EstimateResponse)
async def create_estimate(req: EstimateRequest):
    """Get price/time estimate without creating order."""
    if req.service_id not in CATALOG:
        raise HTTPException(status_code=404, detail="Service not found")

    service = CATALOG[req.service_id]
    base = service["base_price"]

    records_est = req.parameters.get("estimated_records", 1000)
    complexity = service["complexity"]

    low = round(base * complexity * 0.8)
    high = round(base * complexity * 1.2)

    estimate_id = f"est_{uuid.uuid4().hex[:8]}"
    return EstimateResponse(
        estimate_id=estimate_id,
        service=service["name"],
        estimated_cost_low=low,
        estimated_cost_high=high,
        estimated_time_hours=service["estimated_time_hours"],
        estimated_records_low=max(50, int(records_est * 0.7)),
        estimated_records_high=int(records_est * 1.3),
        confidence_tier="high" if complexity < 2.0 else "medium",
        breakdown={
            "base_price": base,
            "complexity_factor": complexity,
            "urgency_factor": 1.0,
        },
        valid_until=datetime.now(timezone.utc).isoformat(),
    )

# ============================================================================
# ORDER ENDPOINTS
# ============================================================================

@app.post("/api/v1/orders", response_model=OrderResponse)
async def create_order(req: OrderRequest, customer_id: str = Depends(get_customer)):
    """Create a new data order."""
    if req.service_id not in CATALOG:
        raise HTTPException(status_code=404, detail="Service not found")

    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    order = {
        "id": order_id,
        "customer_id": customer_id,
        "service_id": req.service_id,
        "status": "pending",
        "parameters": req.parameters,
        "output_format": req.output_format,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Store in Redis (temporary) and queue for estimation
    await redis_client.set(f"order:{order_id}", json.dumps(order))
    await redis_client.lpush("orders:pending", order_id)

    return OrderResponse(
        id=order_id,
        service_id=req.service_id,
        status="pending",
        parameters=req.parameters,
        output_format=req.output_format,
        created_at=order["created_at"],
    )

@app.get("/api/v1/orders")
async def list_orders(customer_id: str = Depends(get_customer)):
    """List all orders for customer."""
    orders = []
    keys = await redis_client.keys(f"order:*")
    for key in keys:
        data = json.loads(await redis_client.get(key))
        if data.get("customer_id") == customer_id:
            orders.append(data)
    return sorted(orders, key=lambda o: o["created_at"], reverse=True)

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, customer_id: str = Depends(get_customer)):
    """Get order details."""
    data = await redis_client.get(f"order:{order_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Order not found")
    order = json.loads(data)
    if order["customer_id"] != customer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return OrderResponse(**order)

@app.get("/api/v1/orders/{order_id}/preview")
async def preview_order(order_id: str, customer_id: str = Depends(get_customer)):
    """Preview first 10 records of order data."""
    data = await redis_client.get(f"order:{order_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Order not found")
    order = json.loads(data)
    if order.get("status") not in ("ready", "delivered"):
        raise HTTPException(status_code=400, detail="Order not ready yet")

    # Return first 10 records
    result_data = await redis_client.get(f"result:{order_id}")
    if result_data:
        records = json.loads(result_data)
        return {"preview": records[:10], "total_records": len(records)}
    return {"preview": [], "total_records": 0}

@app.get("/api/v1/orders/{order_id}/data")
async def download_order(order_id: str, format: Optional[str] = "csv", customer_id: str = Depends(get_customer)):
    """Download order data."""
    data = await redis_client.get(f"order:{order_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Order not found")
    order = json.loads(data)

    result_data = await redis_client.get(f"result:{order_id}")
    if not result_data:
        raise HTTPException(status_code=400, detail="No data available")

    records = json.loads(result_data)

    if format == "csv":
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={order_id}.csv"}
        )
    elif format == "json":
        return records
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

# ============================================================================
# CATALOG ENDPOINTS
# ============================================================================

@app.get("/api/v1/catalog")
async def list_catalog():
    """List all available services."""
    return CATALOG

@app.get("/api/v1/catalog/{service_id}")
async def get_service(service_id: str):
    """Get single service details."""
    if service_id not in CATALOG:
        raise HTTPException(status_code=404, detail="Service not found")
    return CATALOG[service_id]

# ============================================================================
# AI ASSISTANT
# ============================================================================

@app.post("/api/v1/assistant/query", response_model=AssistantResponse)
async def assistant_query(req: AssistantQuery):
    """Natural language → service recommendation. Uses local Ollama."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "http://localhost:11434/v1/chat/completions",
                json={
                    "model": "phi4:14b",
                    "messages": [{
                        "role": "user",
                        "content": f"""Customer query: "{req.query}"
                        Available services: {json.dumps({k: v['name'] for k, v in CATALOG.items()})}
                        Return JSON with: recommended_service, confidence, estimated_price, estimated_time, estimated_records, explanation (in Swedish), alternatives."""
                    }],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                }
            )
            result = resp.json()
            content = json.loads(result["choices"][0]["message"]["content"])
            return AssistantResponse(
                recommended_service=content.get("recommended_service", list(CATALOG.keys())[0]),
                confidence=content.get("confidence", 0.5),
                estimated_price=content.get("estimated_price", "~1 000 kr"),
                estimated_time=content.get("estimated_time", "2-4 timmar"),
                estimated_records=content.get("estimated_records", "~1 000"),
                explanation=content.get("explanation", ""),
                alternatives=content.get("alternatives", []),
            )
        except Exception:
            return AssistantResponse(
                recommended_service="COMPANY_DB_SE",
                confidence=0.3,
                estimated_price="~1 000 kr",
                estimated_time="1-3 timmar",
                estimated_records="Varierar",
                explanation="Kunde inte nå AI-assistenten. Här är ett generellt förslag.",
                alternatives=[],
            )

# ============================================================================
# WEBHOOKS
# ============================================================================

@app.post("/api/v1/webhooks/register")
async def register_webhook(req: WebhookRequest, customer_id: str = Depends(get_customer)):
    """Register a webhook endpoint."""
    webhook_id = f"wh_{uuid.uuid4().hex[:8]}"
    await redis_client.set(f"webhook:{customer_id}:{webhook_id}", json.dumps(req.dict()))
    return {"webhook_id": webhook_id, "status": "registered"}

# ============================================================================
# HEALTH
# ============================================================================

@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "redis": await redis_client.ping(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
