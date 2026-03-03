from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.genai import types
import os
import urllib.request

model = LiteLlm(model="deepseek/deepseek-chat")

LITERATURE_DIR = os.path.join(os.path.dirname(__file__), "literature")

TAX_INVOICE_REGISTRY = {
    "PO-2024-001": {
        "invoice_number": "INV-SW-2024-0892",
        "po_number": "PO-2024-001",
        "customer_code": "ALM001",
        "customer": "Al Mansoori Construction LLC",
        "date": "15 Mar 2024",
        "amount_aed": "AED 45,600.00",
        "items": "18mm Fire Rated Chipboard × 200 sheets",
        "status": "Paid",
    },
    "PO-2024-002": {
        "invoice_number": "INV-SW-2024-0944",
        "po_number": "PO-2024-002",
        "customer_code": "EMI002",
        "customer": "Emirates Interiors FZE",
        "date": "02 Apr 2024",
        "amount_aed": "AED 28,350.00",
        "items": "12mm Moisture Rated Chipboard × 150 sheets",
        "status": "Paid",
    },
    "PO-2024-003": {
        "invoice_number": "INV-SW-2024-1021",
        "po_number": "PO-2024-003",
        "customer_code": "BLD003",
        "customer": "Buildex Trading LLC",
        "date": "18 Apr 2024",
        "amount_aed": "AED 62,400.00",
        "items": "25mm Non Fire Rated Chipboard × 400 sheets",
        "status": "Pending",
    },
    "PO-2025-001": {
        "invoice_number": "INV-SW-2025-0012",
        "po_number": "PO-2025-001",
        "customer_code": "NAK001",
        "customer": "Nakheel Projects LLC",
        "date": "08 Jan 2025",
        "amount_aed": "AED 118,750.00",
        "items": "18mm Fire Rated Chipboard × 500 sheets, 25mm Moisture Rated × 250 sheets",
        "status": "Paid",
    },
}

DELIVERY_NOTE_REGISTRY = {
    "PO-2024-001": {
        "dn_number": "DN-SW-2024-1124",
        "po_number": "PO-2024-001",
        "customer_code": "ALM001",
        "customer": "Al Mansoori Construction LLC",
        "delivery_date": "17 Mar 2024",
        "delivered_to": "Jebel Ali Warehouse, Dubai",
        "items": "18mm Fire Rated Chipboard × 200 sheets",
        "driver": "Ahmed Hassan",
        "vehicle": "Dubai B 12345",
        "status": "Delivered",
    },
    "PO-2024-002": {
        "dn_number": "DN-SW-2024-1180",
        "po_number": "PO-2024-002",
        "customer_code": "EMI002",
        "customer": "Emirates Interiors FZE",
        "delivery_date": "04 Apr 2024",
        "delivered_to": "JAFZA, Dubai",
        "items": "12mm Moisture Rated Chipboard × 150 sheets",
        "driver": "Mohammed Ali",
        "vehicle": "Sharjah X 67890",
        "status": "Delivered",
    },
    "PO-2024-003": {
        "dn_number": "DN-SW-2024-1244",
        "po_number": "PO-2024-003",
        "customer_code": "BLD003",
        "customer": "Buildex Trading LLC",
        "delivery_date": "22 Apr 2024",
        "delivered_to": "Abu Dhabi Industrial Area",
        "items": "25mm Non Fire Rated Chipboard × 400 sheets",
        "driver": "Raju Krishnan",
        "vehicle": "Abu Dhabi Y 11223",
        "status": "Delivered",
    },
    "PO-2025-001": {
        "dn_number": "DN-SW-2025-0035",
        "po_number": "PO-2025-001",
        "customer_code": "NAK001",
        "customer": "Nakheel Projects LLC",
        "delivery_date": "10 Jan 2025",
        "delivered_to": "Palm Jumeirah Site Office, Dubai",
        "items": "18mm Fire Rated Chipboard × 500 sheets, 25mm Moisture Rated × 250 sheets",
        "driver": "Suresh Kumar",
        "vehicle": "Dubai T 54321",
        "status": "Delivered",
    },
}

