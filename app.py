import os
import json
import random
from datetime import datetime

import pandas as pd
import requests

from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable

# --- Optional (private sheets) ---
import gspread
from google.oauth2.service_account import Credentials


# =========================================================
# CONFIG GOOGLE SHEET
# =========================================================
SPREADSHEET_ID = "1P0dxL6YafUuRVhwYKGi0nG5aCYjqGa_UVSg1dn4uFh8"
GID = 41334363  # dal tuo URL
EXPORT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

# Per foglio privato: imposta env var GOOGLE_SERVICE_ACCOUNT_JSON (stringa JSON)
# e condividi il foglio con l'email del service account.
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()


# =========================================================
# DATA LOADER
# =========================================================
def load_sheet_df() -> pd.DataFrame:
    """
    Prova a caricare il foglio in 2 modi:
    1) CSV export (foglio pubblico)
    2) Google Sheets API (foglio privato) tramite service account
    """
    # 1) Public CSV export
    try:
        r = requests.get(EXPORT_CSV_URL, timeout=15)
        if r.status_code == 200 and len(r.text) > 10 and "DOCTYPE html" not in r.text[:200]:
            from io import StringIO
            df = pd.read_csv(StringIO(r.text))
            return df
    except Exception:
        pass

    # 2) Private via service account
    if SERVICE_ACCOUNT_JSON:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)

        sh = gc.open_by_key(SPREADSHEET_ID)
        ws = sh.get_worksheet_by_id(GID)
        values = ws.get_all_values()

        if not values or len(values) < 2:
            return pd.DataFrame()

        headers = values[0]
        rows = values[1:]
        df = pd.DataFrame(rows, columns=headers)
        return df

    # Se siamo qui: non è pubblico e non hai fornito credenziali
    raise PermissionError(
        "Impossibile leggere il Google Sheet: non è pubblico e manca GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def df_b_to_i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prende le 8 colonne da B a I in base alla POSIZIONE.
    (B=indice 1 ... I=indice 8 in zero-based)
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Fornitore", "Data fattura", "Codice fattura", "Articolo", "Quantità",
            "Prezzo unitario (IVA escl.)", "Prezzo totale riga (IVA escl.)", "Totale documento (IVA escl.)"
        ])

    # se il DF ha meno di 9 colonne, ritorna vuoto
    if df.shape[1] < 9:
        return pd.DataFrame(columns=[
            "Fornitore", "Data fattura", "Codice fattura", "Articolo", "Quantità",
            "Prezzo unitario (IVA escl.)", "Prezzo totale riga (IVA escl.)", "Totale documento (IVA escl.)"
        ])

    subset = df.iloc[:, 1:9].copy()
    subset.columns = [
        "Fornitore", "Data fattura", "Codice fattura", "Articolo", "Quantità",
        "Prezzo unitario (IVA escl.)", "Prezzo totale riga (IVA escl.)", "Totale documento (IVA escl.)"
    ]
    return subset


def to_float(x):
    if x is None:
        return 0.0
    s = str(x).strip()
    if not s:
        return 0.0
    # supporto virgola decimale
    s = s.replace(".", "").replace(",", ".") if (s.count(",") == 1 and s.count(".") >= 1) else s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def compute_kpis(df_full: pd.DataFrame) -> dict:
    """
    KPI secondo le tue regole (posizionali sul foglio):
    - Fatture scannerizzate = numero valori univoci presenti in colonna B
    - Numero fornitori = numero valori univoci concatenando le colonne B e D
    - Spesa totale = somma dei Totale documento (colonna I) per ogni valore univoco di (B+D)
    """
    if df_full is None or df_full.empty or df_full.shape[1] < 9:
        return {"fatture": 0, "fornitori": 0, "spesa": 0.0}

    col_b = df_full.iloc[:, 1].astype(str).str.strip()  # colonna B
    col_d = df_full.iloc[:, 3].astype(str).str.strip()  # colonna D
    col_i = df_full.iloc[:, 8]                          # colonna I

    # Fatture scannerizzate: unique su B
    fatture_scannerizzate = int(col_b.replace("", pd.NA).dropna().nunique())

    # Numero fornitori: unique su (B+D)
    key_bd = (col_b.fillna("") + "||" + col_d.fillna("")).replace("||", pd.NA)
    numero_fornitori = int(key_bd.dropna().nunique())

    # Spesa totale: dedup su (B+D), poi somma I
    tmp = pd.DataFrame({"key": key_bd, "totdoc": col_i})
    tmp = tmp[tmp["key"].notna()]
    tmp["totdoc_num"] = tmp["totdoc"].apply(to_float)
    tmp = tmp.drop_duplicates(subset=["key"], keep="first")
    spesa_totale = float(tmp["totdoc_num"].sum())

    return {"fatture": fatture_scannerizzate, "fornitori": numero_fornitori, "spesa": spesa_totale}


