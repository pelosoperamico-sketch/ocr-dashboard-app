import streamlit as st
import pandas as pd
import random
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="OCR Dashboard UX", layout="wide")

# ---------------------------------------------------
# CSS: menu sidebar + top-right button + spacing
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
        margin: 0.55rem 0;
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

      /* leggero spacing sopra il contenuto principale */
      .block-container { padding-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# Rilevazione device (mobile vs desktop) - robusta per iOS/Streamlit Cloud
# ---------------------------------------------------
def detect_is_mobile() -> bool:
    if "is_mobile" in st.session_state:
        return st.session_state.is_mobile

    qp_val = st.query_params.get("is_mobile", None)
    if qp_val is not None:
        st.session_state.is_mobile = (str(qp_val) == "1")
        return st.session_state.is_mobile

    components.html(
        """
        <script>
        (function() {
          try {
            const ua = (navigator.userAgent || navigator.vendor || window.opera || "").toLowerCase();
            const isMobileUA = /android|iphone|ipad|ipod|iemobile|blackberry|opera mini/i.test(ua);
            const w = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
            const isMobileW = w <= 768;
            const isMobile = (isMobileUA || isMobileW) ? "1" : "0";
            const topUrl = new URL(window.top.location.href);
            if (!topUrl.searchParams.has("is_mobile")) {
              topUrl.searchParams.set("is_mobile", isMobile);
              window.top.location.replace(topUrl.toString());
            }
          } catch (e) {}
        })();
        </script>
        """,
        height=0
    )

    return False

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

if st.sidebar.button("🔄 Reset rilevamento dispositivo"):
    st.query_params.pop("is_mobile", None)
    st.session_state.pop("is_mobile", None)
    st.rerun()

page = st.session_state.page

# ---------------------------------------------------
# Utilities (modal helpers)
# ---------------------------------------------------
def open_modal(name: str):
    st.session_state[name] = True

def close_modal(name: str):
    st.session_state[name] = False

if "show_alt_menu" not in st.session_state:
    st.session_state.show_alt_menu = False
if "modal_manual" not in st.session_state:
    st.session_state.modal_manual = False
if "modal_mail" not in st.session_state:
    st.session_state.modal_mail = False

# ---------------------------------------------------
# TOOL 1 - OCR MOCK (Mobile: camera only / Desktop: upload only)
# + Top-right "Fattura alternativa" + modali
# ---------------------------------------------------
if page == "OCR":
    # Header con bottone in alto a destra
    left, right = st.columns([0.72, 0.28], vertical_alignment="top")
    with left:
        st.title("Scanner OCR (Simulazione UX)")
        st.caption("📱 Da mobile: scatta una foto. 💻 Da PC: carica un file dal computer.")
    with right:
        st.write("")  # spazio
        st.write("")  # spazio
        if st.button("🧾 Fattura alternativa", type="secondary", use_container_width=True):
            st.session_state.show_alt_menu = not st.session_state.show_alt_menu

    # Menu "esploso" con 2 opzioni
    if st.session_state.show_alt_menu:
        with st.container(border=True):
            st.markdown("**Scegli un'opzione**")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✍️ Carica manualmente", use_container_width=True):
                    st.session_state.show_alt_menu = False
                    open_modal("modal_manual")
                    st.rerun()
            with c2:
                if st.button("📩 Inoltra via mail", use_container_width=True):
                    st.session_state.show_alt_menu = False
                    open_modal("modal_mail")
                    st.rerun()

    st.divider()

    # --- MODAL 1: Carica manualmente ---
    if st.session_state.modal_manual:
        with st.modal("Carica manualmente"):
            st.write("Compila i dati della fattura (simulazione).")

            col1, col2 = st.columns(2)
            with col1:
                vendor = st.text_input("Fornitore *", placeholder="Es. ABC Srl")
                invoice_no = st.text_input("Numero fattura *", placeholder="Es. 2026/001")
                email = st.text_input("Email fornitore", placeholder="Es. info@fornitore.it")
            with col2:
                date = st.date_input("Data documento *")
                total = st.number_input("Totale (€) *", min_value=0.0, step=1.0, format="%.2f")
                status = st.selectbox("Stato", ["NEW", "EMAILED"], index=0)

            notes = st.text_area("Note", placeholder="Inserisci eventuali note...")

            st.write("")
            a, b = st.columns(2)
            with a:
                if st.button("Annulla", use_container_width=True):
                    close_modal("modal_manual")
                    st.rerun()
            with b:
                if st.button("Salva (mock)", type="primary", use_container_width=True):
                    if not vendor.strip() or not invoice_no.strip() or total <= 0:
                        st.error("Compila i campi obbligatori: Fornitore, Numero fattura e Totale > 0.")
                    else:
                        new_row = {
                            "uniqueKey": f"MAN-{random.randint(2000,3000)}",
                            "vendor": vendor.strip(),
                            "date": date.strftime("%d/%m/%Y"),
                            "total": float(total),
                            "status": status,
                            "email": email.strip() if email else "info@example.com"
                        }
                        st.session_state.data = pd.concat(
                            [st.session_state.data, pd.DataFrame([new_row])],
                            ignore_index=True
                        )
                        close_modal("modal_manual")
                        st.success("Fattura salvata (mock).")
                        st.rerun()

    # --- MODAL 2: Inoltra via mail ---
    if st.session_state.modal_mail:
        with st.modal("Inoltra via mail"):
            st.markdown("inoltra alla seguente mail le fatture che ti interessa scannerizzare: **prova@streamlit.it**")
            st.write("")
            if st.button("Chiudi", use_container_width=True):
                close_modal("modal_mail")
                st.rerun()

    # Journey acquisizione documento
    st.markdown("### 1) Acquisisci documento")

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
            if st.button("Reset estrazione", use_container_width=True):
                st.session_state.last_extracted = None
                st.rerun()

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