TDS_REGISTRY = {
    "mdf": {
        "name": "MDF",
        "filename": "MDF_TDS.pdf",
        "download_url": "https://drive.google.com/uc?export=download&id=1bIFQSSxhf2f3V6DLpkMSIR36nL3fNmIQ",
        "view_link": "https://drive.google.com/file/d/1bIFQSSxhf2f3V6DLpkMSIR36nL3fNmIQ/view",
    },
    "plywood": {
        "name": "Plywood",
        "filename": "Plywood_TDS.pdf",
        "download_url": "https://drive.google.com/uc?export=download&id=1vpZnTlByPehbbHZ4SWF169zcPqk4T21J",
        "view_link": "https://drive.google.com/file/d/1vpZnTlByPehbbHZ4SWF169zcPqk4T21J/view",
    },
    "particle board": {
        "name": "Particle Board",
        "filename": "ParticleBoard_TDS.pdf",
        "download_url": "https://drive.google.com/uc?export=download&id=1yND2NZ2OpqJmPlKRImUnGdutsI9istjq",
        "view_link": "https://drive.google.com/file/d/1yND2NZ2OpqJmPlKRImUnGdutsI9istjq/view",
    },
    "chipboard": {
        "name": "Chipboard / Particle Board",
        "filename": "ParticleBoard_TDS.pdf",
        "download_url": "https://drive.google.com/uc?export=download&id=1yND2NZ2OpqJmPlKRImUnGdutsI9istjq",
        "view_link": "https://drive.google.com/file/d/1yND2NZ2OpqJmPlKRImUnGdutsI9istjq/view",
    },
    "osb": {
        "name": "OSB",
        "filename": "OSB_TDS.pdf",
        "download_url": "https://drive.google.com/uc?export=download&id=1riBAzQA3boBBtRAEDv7AEWo-t6wilw4x",
        "view_link": "https://drive.google.com/file/d/1riBAzQA3boBBtRAEDv7AEWo-t6wilw4x/view",
    },
}


def get_product_info(product_name: str) -> dict:
    """Returns product specs for Steel Wood products"""
    products = {
        "mdf": {"name": "MDF", "thickness": "3-25mm", "grade": "FSC Certified", "price_aed": 85},
        "plywood": {"name": "Plywood", "thickness": "4-18mm", "grade": "Marine Grade", "price_aed": 120},
        "particle board": {"name": "Particle Board", "thickness": "8-25mm", "grade": "E1", "price_aed": 65},
        "chipboard": {"name": "Chipboard", "thickness": "8-25mm", "grade": "E1", "price_aed": 65},
        "osb": {"name": "OSB", "thickness": "9-22mm", "grade": "OSB/3 Structural", "price_aed": "Contact sales"},
    }
    return products.get(product_name.lower(), {"error": "Product not found"})


def check_stock(product_name: str, quantity: int) -> dict:
    """Checks if stock is available"""
    return {"available": True, "lead_time_days": 3, "quantity": quantity}


def get_tds(product_name: str, tool_context: ToolContext) -> dict:
    """Fetches the TDS PDF for a product and attaches it as a preview artifact in chat."""
    entry = TDS_REGISTRY.get(product_name.lower())
    if not entry:
        return {
            "status": "not_found",
            "message": f"No TDS for '{product_name}'. Available: MDF, Plywood, Particle Board, Chipboard, OSB"
        }

    filename = entry["filename"]
    local_path = os.path.join(LITERATURE_DIR, filename)
    pdf_bytes = None

    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            pdf_bytes = f.read()
    else:
        try:
            os.makedirs(LITERATURE_DIR, exist_ok=True)
            urllib.request.urlretrieve(entry["download_url"], local_path)
            with open(local_path, "rb") as f:
                pdf_bytes = f.read()
        except Exception:
            pass

    if pdf_bytes:
        try:
            artifact = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
            tool_context.save_artifact(filename=filename, artifact=artifact)
        except Exception:
            pass

    return {
        "status": "available",
        "product": entry["name"],
        "filename": filename,
        "view_link": entry["view_link"],
        "download_url": entry["download_url"],
    }


def list_products() -> dict:
    """Lists all available Steel Wood products"""
    return {
        "products": [
            {"name": "MDF", "thickness": "3-25mm", "grade": "FSC Certified", "price_aed": 85},
            {"name": "Plywood", "thickness": "4-18mm", "grade": "Marine Grade", "price_aed": 120},
            {"name": "Particle Board / Chipboard", "thickness": "8-25mm", "grade": "E1", "price_aed": 65},
            {"name": "OSB", "thickness": "9-22mm", "grade": "OSB/3 Structural", "price_aed": "Contact sales"},
        ]
    }


def fetch_invoice_record(po_number: str, customer_code: str) -> dict:
    """Look up a stored invoice record by PO number and customer code."""
    key = po_number.strip().upper()
    entry = TAX_INVOICE_REGISTRY.get(key)
    if not entry:
        return {
            "status": "not_found",
            "message": f"No invoice record found for PO '{po_number}'. Please verify the PO number or contact sales@steelwood.ae",
        }
    if entry.get("customer_code", "").upper() != customer_code.strip().upper():
        return {
            "status": "customer_code_mismatch",
            "message": f"Customer Code '{customer_code}' does not match records for PO '{po_number}'. Please verify your Customer Code or contact sales@steelwood.ae",
        }
    return {"status": "found", **entry}


