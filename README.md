# 🎓 AI Školní Inspektor

Moderní webová aplikace vytvořená ve frameworku **Streamlit**, která slouží učitelům k automatizovanému a hromadnému hodnocení odevzdaných studentských prací pomocí umělé inteligence (LLM). 

Aplikace umí přečíst vzorové řešení od učitele, sama z něj odvodit hodnotící kritéria a následně podle nich během několika minut zkontrolovat celou třídu.

## ✨ Hlavní funkce

**🤖 Multi-Model Podpora:** Možnost plynule přepínat mezi poskytovateli:
* **Groq:** Bleskově rychlé a pro učitele (v rámci limitů) zdarma.
* **OpenAI:** Přístup k nejpokročilejším modelům (GPT-4o) pro složité úlohy.
* **Ollama:** 100% lokální spuštění bez odesílání dat do cloudu (vyžaduje výkonný HW).

**📄 Univerzální čtečka formátů:** Podpora pro čistý text, zdrojové kódy (`.py`), Jupyter Notebooky (`.ipynb` – s inteligentním čištěním metadat), Word dokumenty (`.docx`) a PDF (`.pdf`).

**🐍 Python Sandbox:** Volitelná možnost nechat AI bezpečně spustit odevzdaný kód žáka a zkontrolovat jeho reálný výstup.

**📊 Profi Export:** Výsledné hodnocení lze stáhnout jako formátovaný sešit Excelu (`.xlsx`) s automatickým zalamováním textu.

**🛡️ Blbuvzdornost a paměť:** Ochrana proti vyčerpání API limitů. Aplikace průběžně ukládá výsledky a umožňuje kdykoliv navázat tam, kde skončila.

**🪙 Počítadlo tokenů:** Živý přehled o spotřebovaných tokenech pro kontrolu nákladů/limitů.

## 🚀 Jak aplikaci spustit lokálně

Projekt využívá moderní a superrychlý správce balíčků [uv](https://github.com/astral-sh/uv).

1. **Naklonujte repozitář:**

```bash
git clone https://github.com/MasterPumpkin/ai-skolni-inspektor.git
cd ai-skolni-inspektor
```

2. **Vytvořte virtuální prostředí a nainstalujte závislosti:**

```bash
uv sync
# nebo ručně přes: uv pip install -r requirements.txt
```
3. **Spusťte aplikaci:**

```bash
uv run streamlit run main.py
```

## 📖 Stručný návod k použití

1. **API Klíč:** V levém bočním panelu vyberte poskytovatele a zadejte svůj API klíč (získaný např. na console.groq.com).

2. **Příprava (Záložka 1):** Nahrajte své vzorové řešení. AI z něj automaticky vygeneruje zadání a hodnotící kritéria (tzv. prompt).

3. **Hodnocení (Záložka 2):** Nahrajte všechny soubory od žáků. Můžete využít tlačítko 🧪 Test (1 žák) pro kalibraci kritérií, nebo rovnou spustit hromadné hodnocení celé třídy.

4. **Náhled (Záložka 3):** Zde si můžete "Side-by-Side" (vedle sebe) porovnat odevzdanou práci konkrétního žáka a verdikt umělé inteligence.

## ⚠️ Upozornění na ochranu soukromí (GDPR)

Pokud využíváte cloudové modely (Groq, OpenAI), obsah odevzdaných prací se odesílá na servery třetích stran. **Dbejte na to, aby žáci do svých prací (v kódu, dokumentech) nevkládali citlivé osobní údaje.** V případě potřeby absolutní diskrétnosti přepněte aplikaci na lokální běh pomocí nástroje Ollama.

---

Vytvořeno s ❤️ pro moderní školství, aby učitelé mohli trávit méně času známkováním a více času učením.

