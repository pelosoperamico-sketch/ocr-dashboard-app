import streamlit as st
import pandas as pd
import numpy as np
import base64
import random
from datetime import datetime

st.set_page_config(page_title="OCR Dashboard UX", layout="wide")

# ---------------------------------------------------
# DATI MOCK (simulazione Google Sheet)
# ---------------------------------------------------

def generate_mock_data(n=25):
    vendors = ["ABC Srl", "Tech Supply", "Global Parts", "Fast Logistics", "Blue Energy"]
    statuses = ["NEW", "EMAILED"]

    data = []
    for i in range(n):
        data.append({
            "uniqueKey": f"DOC-{1000+i}",
            "vendor": random.choice(vendors),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "total": round(random.uniform(50, 1500), 2),
            "status": random.choice(statuses),
            "email": "info@example.com"
        })
    return pd.DataFrame(data)

if "data" not in st.session_state:
    st.session_state.data = generate_mock_data()

df = st.session_state.data

# ---------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------

st.sidebar.title("Menu")
page = st.sidebar.radio(
    "Seleziona tool",
    ["1) Scanner OCR",
     "2) Dashboard",
     "3) Ricerca & Filtri",
     "4) Email semi-automatiche"]
)

# ---------------------------------------------------
# TOOL 1 - OCR MOCK
# ---------------------------------------------------

if page.startswith("1"):
    st.title("Scanner OCR (Simulazione UX)")

    col1, col2 = st.columns(2)

    with col1:
        uploaded = st.file_uploader("Carica immagine", type=["jpg", "jpeg", "png"])

    with col2:
        camera = st.camera_input("Oppure scatta foto")

    image_bytes = None

    if uploaded:
        image_bytes = uploaded.read()
    elif camera:
        image_bytes = camera.getvalue()

    if image_bytes:
        st.image(image_bytes, caption="Anteprima", use_container_width=True)

        if st.button("Simula OCR", type="primary"):
            with st.spinner("Simulazione scansione..."):
                st.success("OCR completato (mock)")

                extracted = {
                    "vendor": "ABC Srl",
                    "date": "27/02/2026",
                    "total": 249.90
                }

                st.subheader("Dati estratti")
                st.json(extracted)

                if st.button("Simula salvataggio su Sheet"):
                    new_row = {
                        "uniqueKey": f"DOC-{random.randint(2000,3000)}",
                        "vendor": extracted["vendor"],
                        "date": extracted["date"],
                        "total": extracted["total"],
                        "status": "NEW",
                        "email": "info@example.com"
                    }
                    st.session_state.data = pd.concat(
                        [st.session_state.data, pd.DataFrame([new_row])],
                        ignore_index=True
                    )
                    st.success("Riga aggiunta (mock)")

# ---------------------------------------------------
# TOOL 2 - DASHBOARD
# ---------------------------------------------------

elif page.startswith("2"):
    st.title("Dashboard (Mock Data)")

    totals = df["total"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documenti", len(df))
    c2.metric("Fornitori unici", df["vendor"].nunique())
    c3.metric("Totale complessivo", f"{totals.sum():.2f}")
    c4.metric("Da inviare", (df["status"] == "NEW").sum())

    st.subheader("Elenco documenti")
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# TOOL 3 - RICERCA & FILTRI
# ---------------------------------------------------

elif page.startswith("3"):
    st.title("Ricerca & Filtri")

    col1, col2, col3 = st.columns(3)

    with col1:
        vendor_filter = st.text_input("Fornitore contiene")

    with col2:
        status_filter = st.selectbox("Status", ["", "NEW", "EMAILED"])

    with col3:
        min_total = st.number_input("Totale minimo", 0.0)

    filtered = df.copy()

    if vendor_filter:
        filtered = filtered[filtered["vendor"].str.contains(vendor_filter, case=False)]

    if status_filter:
        filtered = filtered[filtered["status"] == status_filter]

    if min_total > 0:
        filtered = filtered[filtered["total"] >= min_total]

    st.write(f"Risultati trovati: {len(filtered)}")
    st.dataframe(filtered, use_container_width=True)

# ---------------------------------------------------
# TOOL 4 - EMAIL MOCK
# ---------------------------------------------------

else:
    st.title("Email semi-automatiche (UX Simulation)")

    df_view = df.copy()
    df_view.insert(0, "select", False)

    edited = st.data_editor(
        df_view,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "select": st.column_config.CheckboxColumn("Seleziona")
        }
    )

    selected = edited[edited["select"] == True].drop(columns=["select"])

    st.write(f"Selezionate: {len(selected)}")

    subject = st.text_input("Oggetto", "Richiesta informazioni documento")
    body = st.text_area(
        "Testo email",
        "Ciao {{vendor}},\n\nTi scrivo in merito al documento {{uniqueKey}} del {{date}}.\n\nGrazie."
    )

    if len(selected) > 0:
        first = selected.iloc[0].to_dict()

        preview = body \
            .replace("{{vendor}}", first["vendor"]) \
            .replace("{{uniqueKey}}", first["uniqueKey"]) \
            .replace("{{date}}", first["date"])

        st.subheader("Preview email")
        st.code(preview)

        if st.button("Simula invio email", type="primary"):
            st.success("Email inviate (simulazione)")
