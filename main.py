import io
import json

import docx
import pandas as pd
import pdfplumber
import requests
import streamlit as st
from openai import OpenAI, RateLimitError


# ==========================================
# 1. POMOCNÉ FUNKCE (Čištění a čtení)
# ==========================================
def vycisti_notebook(obsah_json) -> str:
    text_k_analyze = ""
    for bunka in obsah_json.get("cells", []):
        if bunka["cell_type"] in ["code", "markdown"]:
            zdroj = "".join(bunka["source"]).strip()
            if zdroj:
                typ = "💻 KÓD" if bunka["cell_type"] == "code" else "📝 TEXT"
                text_k_analyze += f"--- {typ} ---\n{zdroj}\n\n"
    return text_k_analyze

def precti_obsah_souboru(nahrany_soubor) -> str:
    jmeno = nahrany_soubor.name.lower()
    try:
        if jmeno.endswith('.ipynb'):
            return vycisti_notebook(json.loads(nahrany_soubor.getvalue().decode("utf-8")))
        elif jmeno.endswith('.pdf'):
            with pdfplumber.open(nahrany_soubor) as pdf:
                return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        elif jmeno.endswith('.docx'):
            doc = docx.Document(nahrany_soubor)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return nahrany_soubor.getvalue().decode("utf-8")
    except Exception as e:
        return f"CHYBA ČTENÍ: {str(e)}"

def spust_python_kod(kod: str) -> str:
    url = "https://emkc.org/api/v2/piston/execute"
    payload = {"language": "python", "version": "3.10", "files": [{"name": "student.py", "content": kod}]}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.json().get("run", {}).get("output", "Bez výstupu.")
    except: return "Chyba sandboxu."

nastroj_python = {
    "type": "function",
    "function": {"name": "spust_python_kod", "description": "Spustí Python kód.", "parameters": {"type": "object", "properties": {"kod": {"type": "string"}}, "required": ["kod"]}}
}

# ==========================================
# 2. STAV APLIKACE (SESSION STATE)
# ==========================================
for klic in ["gen_zadani", "gen_reseni", "gen_instrukce", "posledni_analyza", "posledni_analyza_vysledek"]:
    if klic not in st.session_state: st.session_state[klic] = ""
if "hotove_vysledky" not in st.session_state: st.session_state.hotove_vysledky = []
if "spotrebovane_tokeny" not in st.session_state: st.session_state.spotrebovane_tokeny = 0

# ==========================================
# 3. UI - BOČNÍ PANEL (VÝBĚR MODELU A TOKENY)
# ==========================================
st.set_page_config(page_title="AI Školní Inspektor", page_icon="🎓", layout="wide")
st.title("🎓 AI Školní Inspektor v3.2")

st.sidebar.markdown("### ⚙️ Nastavení AI")
poskytovatel = st.sidebar.selectbox("Poskytovatel AI:", ["Groq (Zdarma/Bleskový)", "OpenAI (Placené/Nejchytřejší)", "Ollama (Lokální zdarma)"])

