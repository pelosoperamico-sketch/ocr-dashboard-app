import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="OCR Dashboard UX", layout="wide")

# ---------------------------------------------------
# CSS: menu sidebar a bottoni con più spacing
# ---------------------------------------------------
st.markdown(
    """
    <style>
      /* Più spazio in sidebar */
      section[data-testid="stSidebar"] .block-container{
        padding-top: 1.2rem;
      }

      /* Bottoni del menu: più alti, più spazio tra loro */
      section[data-testid="stSidebar"] div.stButton > button{
        width: 100%;
        text-align: left;
        padding: 0.9rem 1rem;
        margin: 0.45rem 0;       /* spazio tra righe */
        border-radius: 14px;
        border: 1px solid rgba(120,120,120,0.25);
        background: rgba(255,255,255,0.04);
        font-size: 1.05rem;
        line-height: 1.2rem;
      }

      /* Hover */
      section[data-testid="stSidebar"] div.stButton > button:hover{
        border-color: rgba(120,120,120,0.55);
        background: rgba(255,255,255,0.08);
      }

      /* Stile "active" (lo applichiamo con un container + classe) */
      .menu-active {
        border-radius: 16px;
        padding: 2px;
        background: linear-gradient(90deg, rgba(99,102,241,0.35), rgba(16,185,129,0.25));
      }
      .menu-active section[data-testid="stSidebar"] div.stButton > button{
        border-color: rgba(99,102,241,0.55) !important;
        background: rgba(99,102,241,0.12) !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

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
# SIDEBAR NAVIGATION (emoji menu)
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "OCR"

st.sidebar.markdown("## Menu")

# Definisci voci menu (emoji + label)
menu_items = [
    ("OCR", "📷", "Scanner OCR"),
    ("DASH", "📊", "Dashboard"),
    ("SEARCH", "🔎", "Ricerca & Filtri"),
    ("EMAIL", "✉️", "Email semi-automatiche"),
]

# Render menu con più spazio tra righe e "active"
for key, emoji, label in menu_items:
    is_active = (st.session_state.page == key)

    if is_active:
        st.sidebar.markdown('<div class="menu-active">', unsafe_allow_html=True)

    if st.sidebar.button(f"{emoji}  {label}", use_container_width=True, key=f"menu_{key}"):
        st.session_state.page = key
        st.rerun()

    if is_active:
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.divider()

page = st.session_state.page

# ---------------------------------------------------
# TOOL 1 - OCR MOCK
# ---------------------------------------------------
if page == "OCR":
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
elif page == "DASH":
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
elif page == "SEARCH":
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
