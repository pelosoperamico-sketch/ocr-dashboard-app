import streamlit as st
import pandas as pd
import random
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="OCR Dashboard UX", layout="wide")

# ---------------------------------------------------
# CSS: menu sidebar a bottoni con più spacing
# ---------------------------------------------------
st.markdown(
    """
    <style>
      section[data-testid="stSidebar"] .block-container{
        padding-top: 1.2rem;
      }
      section[data-testid="stSidebar"] div.stButton > button{
        width: 100%;
        text-align: left;
        padding: 0.9rem 1rem;
        margin: 0.55rem 0; /* più spazio tra righe */
        border-radius: 14px;
        border: 1px solid rgba(120,120,120,0.25);
        background: rgba(255,255,255,0.04);
        font-size: 1.05rem;
        line-height: 1.2rem;
      }
      section[data-testid="stSidebar"] div.stButton > button:hover{
        border-color: rgba(120,120,120,0.55);
        background: rgba(255,255,255,0.08);
      }
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
# Rilevazione device (mobile vs desktop) via JS
# ---------------------------------------------------
def detect_is_mobile() -> bool:
    """
    Ritorna True se sembra mobile/tablet, False se desktop.
    Usa userAgent nel browser (approccio pratico per Streamlit).
    """
    if "is_mobile" in st.session_state:
        return st.session_state.is_mobile

    # Piccolo componente HTML+JS che scrive un valore in querystring e forza rerun
    # (workaround comune in Streamlit per leggere user agent)
    components.html(
        """
        <script>
        (function() {
          const ua = navigator.userAgent || navigator.vendor || window.opera;
          const isMobile = /android|iphone|ipad|ipod|iemobile|blackberry|opera mini/i.test(ua.toLowerCase());
          const url = new URL(window.location.href);
          // se già impostato, non fare nulla
          if (url.searchParams.get("is_mobile") === null) {
            url.searchParams.set("is_mobile", isMobile ? "1" : "0");
            window.location.replace(url.toString());
          }
        })();
        </script>
        """,
        height=0
    )

    # Leggi query param
    qp = st.query_params
    val = qp.get("is_mobile", None)
    if val is None:
        # primo giro: la pagina verrà ricaricata dal JS
        return False

    st.session_state.is_mobile = (str(val) == "1")
    return st.session_state.is_mobile

is_mobile = detect_is_mobile()

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

menu_items = [
    ("OCR", "📷", "Scanner OCR"),
    ("DASH", "📊", "Dashboard"),
    ("SEARCH", "🔎", "Ricerca & Filtri"),
    ("EMAIL", "✉️", "Email semi-automatiche"),
]

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
st.sidebar.caption(f"Dispositivo rilevato: {'📱 Mobile' if is_mobile else '💻 Desktop'}")

page = st.session_state.page

# ---------------------------------------------------
# TOOL 1 - OCR MOCK (MIGLIORATO)
# - Mobile: SOLO camera_input
# - Desktop: SOLO file_uploader
# ---------------------------------------------------
if page == "OCR":
    st.title("Scanner OCR (Simulazione UX)")
    st.caption("📱 Da mobile: scatta una foto. 💻 Da PC: carica un file dal computer.")

    # Step indicator
    st.markdown("### 1) Acquisisci documento")
    st.write("")

    image_bytes = None
    filename = None

    if is_mobile:
        st.info("Modalità mobile attiva: puoi scattare una foto.")
        cam = st.camera_input("Scatta foto del documento")
        if cam is not None:
            image_bytes = cam.getvalue()
            filename = "camera.jpg"
    else:
        st.info("Modalità desktop attiva: puoi solo caricare un file.")
        up = st.file_uploader("Carica immagine (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if up is not None:
            image_bytes = up.read()
            filename = up.name

    if image_bytes:
        st.image(image_bytes, caption=f"Anteprima — {filename}", use_container_width=True)

        st.markdown("### 2) Estrai dati (simulazione OCR)")
        colA, colB = st.columns([1, 1])

        with colA:
            if st.button("Simula OCR", type="primary", use_container_width=True):
                with st.spinner("Simulazione scansione..."):
                    extracted = {
                        "vendor": "ABC Srl",
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "total": 249.90
                    }
                    st.session_state.last_extracted = extracted
                    st.success("OCR completato (mock)")

        with colB:
            st.button("Reset immagine", use_container_width=True, on_click=lambda: st.session_state.update({"last_extracted": None}))

        extracted = st.session_state.get("last_extracted")
        if extracted:
            st.subheader("Dati estratti")
            st.json(extracted)

            st.markdown("### 3) Salva nel database (mock)")
            if st.button("Simula salvataggio su Sheet", use_container_width=True):
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
        column_config={"select": st.column_config.CheckboxColumn("Seleziona")}
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
        preview = (body
            .replace("{{vendor}}", first["vendor"])
            .replace("{{uniqueKey}}", first["uniqueKey"])
            .replace("{{date}}", first["date"])
        )

        st.subheader("Preview email")
        st.code(preview)

        if st.button("Simula invio email", type="primary"):
            st.success("Email inviate (simulazione)")
