import uvicorn
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
from manager.agent import TAX_INVOICE_REGISTRY, DELIVERY_NOTE_REGISTRY

ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "https://sdh22.github.io",
]

app = get_fast_api_app(
    agents_dir="C:\\Users\\Lenovo E480\\Desktop\\Codes\\adk\\7-multi-agent",
    allow_origins=ALLOWED_ORIGINS,
    web=True,
)


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")

    # Handle preflight
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "600"
        return response

    response = await call_next(request)

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


@app.post("/lookup/invoice")
async def lookup_invoice(request: Request):
    data = await request.json()
    po  = data.get("po_number", "").strip().upper()
    cc  = data.get("customer_code", "").strip().upper()
    entry = TAX_INVOICE_REGISTRY.get(po)
    if not entry:
        return JSONResponse({"status": "not_found"})
    if entry.get("customer_code", "").upper() != cc:
        return JSONResponse({"status": "mismatch"})
    return JSONResponse({"status": "found", **entry})


@app.post("/lookup/delivery")
async def lookup_delivery(request: Request):
    data = await request.json()
    po  = data.get("po_number", "").strip().upper()
    cc  = data.get("customer_code", "").strip().upper()
    entry = DELIVERY_NOTE_REGISTRY.get(po)
    if not entry:
        return JSONResponse({"status": "not_found"})
    if entry.get("customer_code", "").upper() != cc:
        return JSONResponse({"status": "mismatch"})
    return JSONResponse({"status": "found", **entry})


if __name__ == "__main__":
    print("Starting Steel Wood ADK server on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
