import pandas as pd
import streamlit as st
from openai import OpenAI

# ==========================================
# 1. NASTAVENÍ APLIKACE A API
# ==========================================
st.set_page_config(page_title="AI Metodik (Plánovač)", page_icon="🧠", layout="centered")
st.title("🧠 AI Metodik: Plánovač hodin")
st.markdown("Nahrajte Excel z **AI Školního Inspektora** a nechte si analyzovat třídu.")

st.sidebar.markdown("### ⚙️ Nastavení API")
klic_ok = False

if "api_klic" in st.session_state and st.session_state.api_klic:
    api_klic = st.session_state.api_klic
    model_ai = st.session_state.get("model_ai", "llama-3.3-70b-versatile")
    base_url = "https://api.groq.com/openai/v1" if api_klic.startswith("gsk_") else "https://api.openai.com/v1"
    klic_ok = True
    st.sidebar.success("✅ API klíč je sdílen z Hlavního rozcestníku.")
else:
    api_klic = st.sidebar.text_input("🔑 Groq / OpenAI API klíč:", type="password")

    # Pro zjednodušení používáme v ukázce rovnou OpenAI formát (kompatibilní s Groq)
    if api_klic.startswith("gsk_"):
        base_url = "https://api.groq.com/openai/v1"
        model_ai = "llama-3.3-70b-versatile"
    else:
        base_url = "https://api.openai.com/v1"
        model_ai = "gpt-4o-mini"

# INICIALIZACE POČÍTADLA
if "spotrebovane_tokeny" not in st.session_state: 
    st.session_state.spotrebovane_tokeny = 0

st.sidebar.markdown("---")
token_metric_container = st.sidebar.empty()

def update_token_ui():
    token_metric_container.metric(
        "🪙 Spotřebované tokeny", 
        f"{st.session_state.spotrebovane_tokeny:,}".replace(",", " ")
    )

update_token_ui()
st.sidebar.caption("Počítá se vstupní kontext i odpověď modelu.")

# ==========================================
# 2. NAHRÁNÍ SOUBORU
# ==========================================
# OPRAVA 1: Povolujeme POUZE xlsx, protože spoléháme na listy
nahrany_soubor = st.file_uploader("📥 Nahrajte hodnoceni.xlsx", type=["xlsx"])

# OPRAVA 2: Inicializace paměti pro uložení výsledku před stažením
if "vysledek_metodika" not in st.session_state:
    st.session_state.vysledek_metodika = ""

if nahrany_soubor and api_klic:
    try:
        df = pd.read_excel(nahrany_soubor, sheet_name='Hodnocení')
        
        nacteny_kontext = ""
        try:
            df_kontext = pd.read_excel(nahrany_soubor, sheet_name='Kontext')
            nacteny_kontext = "PŮVODNÍ KONTEXT ÚKOLU:\n"
            for index, row in df_kontext.iterrows():
                nacteny_kontext += f"--- {row['Klíč']} ---\n{row['Hodnota']}\n\n"
            st.success("🤖 Úspěšně načteno hodnocení žáků i původní zadání testu.")
        except Exception:
            st.warning("⚠️ Načteny pouze výsledky. Původní zadání nebylo v souboru nalezeno.")

        if "Zpětná vazba" not in df.columns:
            st.error("❌ Soubor neobsahuje sloupec 'Zpětná vazba'.")
        else:
            MAX_CHARS = 40_000 
            vsechny_vazby = "\n---\n".join(df["Zpětná vazba"].dropna().astype(str)).strip()
            
            # OPRAVA 3: Kontrola, zda vůbec máme nějaká data
            if not vsechny_vazby:
                st.error("❌ Sloupec se zpětnou vazbou je prázdný. Není co analyzovat.")
            else:
                if len(vsechny_vazby) > MAX_CHARS:
                    st.warning(f"⚠️ Soubor je velmi rozsáhlý. Bude analyzována pouze část (prvních {MAX_CHARS} znaků).")
                    vsechny_vazby = vsechny_vazby[:MAX_CHARS] + "\n... [ZBYTEK ZKRÁCEN]"

                if st.button("🔮 Analyzovat třídu a navrhnout další hodinu", type="primary"):
                    client = OpenAI(api_key=api_klic, base_url=base_url)
                    
                    system_prompt = """Jsi profesionální školní metodik. Tvá odpověď nesmí obsahovat žádnou zdvořilostní omáčku.
Dostaneš seznam chyb, které udělali žáci. 

TVÉ ÚKOLY:
1. 📊 DIAGNOSTIKA (Bullet points): Identifikuj 3 nejčastější koncepční chyby. IGNORUJ jména žáků. Shrň pouze jevy.
2. 🚀 AKČNÍ PLÁN NA PŘÍŠTĚ (Warm-up): Navrhni konkrétní 5minutovou aktivitu na začátek další hodiny. Dej jasný příklad na tabuli/projektor.
3. 💡 TIP PRO UČITELE: Jedna krátká věta, jak chybu jednoduše vysvětlit.

FORMÁT:
Použij formátování Markdown. Buď věcný a stručný."""

                    obsah_pro_ai = f"{nacteny_kontext}\nZPĚTNÉ VAZBY OD ŽÁKŮ:\n{vsechny_vazby}"

                    with st.spinner(f"AI analyzuje data..."):
                        try:
                            resp = client.chat.completions.create(
                                model=model_ai,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": obsah_pro_ai}
                                ],
                                temperature=0.3 
                            )

                            u = getattr(resp, 'usage', None)
                            if u:
                                st.session_state.spotrebovane_tokeny += getattr(u, 'total_tokens', getattr(u, 'prompt_tokens', 0) + getattr(u, 'completion_tokens', 0))
                                update_token_ui()
                            
                            # Uložení do session state, aby to přežilo refresh po stažení
                            st.session_state.vysledek_metodika = resp.choices[0].message.content
                            
                        except Exception as e:
                            st.error(f"❌ Chyba komunikace s API: {str(e)}")

                # Zobrazení a stažení výsledku POUZE pokud už je v paměti
                if st.session_state.vysledek_metodika:
                    st.markdown("### 📊 Výsledek analýzy a plán na další hodinu")
                    st.markdown(st.session_state.vysledek_metodika)
                    
                    st.download_button(
                        label="📥 Stáhnout přípravu na hodinu (.md)",
                        data=st.session_state.vysledek_metodika,
                        file_name="priprava_dalsi_hodina.md",
                        mime="text/markdown"
                    )

    except Exception as e:
        st.error(f"❌ Nelze přečíst soubor: {str(e)}. Ujistěte se, že nahráváte platný Excel.")
elif nahrany_soubor and not api_klic:
    st.warning("👈 Nezapomeňte vložit API klíč v levém panelu.")