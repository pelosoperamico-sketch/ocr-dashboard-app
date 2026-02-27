import base64
import json
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="OCR + Sheets + Email", layout="wide")

# --- Secrets ---
if "GAS_BASE_URL" not in st.secrets:
    st.error("Manca GAS_BASE_URL nei Secrets. Vai su Settings → Secrets e aggiungilo.")
    st.stop()

GAS_BASE_URL = st.secrets["GAS_BASE_URL"]


# --- Helpers ---
def gas_post(path: str, payload: dict, timeout=90):
    r = requests.post(GAS_BASE_URL, params={"path": path}, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def gas_get(mode: str, filters: dict | None = None, timeout=60):
    params = {"mode": mode}
    if filters is not None:
        params["filters"] = json.dumps(filters)
    r = requests.get(GAS_BASE_URL, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def to_b64(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")

def safe_df(rows):
    df = pd.DataFrame(rows or [])
    # normalizza colonne attese (se mancano, le crea)
    for col in ["uniqueKey", "vendor", "date", "total", "status", "email", "timestamp", "rawText"]:
        if col not in df.columns:
            df[col] = None
    return df


# --- Sidebar ---
st.sidebar.title("Menu")
page = st.sidebar.radio(
    "Seleziona tool",
    ["1) Scanner OCR", "2) Dashboard", "3) Ricerca", "4) Email semi-automatiche"]
)

# Piccolo check connessione
with st.sidebar.expander("Test connessione"):
    if st.button("Ping GAS"):
        try:
            res = gas_get("dashboard")
            if res.get("ok"):
                st.success("OK: GAS raggiungibile")
            else:
                st.error(res)
        except Exception as e:
            st.error(str(e))

# -------------------- 1) OCR --------------------
if page.startswith("1"):
    st.title("Tool 1 — Carica o scatta foto → OCR → salva su Google Sheet")

    col1, col2 = st.columns(2)
    with col1:
        up = st.file_uploader("Carica immagine", type=["jpg", "jpeg", "png"])
    with col2:
        cam = st.camera_input("Oppure scatta dal cellulare")

    image_bytes = None
    filename = None

    if up is not None:
        image_bytes = up.read()
        filename = up.name
    elif cam is not None:
        image_bytes = cam.getvalue()
        filename = "camera.jpg"

    if image_bytes:
        st.image(image_bytes, caption="Anteprima", use_container_width=True)

        if st.button("Esegui OCR e salva", type="primary"):
            with st.spinner("OCR in corso..."):
                payload = {"filename": filename, "imageBase64": to_b64(image_bytes)}
                res = gas_post("ocr", payload, timeout=120)

            if res.get("ok"):
                if res.get("dedup"):
                    st.info("Documento già presente (dedup).")
                else:
                    st.success("Salvato su Google Sheet!")
                st.subheader("Dati estratti")
                st.json(res.get("extracted", {}))
                st.caption(f"uniqueKey: {res.get('uniqueKey')}")
            else:
                st.error(res)

# -------------------- 2) Dashboard --------------------
elif page.startswith("2"):
    st.title("Tool 2 — Dashboard basata su Google Sheet")

    try:
        res = gas_get("dashboard")
    except Exception as e:
        st.error(f"Errore chiamando GAS: {e}")
        st.stop()

    if not res.get("ok"):
        st.error(res)
        st.stop()

    df = safe_df(res.get("rows"))
    if df.empty:
        st.warning("Nessun dato nel foglio.")
        st.stop()

    # KPI
    totals = pd.to_numeric(df["total"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Righe", len(df))
    c2.metric("Fornitori unici", int(df["vendor"].nunique(dropna=True)))
    c3.metric("Somma totali", f"{totals.sum():.2f}")
    c4.metric("Nuove (NEW)", int((df["status"].astype(str) == "NEW").sum()))

    st.subheader("Tabella dati")
    st.dataframe(df.drop(columns=["rawText"], errors="ignore"), use_container_width=True)

# -------------------- 3) Ricerca --------------------
elif page.startswith("3"):
    st.title("Tool 3 — Ricerca con filtri (Google Sheet)")

    with st.sidebar:
        vendor = st.text_input("Fornitore contiene")
        status = st.selectbox("Status", ["", "NEW", "EMAILED"])
        min_total = st.number_input("Totale minimo", value=0.0, step=1.0)
        apply_max = st.checkbox("Applica totale massimo")
        max_total = st.number_input("Totale massimo", value=0.0, step=1.0, disabled=not apply_max)

    filters = {
        "vendor": vendor,
        "status": status,
        "minTotal": min_total if min_total > 0 else None,
        "maxTotal": max_total if apply_max else None
    }

    try:
        res = gas_get("search", filters)
    except Exception as e:
        st.error(f"Errore chiamando GAS: {e}")
        st.stop()

    if not res.get("ok"):
        st.error(res)
        st.stop()

    df = safe_df(res.get("rows"))
    st.caption(f"Risultati: {len(df)}")
    st.dataframe(df.drop(columns=["rawText"], errors="ignore"), use_container_width=True)

# -------------------- 4) Email --------------------
else:
    st.title("Tool 4 — Seleziona righe e invia email semi-automatiche")

    st.info("Serve che nel foglio ci sia una colonna `email` compilata per ogni riga da contattare.")

    try:
        res = gas_get("dashboard")
    except Exception as e:
        st.error(f"Errore chiamando GAS: {e}")
        st.stop()

    if not res.get("ok"):
        st.error(res)
        st.stop()

    df = safe_df(res.get("rows"))
    if df.empty:
        st.warning("Nessun dato nel foglio.")
        st.stop()

    # editor con checkbox
    df_view = df.drop(columns=["rawText"], errors="ignore").copy()
    df_view.insert(0, "select", False)

    edited = st.data_editor(
        df_view,
        use_container_width=True,
        num_rows="fixed",
        column_config={"select": st.column_config.CheckboxColumn("Seleziona")}
    )

    selected = edited[edited["select"] == True].drop(columns=["select"])
    st.write(f"Selezionate: **{len(selected)}**")

    subject = st.text_input("Oggetto", "Richiesta informazioni")
    body = st.text_area(
        "Corpo (placeholder: {{vendor}}, {{date}}, {{total}}, {{uniqueKey}})",
        "Ciao {{vendor}},\n\nTi contatto in merito al documento {{uniqueKey}} del {{date}} (totale {{total}}).\n\nGrazie,\n"
    )

    if len(selected) > 0:
        first = selected.iloc[0].to_dict()
        preview = (body
            .replace("{{vendor}}", str(first.get("vendor", "")))
            .replace("{{date}}", str(first.get("date", "")))
            .replace("{{total}}", str(first.get("total", "")))
            .replace("{{uniqueKey}}", str(first.get("uniqueKey", "")))
        )
        st.subheader("Preview (prima selezione)")
        st.code(preview)

    if st.button("Invia email", type="primary", disabled=(len(selected) == 0)):
        items = selected.to_dict(orient="records")
        try:
            res2 = gas_post("sendEmails", {"items": items, "subject": subject, "body": body}, timeout=90)
        except Exception as e:
            st.error(f"Errore chiamando GAS: {e}")
            st.stop()

        if res2.get("ok"):
            st.success(f"Inviate: {len(res2.get('sent', []))} — Errori: {len(res2.get('failed', []))}")
            if res2.get("failed"):
                st.warning("Alcune email non sono partite:")
                st.json(res2["failed"])
        else:
            st.error(res2)
