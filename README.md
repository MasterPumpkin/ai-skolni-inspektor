# 🏫 Školní AI Ekosystém

Komplexní webová aplikace vytvořená ve frameworku Streamlit, která slouží učitelům k automatizovanému hodnocení odevzdaných studentských prací, plánování výuky a generování interaktivních kvízů pomocí umělé inteligence (LLM).

Systém je navržen na principech UNIXu – skládá se ze samostatných, úzce specializovaných nástrojů, které si mezi sebou dokážou předávat data (piping), nebo je lze spustit všechny najednou pomocí centrálního Agenta.

## 🧩 Hlavní moduly aplikace

Aplikace se skládá z Hlavního rozcestníku a 4 specializovaných nástrojů (dostupných v levém menu):

### 🤖 Super Agent (Vše v jednom): 
Hlavní asistent. Stačí nahrát odevzdané práce žáků a Agent je automaticky opraví, navrhne metodiku na další hodinu, vytvoří kvízy a vše vám stáhne zabalené v jednom přehledném .zip archivu.

### 🎓 AI Inspektor (Opravář): 
Samostatný nástroj pro detailní hromadné hodnocení a bodování prací. Umožňuje testovat hodnocení nanečisto na jednom žákovi a exportuje výsledky do naformátovaného Excelu (.xlsx).

### 🧠 AI Metodik (Plánovač): 
Analyzuje data z Inspektora. Zjistí nejčastější koncepční chyby třídy a vygeneruje konkrétní 5minutovou "warm-up" aktivitu na začátek další hodiny (ve formátu .md).

### 🕹️ AI Kvízovač (Hry): 
Bere reálné chyby žáků z Excelu a generuje z nich dokonalé "chytáky". Exportuje hotové soubory pro import na jeden klik do platforem Kahoot! (.csv), Quizlet/Blooket (.csv) nebo Moodle (Aiken formát .txt).

## ✨ Klíčové vlastnosti

**🔑 Sdílený API klíč:** Klíč stačí zadat pouze jednou na hlavní stránce (Rozcestníku) a všechny moduly ho budou automaticky využívat.

**🤖 Multi-Model Podpora:** Možnost plynule přepínat mezi Groq (bleskově rychlé, vhodné pro učitele zdarma) a OpenAI (nejpokročilejší modely GPT-4o).

**📄 Univerzální čtečka formátů:** Podpora pro čistý text, zdrojové kódy (.py, .cpp, atd.), Jupyter Notebooky (.ipynb s inteligentním čištěním), Word (.docx) a PDF (.pdf).

**🛡️ Ochrana proti prompt injection:** Systém striktně odděluje instrukce od textu žáka pomocí ochranných značek.

**🪙 Živé počítadlo tokenů:** Neustálý přehled o spotřebovaných tokenech napříč celou aplikací.

## 📁 Struktura složek

Aby aplikace fungovala jako propojený ekosystém (Multipage App), musí být soubory uspořádány takto:

```text
Skolni_AI/
├── rozcestnik.py         <-- Spouštěcí soubor (Hlavní menu)
└── pages/                <-- Složka pro moduly
├── 1_🤖Super_Agent.py
├── 2🎓Inspektor.py
├── 3🧠Metodik.py
└── 4🕹️_Kvizovac.py
```

## 🚀 Jak aplikaci spustit lokálně

Projekt využívá moderní a superrychlý správce balíčků uv.

Naklonujte repozitář:
```bash
git clone https://github.com/MasterPumpkin/ai-skolni-inspektor.git
cd ai-skolni-inspektor
```

Vytvořte virtuální prostředí a nainstalujte závislosti:
```bash
uv sync

nebo ručně přes: uv pip install -r requirements.txt

```

Spusťte Hlavní rozcestník:
```bash
uv run streamlit run rozcestnik.py
```

## ⚠️ Upozornění na ochranu soukromí (GDPR)

Pokud využíváte cloudové modely (Groq, OpenAI), obsah odevzdaných prací se odesílá na servery třetích stran. Dbejte na to, aby žáci do svých prací (v kódu, dokumentech) nevkládali citlivé osobní údaje. 

---

Vytvořeno s ❤️ pro moderní školství, aby učitelé mohli trávit méně času známkováním a více času učením.


