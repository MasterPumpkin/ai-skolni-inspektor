import pandas as pd
import streamlit as st
import io
from openai import OpenAI

# ==========================================
# 1. NASTAVENÍ APLIKACE A PAMĚTI
# ==========================================
st.set_page_config(page_title="AI Tvůrce Kvízů", page_icon="🕹️", layout="centered")
st.title("🕹️ AI Tvůrce Kvízů")
st.markdown("Vygenerujte test na míru chybám vaší třídy pro Kahoot, Quizlet nebo Moodle.")

if "spotrebovane_tokeny" not in st.session_state: 
    st.session_state.spotrebovane_tokeny = 0
if "vysledek_kvizu" not in st.session_state:
    st.session_state.vysledek_kvizu = ""
if "cilova_platforma" not in st.session_state:
    st.session_state.cilova_platforma = "Kahoot!"

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

    if api_klic.startswith("gsk_"):
        base_url = "https://api.groq.com/openai/v1"
        model_ai = "llama-3.3-70b-versatile"
    else:
        base_url = "https://api.openai.com/v1"
        model_ai = "gpt-4o-mini"

st.sidebar.markdown("---")
token_metric_container = st.sidebar.empty()

def update_token_ui():
    token_metric_container.metric(
        "🪙 Spotřebované tokeny", 
        f"{st.session_state.spotrebovane_tokeny:,}".replace(",", " ")
    )

update_token_ui()

# PŘIDÁNO: Funkce, která vymaže starý výsledek při jakékoliv změně nastavení
def reset_vysledku():
    st.session_state.vysledek_kvizu = ""

# ==========================================
# 2. UI - PŘEPÍNAČE A VÝBĚR PLATFORMY
# ==========================================
platforma = st.radio(
    "Cílová platforma pro export:", 
    ["Kahoot!", "Quizlet / Blooket", "Moodle (Aiken formát)"], 
    horizontal=True,
    on_change=reset_vysledku # PŘIDÁNO: Spustí smazání paměti při překliknutí
)
st.session_state.cilova_platforma = platforma

st.markdown("---")
rezim = st.radio(
    "Režim analýzy dat:",
    ["🟢 Rychlé opáčko (Nahrát .md z Metodika)", "🔴 Chytáky na tělo (Nahrát .xlsx z Inspektora)"],
    help="Rychlé opáčko spotřebuje méně tokenů. Chytáky na tělo projdou práce všech žáků a použijí jejich omyly jako špatné odpovědi.",
    on_change=reset_vysledku # PŘIDÁNO: Spustí smazání paměti při překliknutí
)

obsah_pro_ai = ""
MAX_CHARS = 40_000 

# ==========================================
# 3. NAHRÁNÍ A ZPRACOVÁNÍ SOUBORU PODLE REŽIMU
# ==========================================
if "🟢" in rezim:
    nahrany_soubor = st.file_uploader("📥 Nahrajte přípravu na hodinu (.md nebo .txt)", type=["md", "txt"])
    if nahrany_soubor:
        obsah = nahrany_soubor.getvalue().decode("utf-8")
        if not obsah.strip():
            st.error("❌ Soubor je prázdný.")
        else:
            obsah_pro_ai = obsah[:MAX_CHARS]
            st.success("✅ Metodická příprava načtena.")
elif "🔴" in rezim:
    nahrany_soubor = st.file_uploader("📥 Nahrajte původní hodnocení žáků (.xlsx)", type=["xlsx"])
    if nahrany_soubor:
        try:
            df = pd.read_excel(nahrany_soubor, sheet_name='Hodnocení')
            nacteny_kontext = ""
            try:
                df_kontext = pd.read_excel(nahrany_soubor, sheet_name='Kontext')
                nacteny_kontext = "PŮVODNÍ ZADÁNÍ ÚKOLU:\n"
                for index, row in df_kontext.iterrows():
                    nacteny_kontext += f"--- {row['Klíč']} ---\n{row['Hodnota']}\n\n"
            except Exception:
                pass 
                
            if "Zpětná vazba" not in df.columns:
                st.error("❌ Excel neobsahuje sloupec 'Zpětná vazba'.")
            else:
                vsechny_vazby = "\n---\n".join(df["Zpětná vazba"].dropna().astype(str)).strip()
                if not vsechny_vazby:
                    st.error("❌ Sloupec se zpětnou vazbou je prázdný.")
                else:
                    if len(vsechny_vazby) > MAX_CHARS:
                        vsechny_vazby = vsechny_vazby[:MAX_CHARS] + "\n... [ZBYTEK ZKRÁCEN]"
                    obsah_pro_ai = f"{nacteny_kontext}\nCHYBY, KTERÉ DĚLALI ŽÁCI:\n{vsechny_vazby}"
                    st.success("✅ Omyly žáků načteny.")
        except Exception as e:
            st.error(f"❌ Chyba čtení Excelu: {str(e)}")