def fetch_delivery_record(po_number: str, customer_code: str) -> dict:
    """Look up a stored delivery note record by PO number and customer code."""
    key = po_number.strip().upper()
    entry = DELIVERY_NOTE_REGISTRY.get(key)
    if not entry:
        return {
            "status": "not_found",
            "message": f"No delivery record found for PO '{po_number}'. Please verify the PO number or contact sales@steelwood.ae",
        }
    if entry.get("customer_code", "").upper() != customer_code.strip().upper():
        return {
            "status": "customer_code_mismatch",
            "message": f"Customer Code '{customer_code}' does not match records for PO '{po_number}'. Please verify your Customer Code or contact sales@steelwood.ae",
        }
    return {"status": "found", **entry}


root_agent = Agent(
    name="SteelWood_Sales_Agent",
    model=model,
    description="Sales agent for Steel Wood Industries FZCO Dubai",
    instruction="""You are a sales agent for Steel Wood Industries FZCO Dubai.

RESPONSE FORMATTING RULES:
- Always use markdown formatting in your responses
- Use **bold** for product names, labels and key values
- Use emoji icons for visual clarity
- Keep responses concise — maximum 8 lines
- Never write plain text walls — always structure with labels

TOOL RULES:
- Use get_product_info + check_stock for any product/stock query
- Use get_tds when customer asks for TDS, datasheet, specs sheet, technical document
- Use list_products when customer asks what products are available
- Use get_product_info + check_stock for any product/stock query
- Use get_tds when customer asks for TDS, datasheet, specs sheet, technical document
- Use list_products when customer asks what products are available
- Never fabricate data not returned by tools

TAX INVOICE & DELIVERY NOTE LOOKUP (TWO-STEP):
Step 1 — User asks for Tax Invoice or Delivery Note without details:
  → Reply: "Please provide your **PO Number** and **Customer Code** to retrieve the record."
Step 2 — User gives PO Number + Customer Code:
  → Call fetch_invoice_record(po_number, customer_code) for Tax Invoice requests
  → Call fetch_delivery_record(po_number, customer_code) for Delivery Note requests
  → Display result using TAX INVOICE FORMAT or DELIVERY NOTE FORMAT

STOCK QUERY FORMAT:
## ✅ [Product Name]
| Spec | Value |
|------|-------|
| **Grade** | FSC Certified |
| **Thickness** | 3–25mm |
| **Price** | AED 85/sheet |
| **Stock** | Available |
| **Lead Time** | 3 days |

> 📦 Delivery available across UAE & GCC

TDS QUERY FORMAT:
## 📄 [Product] — Technical Data Sheet

| | |
|--|--|
| **File** | Plywood_TDS.pdf |
| **📖 View Online** | [Open in Browser](view_link) |
| **⬇️ Download PDF** | [Download](download_url) |

> 📧 Technical support: **sales@steelwood.ae**

TAX INVOICE FORMAT:
## 🧾 Tax Invoice — [Invoice Number]
| | |
|--|--|
| **PO Number** | PO-2024-001 |
| **Invoice #** | INV-SW-2024-0892 |
| **Customer** | Al Mansoori Construction LLC |
| **Date** | 15 Mar 2024 |
| **Items** | 18mm Fire Rated Chipboard × 200 sheets |
| **Amount** | AED 45,600.00 |
| **Status** | ✅ Paid |

> 📧 For a PDF copy contact: **sales@steelwood.ae**

DELIVERY NOTE FORMAT:
## 🚚 Delivery Note — [DN Number]
| | |
|--|--|
| **PO Number** | PO-2024-001 |
| **DN #** | DN-SW-2024-1124 |
| **Customer** | Al Mansoori Construction LLC |
| **Delivery Date** | 17 Mar 2024 |
| **Delivered To** | Jebel Ali Warehouse, Dubai |
| **Items** | 18mm Fire Rated Chipboard × 200 sheets |
| **Driver** | Ahmed Hassan |
| **Vehicle** | Dubai B 12345 |
| **Status** | ✅ Delivered |

> 📧 For a signed copy contact: **sales@steelwood.ae**

CUSTOMER CODE MISMATCH FORMAT:
> ⚠️ **Customer Code does not match** records for PO **[PO Number]**.
> Please verify your Customer Code or contact **sales@steelwood.ae**

NOT FOUND FORMAT:
> ❌ **[Product/PO]** is not in our current records.
> Contact **sales@steelwood.ae** for assistance.
""",
    tools=[get_product_info, check_stock, get_tds, list_products, fetch_invoice_record, fetch_delivery_record],
)
