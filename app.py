import streamlit as st
import pandas as pd
import random
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Smart Document Manager",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# STILE CUSTOM (UX più moderna)
# ---------------------------------------------------

st.markdown("""
<style>
.main {
    padding-top: 1rem;
}
.block-container {
    padding-top: 1rem;
}
.card {
    padding: 20px;
    border-radius: 14px;
    background-color: #111827;
    border: 1px solid #1f2937;
}
.badge-new {
    background-color: #f59e0b;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    color: white;
}
.badge-emailed {
    background-color: #10b981;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# MOCK DATA
# ---------------------------------------------------

def generate_mock_data(n=30):
    vendors = ["ABC Srl", "Tech Supply", "Global Parts", "Fast Logistics", "Blue Energy"]
    statuses = ["NEW", "EMAILED"]

    rows = []
    for i in range(n):
        rows.append({
            "uniqueKey": f"DOC-{1000+i}",
            "vendor": random.choice(vendors),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "total": round(random.uniform(50, 1500), 2),
            "status": random.choice(statuses),
            "email": "info@example.com"
        })
    return pd.DataFrame(rows)

if "data" not in st.session_state:
    st.session_state.data = generate_mock_data()

df = st.session_state.data

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

st.markdown("## 📊 Smart Document Manager")
st.caption("OCR • Dashboard • Ricerca • Email Automation")

st.divider()

# ---------------------------------------------------
# NAV
# ---------------------------------------------------

page = st.segmented_control(
    "Seleziona modulo",
    ["OCR", "Dashboard", "Ricerca", "Email"],
    default="Dashboard"
)

# ---------------------------------------------------
# OCR
# ---------------------------------------------------

if page == "OCR":
    st.subheader("📷 Scanner Documenti")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded = st.file_uploader("Carica documento", type=["jpg", "jpeg", "png"])

    with col2:
        camera = st.camera_input("Oppure scatta foto")

    image_bytes = None
    if uploaded:
        image_bytes = uploaded.read()
    elif camera:
        image_bytes = camera.getvalue()

    if image_bytes:
        st.image(image_bytes, use_container_width=True)

        if st.button("Avvia scansione", type="primary", use_container_width=True):
            with st.spinner("Analisi documento in corso..."):
                extracted = {
                    "vendor": "ABC Srl",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "total": 349.90
                }

                st.success("Documento analizzato")

                colA, colB, colC = st.columns(3)
                colA.metric("Fornitore", extracted["vendor"])
                colB.metric("Data", extracted["date"])
                colC.metric("Totale", f"{extracted['total']} €")

                if st.button("Salva documento", use_container_width=True):
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
                    st.success("Documento salvato")

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

elif page == "Dashboard":
    st.subheader("📈 Overview")

    totals = df["total"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Documenti", len(df))
    col2.metric("Fornitori", df["vendor"].nunique())
    col3.metric("Totale €", f"{totals.sum():.2f}")
    col4.metric("Da gestire", (df["status"] == "NEW").sum())

    st.divider()

    st.subheader("Elenco documenti")

    def status_badge(val):
        if val == "NEW":
            return "🟠 NEW"
        return "🟢 EMAILED"

    df_display = df.copy()
    df_display["status"] = df_display["status"].apply(status_badge)

    st.dataframe(df_display, use_container_width=True)

# ---------------------------------------------------
# RICERCA
# ---------------------------------------------------

elif page == "Ricerca":
    st.subheader("🔎 Filtra documenti")

    col1, col2, col3 = st.columns(3)

    with col1:
        vendor_filter = st.text_input("Fornitore")

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

    st.write(f"{len(filtered)} risultati trovati")
    st.dataframe(filtered, use_container_width=True)

# ---------------------------------------------------
# EMAIL
# ---------------------------------------------------

else:
    st.subheader("✉️ Email Automation")

    df_view = df.copy()
    df_view.insert(0, "Seleziona", False)

    edited = st.data_editor(
        df_view,
        use_container_width=True,
        num_rows="fixed"
    )

    selected = edited[edited["Seleziona"] == True].drop(columns=["Seleziona"])

    st.write(f"Documenti selezionati: {len(selected)}")

    subject = st.text_input("Oggetto", "Richiesta informazioni documento")
    body = st.text_area(
        "Messaggio",
        "Ciao {{vendor}},\n\nTi scrivo in merito al documento {{uniqueKey}} del {{date}}.\n\nGrazie."
    )

    if len(selected) > 0:
        first = selected.iloc[0].to_dict()
        preview = body \
            .replace("{{vendor}}", first["vendor"]) \
            .replace("{{uniqueKey}}", first["uniqueKey"]) \
            .replace("{{date}}", first["date"])

        st.subheader("Anteprima")
        st.code(preview)

        if st.button("Invia email", type="primary", use_container_width=True):
            st.success("Email inviate (simulazione)")