# =========================================================
# UI HELPERS
# =========================================================
def kpi_card(title: str, value: str):
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, className="text-muted", style={"fontSize": "0.9rem"}),
            html.Div(value, style={"fontSize": "1.6rem", "fontWeight": 800}),
        ]),
        className="shadow-sm",
    )


# =========================================================
# APP
# =========================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
server = app.server

app.index_string = """
<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>Storico Aziendale</title>
    {%favicon%}
    {%css%}
    <style>
      body { background-color: #0b1220; }
      .sidebar {
        width: 290px;
        position: fixed;
        top: 0; left: 0; bottom: 0;
        padding: 16px 14px;
        background: rgba(255,255,255,0.03);
        border-right: 1px solid rgba(255,255,255,0.08);
        overflow-y: auto;
      }
      .content {
        margin-left: 290px;
        padding: 22px 26px;
      }
      .navbtn {
        display: block;
        width: 100%;
        text-align: left;
        padding: 14px 14px;
        margin: 10px 0;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.02);
        color: #e5e7eb;
        text-decoration: none;
        font-size: 1.02rem;
      }
      .navbtn:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.14); }
      .navbtn.active { border-color: rgba(99,102,241,0.6); background: rgba(99,102,241,0.12); }

      .logo {
        display: inline-block;
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.02);
        font-weight: 900;
        letter-spacing: 0.04em;
        cursor: pointer;
        text-decoration: none;
        color: #e5e7eb;
      }
      .hint { color: rgba(255,255,255,0.70); }
      .panel {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        padding: 16px;
        background: rgba(255,255,255,0.03);
      }
    </style>
  </head>
  <body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
  </body>
</html>
"""

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="store-data", data=None),
    dcc.Store(id="store-error", data=None),

    # Sidebar
    html.Div([
        html.A("LOGO", href="/", className="logo", id="logo-link"),
        html.Div("Storico aziendale • fatture • spese", className="hint", style={"marginTop": "10px"}),

        html.Hr(style={"borderColor": "rgba(255,255,255,0.10)", "marginTop": "14px"}),

        html.Div("Funzioni", className="hint", style={"marginBottom": "8px"}),

        html.A("🧾  Storico Fatture", href="/storico-fatture", id="nav-storico", className="navbtn"),

        html.Hr(style={"borderColor": "rgba(255,255,255,0.10)", "marginTop": "14px"}),

        dbc.Button("🔄 Aggiorna dati", id="btn-refresh", color="secondary", className="w-100"),
        html.Div(id="last-refresh", className="hint", style={"marginTop": "10px", "fontSize": "0.9rem"}),

    ], className="sidebar"),

    # Content
    html.Div(id="page-content", className="content"),
])


# =========================================================
# DATA REFRESH
# =========================================================
@app.callback(
    Output("store-data", "data"),
    Output("store-error", "data"),
    Output("last-refresh", "children"),
    Input("btn-refresh", "n_clicks"),
    State("store-data", "data"),
    prevent_initial_call=False
)
def refresh_data(n, existing):
    # al primo load: carico comunque
    try:
        df_full = load_sheet_df()
        return df_full.to_dict("records"), None, f"Ultimo refresh: {datetime.now().strftime('%H:%M:%S')}"
    except Exception as e:
        # mantieni i dati esistenti se presenti
        return existing, str(e), f"Errore refresh: {datetime.now().strftime('%H:%M:%S')}"