# ==========================================
# 4. VOLÁNÍ AI A GENEROVÁNÍ KVÍZU
# ==========================================
if obsah_pro_ai and api_klic:
    if st.button("🚀 Vygenerovat exportní soubor", type="primary"):
        client = OpenAI(api_key=api_klic, base_url=base_url)
        
        if platforma == "Kahoot!":
            system_prompt = """Jsi generátor testů. Tvým jediným úkolem je vrátit čistý CSV text (hodnoty oddělené středníkem). 
Nevygeneruj vůbec nic jiného. Nechci žádný úvodní text, ani markdown bloky (nepiš ```csv).
Vygeneruj 5-8 otázek na základě dodaných dat. Pokud jsou v datech specifické chyby žáků, použij je jako špatné odpovědi (distraktory).
Záhlaví tabulky MUSÍ vypadat přesně takto:
Question;Answer 1;Answer 2;Answer 3;Answer 4;Time limit (sec);Correct answer
Příklad řádku: Kolik je 2+2?;3;4;5;22;20;2"""

        elif platforma == "Quizlet / Blooket":
            system_prompt = """Jsi generátor kartiček. Tvým jediným úkolem je vrátit čistý CSV text (hodnoty oddělené středníkem).
Nevygeneruj vůbec nic jiného. Nechci žádný úvodní text, ani markdown bloky.
Vygeneruj 10 pojmů a k nim správné definice na základě dodaných dat. Zaměř se na chyby žáků.
Záhlaví tabulky MUSÍ vypadat přesně takto:
Pojem;Definice
Příklad řádku: Fotosyntéza;Proces, při kterém rostliny tvoří kyslík."""

        else: # Moodle (Aiken)
            system_prompt = """Jsi generátor testů pro Moodle. Tvým jediným úkolem je vrátit čistý text ve formátu Aiken.
Nevygeneruj vůbec nic jiného než tento text. Nechci žádný úvodní text, ani markdown bloky (nepiš ```txt).
Vygeneruj 5-8 otázek s výběrem ze 4 možností (A, B, C, D) na základě dodaných dat. Pokud jsou v datech specifické chyby žáků, použij je jako špatné odpovědi (distraktory).

Pravidla formátu Aiken:
1. Otázka musí být na jednom řádku.
2. Každá odpověď musí začínat velkým písmenem, závorkou a mezerou (A) , B) , C) , D) ).
3. Hned pod odpověďmi musí být řádek začínající přesně "ANSWER: " a velkým písmenem správné odpovědi.
4. Mezi jednotlivými otázkami je jeden prázdný řádek.

Příklad:
Kde udělala většina třídy chybu při definici for cyklu?
A) Zapomněli dvojtečku na konci řádku
B) Špatně odsazovali blok kódu
C) Použili kulaté závorky místo hranatých
D) Zapomněli klíčové slovo in
ANSWER: A"""

        with st.spinner(f"AI generuje strukturovaný kvíz pro {platforma}..."):
            try:
                resp = client.chat.completions.create(
                    model=model_ai,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": obsah_pro_ai}
                    ],
                    temperature=0.2 
                )
                
                u = getattr(resp, 'usage', None)
                if u:
                    st.session_state.spotrebovane_tokeny += getattr(u, 'total_tokens', getattr(u, 'prompt_tokens', 0) + getattr(u, 'completion_tokens', 0))
                    update_token_ui()
                
                surovy_text = resp.choices[0].message.content.strip()
                
                if surovy_text.startswith("```"):
                    radky = surovy_text.split("\n")
                    surovy_text = "\n".join(radky[1:-1]).strip()
                
                st.session_state.vysledek_kvizu = surovy_text
                
            except Exception as e:
                st.error(f"❌ Chyba komunikace s API: {str(e)}")

# ==========================================
# 5. ZOBRAZENÍ A STAŽENÍ
# ==========================================
if st.session_state.vysledek_kvizu:
    st.markdown(f"### 🎉 Hotovo! Kvíz připraven pro import do {st.session_state.cilova_platforma}")
    
    if st.session_state.cilova_platforma == "Moodle (Aiken formát)":
        st.text_area("Náhled Aiken formátu (čistý text):", st.session_state.vysledek_kvizu, height=300)
        st.download_button(
            label="📥 Stáhnout soubor pro Moodle (.txt)",
            data=st.session_state.vysledek_kvizu.encode('utf-8-sig'), 
            file_name="moodle_aiken_import.txt",
            mime="text/plain"
        )
        st.info("💡 **Návod pro Moodle:** Jděte do své banky úloh v Moodlu, klikněte na 'Import', vyberte formát **Aiken** a nahrajte tento stažený `.txt` soubor.")
        
    else: 
        try:
            df_nahled = pd.read_csv(io.StringIO(st.session_state.vysledek_kvizu), sep=";")
            st.dataframe(df_nahled, use_container_width=True)
        except Exception:
            st.warning("Náhled tabulky se nezdařil (AI nedodrželo přesný počet sloupců), ale soubor můžete přesto stáhnout a zkusit:")
            st.text(st.session_state.vysledek_kvizu)

        jmeno_souboru = "kahoot_import.csv" if st.session_state.cilova_platforma == "Kahoot!" else "quizlet_import.csv"
        
        st.download_button(
            label=f"📥 Stáhnout soubor pro {st.session_state.cilova_platforma} (.csv)",
            data=st.session_state.vysledek_kvizu.encode('utf-8-sig'),
            file_name=jmeno_souboru,
            mime="text/csv"
        )
        st.info(f"💡 **Návod pro {st.session_state.cilova_platforma}:** Stáhněte soubor. Běžte na web platformy, vytvořte nový kvíz a klikněte na 'Import from spreadsheet' nebo 'Importovat data'.")

elif not api_klic:
    st.warning("👈 Nezapomeňte vložit API klíč v levém panelu.")