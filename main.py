from __future__ import annotations

from datetime import date
from typing import Literal, Optional, List, Dict, Any
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

app = FastAPI(title="Storico Fatture")

# ===== Demo data (sostituisci con DB) =====
INVOICES = [
    {
        "id": "A260355",
        "vendor": "DBL",
        "type": "Factura",
        "status": "Digitalizado",
        "docDate": "2026-02-18",
        "uploadDate": "2026-02-25",
        "amount": 149.34,
        "payStatus": "Vencido",
    },
    {
        "id": "A260270",
        "vendor": "DBL",
        "type": "Factura",
        "status": "Digitalizado",
        "docDate": "2026-02-08",
        "uploadDate": "2026-02-12",
        "amount": 404.84,
        "payStatus": "Vencido",
    },
    {
        "id": "B100011",
        "vendor": "ACME",
        "type": "Factura",
        "status": "Requieren revisión",
        "docDate": "2026-02-20",
        "uploadDate": "2026-02-20",
        "amount": 99.90,
        "payStatus": "Pendiente",
    },
    {
        "id": "C777001",
        "vendor": "FooBar SL",
        "type": "Factura",
        "status": "Rechazados",
        "docDate": "2026-01-28",
        "uploadDate": "2026-02-01",
        "amount": 871.75,
        "payStatus": "Pagado",
    },
]

SortKey = Literal["uploadDate", "docDate", "amount", "id"]
SortDir = Literal["asc", "desc"]

HTML_PAGE = """
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Documentos</title>
    <link rel="stylesheet" href="/static/style.css" />
  </head>
  <body>
    <div id="app"></div>
    <script src="/static/app.js"></script>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HTML_PAGE

@app.get("/api/invoices")
def list_invoices(
    q: str = Query(default=""),
    status: str = Query(default="ALL"),
    payStatus: str = Query(default="ALL"),
    fromDate: str = Query(default=""),
    toDate: str = Query(default=""),
    sort: SortKey = Query(default="uploadDate"),
    sortDir: SortDir = Query(default="desc"),
) -> JSONResponse:
    rows = filter_sort(INVOICES, q=q, status=status, pay_status=payStatus, from_date=fromDate, to_date=toDate, sort=sort, sort_dir=sortDir)
    return JSONResponse({"rows": rows, "total": len(rows)})

@app.get("/api/invoices.csv")
def export_invoices_csv(
    q: str = Query(default=""),
    status: str = Query(default="ALL"),
    payStatus: str = Query(default="ALL"),
    fromDate: str = Query(default=""),
    toDate: str = Query(default=""),
    sort: SortKey = Query(default="uploadDate"),
    sortDir: SortDir = Query(default="desc"),
    cols: str = Query(default="id,vendor,type,status,docDate,uploadDate,amount,payStatus"),
) -> Response:
    rows = filter_sort(INVOICES, q=q, status=status, pay_status=payStatus, from_date=fromDate, to_date=toDate, sort=sort, sort_dir=sortDir)
    col_keys = [c.strip() for c in cols.split(",") if c.strip()]

    header_map = {
        "id": "N.ro Documento",
        "vendor": "Proveedor",
        "type": "Tipo",
        "status": "Estado",
        "docDate": "Fecha documento",
        "uploadDate": "Fecha subida",
        "amount": "Importe",
        "payStatus": "Estado pago",
    }

    def esc(s: Any) -> str:
        s = "" if s is None else str(s)
        return '"' + s.replace('"', '""') + '"'

    lines = []
    lines.append(",".join(esc(header_map.get(k, k)) for k in col_keys))
    for r in rows:
        lines.append(",".join(esc(r.get(k, "")) for k in col_keys))

    csv = "\n".join(lines)
    return Response(
        content=csv.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="storico_fatture.csv"'},
    )

def filter_sort(data: List[Dict[str, Any]], *, q: str, status: str, pay_status: str, from_date: str, to_date: str, sort: str, sort_dir: str) -> List[Dict[str, Any]]:
    rows = list(data)

    qn = (q or "").strip().lower()
    if qn:
        def match(r: Dict[str, Any]) -> bool:
            return any(qn in str(r.get(k, "")).lower() for k in ["id", "vendor", "type", "status", "payStatus"])
        rows = [r for r in rows if match(r)]

    if status and status != "ALL":
        rows = [r for r in rows if r.get("status") == status]

    if pay_status and pay_status != "ALL":
        rows = [r for r in rows if r.get("payStatus") == pay_status]

    # date range on uploadDate (YYYY-MM-DD)
    if from_date:
        rows = [r for r in rows if str(r.get("uploadDate", "")) >= from_date]
    if to_date:
        rows = [r for r in rows if str(r.get("uploadDate", "")) <= to_date]

    reverse = (sort_dir != "asc")
    if sort == "amount":
        rows.sort(key=lambda r: float(r.get("amount", 0) or 0), reverse=reverse)
    else:
        rows.sort(key=lambda r: str(r.get(sort, "") or ""), reverse=reverse)

    return rows