# =========================================================
# ROUTER + NAV ACTIVE
# =========================================================
@app.callback(
    Output("page-content", "children"),
    Output("nav-storico", "className"),
    Input("url", "pathname"),
    State("store-data", "data"),
    State("store-error", "data"),
)
def render_page(pathname, data, err):
    nav_storico_class = "navbtn"
    is_home = pathname in (None, "/", "")

    # Homepage (nessuna funzione selezionata)
    if is_home:
        home = html.Div([
            html.H2("Homepage"),
            html.Div("Questa app traccia lo storico dell’azienda: fatture, fornitori e spese nel tempo.", className="hint"),
            html.Br(),
            html.Div(className="panel", children=[
                html.H4("Cosa puoi fare qui"),
                html.Ul([
                    html.Li("Consultare lo storico fatture (KPI + tabella dettagli)."),
                    html.Li("Cercare e filtrare informazioni (nelle prossime funzioni)."),
                    html.Li("Automatizzare attività operative (nelle prossime funzioni)."),
                ]),
                html.Div("Seleziona una funzione dal menu a sinistra per iniziare.", className="hint"),
            ])
        ])
        return home, nav_storico_class

    # Storico fatture
    if pathname == "/storico-fatture":
        nav_storico_class += " active"

        # Error banner se non riesco a leggere il foglio
        if err and not data:
            return html.Div([
                html.H2("Storico Fatture"),
                dbc.Alert(
                    [
                        html.Div("Non riesco a leggere il Google Sheet.", style={"fontWeight": 800}),
                        html.Div(err),
                        html.Br(),
                        html.Div("Soluzioni:"),
                        html.Ul([
                            html.Li("Rendere il foglio pubblico (solo per demo) così funziona l’export CSV."),
                            html.Li("Oppure usare Service Account: imposta GOOGLE_SERVICE_ACCOUNT_JSON e condividi il foglio col service account."),
                        ]),
                    ],
                    color="danger",
                ),
            ]), nav_storico_class

        df_full = pd.DataFrame(data or [])
        kpis = compute_kpis(df_full)
        df_table = df_b_to_i(df_full)

        content = html.Div([
            html.H2("Storico Fatture"),
            html.Div("KPI e dettaglio righe (colonne B → I del foglio).", className="hint"),
            html.Hr(style={"borderColor": "rgba(255,255,255,0.10)"}),

            dbc.Row([
                dbc.Col(kpi_card("Fatture scannerizzate", f"{kpis['fatture']}"), md=4),
                dbc.Col(kpi_card("Numero fornitori", f"{kpis['fornitori']}"), md=4),
                dbc.Col(kpi_card("Spesa totale", f"{kpis['spesa']:.2f} €"), md=4),
            ], className="g-3"),

            html.Div(style={"height": "14px"}),

            html.Div(className="panel", children=[
                html.Div("Dettaglio", style={"fontWeight": 800, "marginBottom": "10px"}),
                DataTable(
                    id="table-storico",
                    columns=[{"name": c, "id": c} for c in df_table.columns],
                    data=df_table.to_dict("records"),
                    page_size=12,
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": "rgba(255,255,255,0.05)",
                        "border": "1px solid rgba(255,255,255,0.08)",
                        "color": "#e5e7eb",
                        "fontWeight": "700",
                    },
                    style_cell={
                        "backgroundColor": "rgba(255,255,255,0.02)",
                        "color": "#e5e7eb",
                        "border": "1px solid rgba(255,255,255,0.06)",
                        "padding": "10px",
                        "whiteSpace": "normal",
                        "height": "auto",
                    },
                )
            ]),
        ])

        return content, nav_storico_class

    # fallback -> homepage
    return html.Div([dcc.Location(pathname="/", id="redir")]), nav_storico_class


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