klic_ok = False
if poskytovatel == "Groq (Zdarma/Bleskový)":
    api_klic = st.sidebar.text_input("🔑 Groq API klíč:", type="password")
    base_url = "https://api.groq.com/openai/v1"
    model_ai = st.sidebar.selectbox("Model:", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
    if api_klic.startswith("gsk_"): klic_ok = True

elif poskytovatel == "OpenAI (Placené/Nejchytřejší)":
    api_klic = st.sidebar.text_input("🔑 OpenAI API klíč:", type="password")
    base_url = "https://api.openai.com/v1"
    model_ai = st.sidebar.selectbox("Model:", ["gpt-4o-mini", "gpt-4o"])
    if api_klic.startswith("sk-"): klic_ok = True

else: # Ollama
    api_klic = "ollama"
    base_url = "http://localhost:11434/v1"
    model_ai = st.sidebar.text_input("Název lokálního modelu:", value="llama3.1")
    klic_ok = True
    st.sidebar.warning("⚠️ Pozor: Ollama funguje pouze, pokud tuto aplikaci spouštíte lokálně na svém PC. Z cloudu se k vašemu počítači nepřipojí.")

st.sidebar.markdown("---")
st.sidebar.metric("🪙 Spotřebované tokeny", f"{st.session_state.spotrebovane_tokeny:,}".replace(",", " "))
st.sidebar.caption("Počítá se text zadání i odpovědi modelu. (Ollama tokeny nevrací).")

# --- Navigace pro ztracené uživatele ---
if not klic_ok:
    st.info("👈 Vítejte! Pro zpřístupnění všech funkcí rozbalte boční panel (šipkou vlevo nahoře) a zadejte svůj API klíč pro vybraného poskytovatele.")

zalozka_priprava, zalozka_hodnoceni, zalozka_nahled, zalozka_napoveda = st.tabs(["🪄 1. Příprava", "🚀 2. Hodnocení", "🕵️ 3. Náhled", "❓ 4. Návod a API klíče"])

# ------------------------------------------
# ZÁLOŽKA 1: PŘÍPRAVA
# ------------------------------------------
with zalozka_priprava:
    ucitelsky_soubor = st.file_uploader("Nahrajte VZOROVÉ řešení (učitel)", type=["ipynb", "docx", "pdf", "py", "txt"])
    if st.button("✨ Vygenerovat kritéria z mého souboru", type="primary"):
        if not klic_ok or not ucitelsky_soubor: st.warning("Chybí správný klíč nebo soubor.")
        else:
            client = OpenAI(api_key=api_klic, base_url=base_url)
            obsah = precti_obsah_souboru(ucitelsky_soubor)
            with st.spinner(f"AI ({model_ai}) studuje vaše materiály..."):
                try:
                    resp = client.chat.completions.create(
                        model=model_ai,
                        messages=[{"role": "system", "content": "Vytvoř 3 sekce uvozené ###ZADANI###, ###RESENI### a ###INSTRUKCE### pro AI opravovače."}, {"role": "user", "content": obsah}]
                    )
                    
                    # Přičtení tokenů
                    if hasattr(resp, 'usage') and resp.usage:
                        st.session_state.spotrebovane_tokeny += resp.usage.total_tokens

                    txt = resp.choices[0].message.content or ""
                    try:
                        st.session_state.gen_zadani = txt.split("### ZADANI ###")[1].split("### RESENI ###")[0].strip()
                        st.session_state.gen_reseni = txt.split("### RESENI ###")[1].split("### INSTRUKCE ###")[0].strip()
                        st.session_state.gen_instrukce = txt.split("### INSTRUKCE ###")[1].strip()
                        st.success("Kritéria připravena!")
                    except: st.text_area("Hrubý výstup (model nedodržel formát):", txt)
                except Exception as e: st.error(f"Chyba komunikace s API: {str(e)}")

# ------------------------------------------
# ZÁLOŽKA 2: HODNOCENÍ
# ------------------------------------------
with zalozka_hodnoceni:
    col1, col2 = st.columns([1, 1])
    with col1:
        zadani = st.text_area("Zadání pro žáky:", value=st.session_state.gen_zadani, height=100)
        reseni = st.text_area("Vzorové řešení:", value=st.session_state.gen_reseni, height=100)
        instrukce = st.text_area("Kritéria (prompt):", value=st.session_state.gen_instrukce, height=150)
        pouzit_sandbox = st.checkbox("Aktivovat Python Sandbox")
    
    with col2:
        zak_soubory = st.file_uploader("Odevzdané práce", accept_multiple_files=True)
        hotova_jmena = [v["Žák"] for v in st.session_state.hotove_vysledky]
        
        c1, c2, c3 = st.columns(3)
        btn_test = c1.button("🧪 Test (1 žák)")
        btn_start = c2.button("🚀 Spustit / Pokračovat", type="primary")
        btn_reset = c3.button("🔄 Začít znovu (smazat)")
        btn_stop = st.button("🛑 Nouzově zastavit hodnocení", type="secondary")

        if btn_reset:
            st.session_state.hotove_vysledky = []
            st.session_state.posledni_analyza = ""
            st.session_state.posledni_analyza_vysledek = ""
            st.session_state.spotrebovane_tokeny = 0 # Vyresetujeme i tokeny
            st.rerun()
            
        if btn_stop: st.warning("Systém byl ručně zastaven. Vaše dosavadní výsledky jsou uloženy níže.")

        if btn_test or btn_start:
            if not klic_ok or not zak_soubory: st.error("Chybí správný klíč nebo soubory!")
            else:
                client = OpenAI(api_key=api_klic, base_url=base_url)
                fronta = [zak_soubory[0]] if btn_test else zak_soubory
                prog = st.progress(0)
                status = st.empty()
                
                for idx, soubor in enumerate(fronta):
                    if soubor.name in hotova_jmena and not btn_test:
                        prog.progress((idx+1)/len(fronta))
                        continue
                    
                    status.info(f"Zpracovávám: {soubor.name} (Model: {model_ai})")
                    obsah_zaka = precti_obsah_souboru(soubor)
                    st.session_state.posledni_analyza = obsah_zaka 
                    
                    historie = [
                        {"role": "system", "content": f"Jsi učitel. Zadání: {zadani}\nVzor: {reseni}\nKritéria: {instrukce}\nODPOVÍDEJ JEN:\n📊 Výsledek: [Splněno/Částečně/Nesplněno]\n📝 Zpětná vazba: [2 věty k žákovi]"},
                        {"role": "user", "content": obsah_zaka}
                    ]
                    
                    fin = "" 
                    try:
                        while True:
                            p = {"model": model_ai, "messages": historie, "temperature": 0.0}
                            if pouzit_sandbox: p["tools"] = [nastroj_python]
                            resp = client.chat.completions.create(**p)
                            
                            # Přičtení tokenů (za každý krok smyčky)
                            if hasattr(resp, 'usage') and resp.usage:
                                st.session_state.spotrebovane_tokeny += resp.usage.total_tokens

                            msg = resp.choices[0].message
                            historie.append(msg)
                            
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    res = spust_python_kod(json.loads(tc.function.arguments).get("kod",""))
                                    historie.append({"tool_call_id": tc.id, "role": "tool", "name": tc.function.name, "content": res})
                            else:
                                fin = msg.content
                                break
                                
                        st.session_state.posledni_analyza_vysledek = fin
                        if btn_start: st.session_state.hotove_vysledky.append({"Žák": soubor.name, "Hodnocení": fin})
                            
                    except RateLimitError:
                        st.error("Limit vyčerpán. Počkejte chvíli.")
                        break
                    except Exception as e:
                        st.error(f"Chyba při komunikaci s AI: {str(e)}")
                        break
                        
                    prog.progress((idx+1)/len(fronta))
                
                status.success("Hotovo!")
                if btn_test: st.info("VÝSLEDEK TESTU NAHRÁN V ZÁLOŽCE '3. DETAILNÍ NÁHLED'. Můžete si ho tam zkontrolovat.")

    if st.session_state.hotove_vysledky:
        df = pd.DataFrame(st.session_state.hotove_vysledky)
        st.dataframe(df, width='stretch')
        
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Hodnocení')
                workbook = writer.book
                worksheet = writer.sheets['Hodnocení']
                format_wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                worksheet.set_column('A:A', 30)
                worksheet.set_column('B:B', 80, format_wrap)
            st.download_button("📥 Stáhnout Excel (.xlsx)", data=output.getvalue(), file_name="hodnoceni.xlsx")
        except Exception as e:
            st.warning(f"Nelze vytvořit Excel (chyba: {e}). Zkuste stáhnout obyčejné CSV.")
            st.download_button("📥 Stáhnout CSV", data=df.to_csv(index=False, sep=';', encoding='utf-8-sig'), file_name="hodnoceni.csv")

# ------------------------------------------
# ZÁLOŽKA 3: DETAILNÍ NÁHLED (Side-by-Side)
# ------------------------------------------
with zalozka_nahled:
    if st.session_state.posledni_analyza:
        st.subheader("🕵️ Kontrola posledního zpracovaného žáka")
        c1, c2 = st.columns(2)
        with c1:
            st.info("📄 Co odevzdal žák:")
            st.code(st.session_state.posledni_analyza)
        with c2:
            st.success("🤖 Co na to AI:")
            st.markdown(st.session_state.posledni_analyza_vysledek if st.session_state.posledni_analyza_vysledek else "Zatím nic.")
    else:
        st.write("Zatím nebyl zpracován žádný soubor. Zkuste v záložce Hodnocení kliknout na tlačítko 'Test'.")

# ------------------------------------------
# ZÁLOŽKA 4: NÁPOVĚDA A NÁVOD
# ------------------------------------------
with zalozka_napoveda:
    st.markdown("## 📖 Jak pracovat s AI Školním Inspektorem")
    st.write("Tato aplikace vám ušetří hodiny času při opravování žákovských prací. Aby ale mohla fungovat, potřebuje kousek 'umělé inteligence', kterou jí musíte dodat pomocí tzv. API klíče.")
    
    st.markdown("### 🔑 Kde získat API klíč?")
    
    colA, colB = st.columns(2)
    with colA:
        st.info("**ZDARMA: Groq API (Doporučeno)**")
        st.write("Groq je bleskově rychlý poskytovatel, který nabízí štědré limity pro učitele zcela zdarma.")
        st.markdown("""
        1. Jděte na [console.groq.com](https://console.groq.com/keys).
        2. Přihlaste se (např. přes Google účet).
        3. Klikněte na tlačítko **Create API Key**.
        4. Zkopírujte si vygenerovaný text (začíná na `gsk_`) a vložte ho do levého panelu v této aplikaci.
        """)
        
    with colB:
        st.success("**PLACENÉ: OpenAI API (Nejchytřejší)**")
        st.write("Pokud máte školní účet u OpenAI a nabité kredity, získáte ty nejpřesnější výsledky.")
        st.markdown("""
        1. Jděte na [platform.openai.com](https://platform.openai.com/api-keys).
        2. Přihlaste se.
        3. Klikněte na **Create new secret key**.
        4. Zkopírujte klíč (začíná na `sk-`) a vložte ho do levého panelu vlevo.
        """)

    st.markdown("---")
    st.markdown("### 🚀 Jak hodnotit práce (Krok za krokem)")
    st.markdown("""
    * **Krok 1 (Příprava):** Běžte do záložky 1. Nahrajte **své vlastní** (vzorové) řešení úkolu. Může to být Word, PDF, nebo kód. Klikněte na tlačítko a nechte AI, ať z něj vycucne zadání, správný výsledek a vymyslí kritéria pro hodnocení.
    * **Krok 2 (Kontrola):** Překlikněte se do záložky 2. Zkontrolujte, jestli se vám kritéria líbí. Pokud je chcete přísnější, prostě text přepište.
    * **Krok 3 (Test jednoho žáka):** Do pole vpravo nahrajte soubory od žáků. Klikněte na **🧪 Test (1 žák)**. Aplikace ohodnotí jen prvního ze seznamu.
    * **Krok 4 (Náhled a ladění):** Běžte do záložky 3. Zde uvidíte přesně to, co odevzdal žák a co mu na to řekla AI. Pokud AI hodnotí moc mírně, upravte kritéria v záložce 2.
    * **Krok 5 (Hromadná oprava):** Jste spokojeni? Běžte zpět do záložky 2 a klikněte na **🚀 Spustit / Pokračovat**. AI teď opraví celou třídu a vy si dole stáhnete hotový Excel!
    """)