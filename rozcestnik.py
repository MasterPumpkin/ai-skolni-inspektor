import streamlit as st

# ==========================================
# HLAVNÍ ROZCESTNÍK (Spouštěcí soubor)
# ==========================================
st.set_page_config(page_title="Školní AI Ekosystém", page_icon="🏫", layout="centered")

# Inicializace globální paměti pro celou aplikaci (napříč záložkami)
if "spotrebovane_tokeny" not in st.session_state:
    st.session_state.spotrebovane_tokeny = 0
if "api_klic" not in st.session_state:
    st.session_state.api_klic = ""
if "model_ai" not in st.session_state:
    st.session_state.model_ai = "llama-3.3-70b-versatile"

st.title("🏫 Školní AI Ekosystém")
st.markdown("""
Vítejte v hlavním řídícím centru vašeho AI asistenta. 
Díky tomuto rozcestníku už **nemusíte zadávat API klíč do každé aplikace zvlášť**. 
Nastavte ho jednou zde a všechny nástroje v levém menu ho začnou automaticky využívat.
""")

# 1. Globální nastavení API
st.sidebar.markdown("### ⚙️ Globální API klíč")
poskytovatel = st.sidebar.selectbox("Poskytovatel AI:", ["Groq (Zdarma/Bleskový)", "OpenAI (Placené/Nejchytřejší)"])

if "Groq" in poskytovatel:
    klic = st.sidebar.text_input("🔑 Groq API klíč:", type="password", value=st.session_state.api_klic if st.session_state.api_klic.startswith("gsk_") else "")
    model = st.sidebar.selectbox("Model:", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
else:
    klic = st.sidebar.text_input("🔑 OpenAI API klíč:", type="password", value=st.session_state.api_klic if st.session_state.api_klic.startswith("sk-") else "")
    model = st.sidebar.selectbox("Model:", ["gpt-4o-mini", "gpt-4o"])

# Uložení do paměti
if klic:
    st.session_state.api_klic = klic
    st.session_state.model_ai = model
    st.sidebar.success("✅ Klíč uložen do globální paměti!")

# 2. Globální statistiky
st.sidebar.markdown("---")
st.sidebar.metric("🪙 Celkem spotřebováno tokenů", f"{st.session_state.spotrebovane_tokeny:,}".replace(",", " "))
st.sidebar.caption("Toto počítadlo se sčítá napříč všemi nástroji v menu.")

# 3. Přehled modulů
st.markdown("---")
st.markdown("### 👈 Vyberte si nástroj v levém panelu")

col1, col2 = st.columns(2)
with col1:
    st.info("**🤖 1. Super Agent (Vše v jednom)**\n\nNahrajte odevzdané testy a nechte si na jedno kliknutí vygenerovat hodnocení, metodiku i kvízy do hotového ZIP archivu.")
    st.success("**🎓 2. AI Inspektor (Opravář)**\n\nSamostatný nástroj pro detailní hromadné hodnocení a bodování studentských prací podle vašich kritérií.")
with col2:
    st.warning("**🧠 3. AI Metodik (Plánovač)**\n\nSamostatný analytik, který vezme chyby třídy z Inspektora a navrhne vám zahřívačku na další hodinu.")
    st.error("**🕹️ 4. AI Kvízovač (Hry)**\n\nVytvoří chytáky do Kahootu, Quizletu nebo test do Moodlu přesně na míru aktuálním chybám vaší třídy.")