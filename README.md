# 📘 **TruthLens — Real-Time LLM-Powered Misinformation & Fake News Detector**

A lightweight, fast, and reliable misinformation detection tool powered by OpenRouter LLMs.
TruthLens helps journalists, researchers, and everyday users verify headlines, claims, or full news articles in seconds.

---

## 🔍 **Why TruthLens? (Backstory)**

In today’s digital landscape, misinformation spreads faster than ever — across social media, blogs, and even mainstream news portals. A small digital journalism team (our fictional “client”) approached me to build a tool that:

> “Quickly tells us whether a news article is Real, Fake, Misleading, or Biased — with confidence and evidence.”

TruthLens automates their **initial screening** using NLP preprocessing + modern LLM reasoning.

---

## 🚀 **Core Features**

### ✔ Input Options:

* **Headline or Short Text**
* **Full article URL** (auto-scraping using BeautifulSoup)

### ✔ LLM-Powered Verification:

After preprocessing, the system extracts:

* Key claim
* Label: **Real / Fake / Misleading / Biased**
* Confidence score (0–1)
* Short explanation
* Evidence URLs (trusted external sources)

### ✔ Clean Modern UI (Flask + Bootstrap)

* Color-coded labels

  * 🟢 Real
  * 🔴 Fake
  * 🟡 Misleading
  * 🔵 Biased
* Confidence progress bar
* Collapsible raw LLM JSON
* Mobile-friendly layout

### ✔ Article Scraping:

* Removes ads, scripts, junk HTML
* Extracts main `<article>` content or fallback to `<p>` tags

### ✔ Preprocessing:

* Lowercasing
* Removing HTML, URLs, non-text characters
* Safe text shortening
* Extracting first 2 sentences (claim-focused)

---

## 🧠 **How It Works — Architecture Overview**

```
                      ┌───────────────────────┐
                      │      User Input        │
                      │   (Text or URL)        │
                      └──────────┬────────────┘
                                 │
                     URL?        ▼
                        ┌──────────────────────┐
                        │  Scraper (BeautifulSoup) │
                        │  + Domain Extraction   │
                        └──────────┬────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Preprocessing       │
                     │ clean_text(), extract_lead() │
                     └──────────┬────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    LLM Verifier (OpenRouter) │
                    │    → JSON claim + label     │
                    └──────────┬─────────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │     Flask Frontend       │
                     │  Color-coded results     │
                     │  Evidence + Confidence   │
                     └─────────────────────────┘
```

---

## 🛠 **Tech Stack**

* **Frontend:** Flask + Bootstrap 5
* **Backend:** Python
* **LLM API:** OpenRouter (GPT-4o-mini by default)
* **Scraping:** BeautifulSoup4
* **Environment:** dotenv
* **Deployment:** Works locally or on any VPS/Render/Heroku/Docker

---

## 📦 **Project Structure**

```
truthlens/
│
├── app.py                     # Flask UI
├── requirements.txt
├── README.md
│
├── src/
│   ├── preprocess.py          # text cleaning helpers
│   ├── scrapers.py            # URL scraping
│   └── verify_openrouter.py   # LLM JSON verifier
│
└── .env                       # OPENROUTER_API_KEY
```

---

## ⚙️ **Installation**

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/truthlens.git
cd truthlens
```

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# OR source .venv/bin/activate for Linux/Mac
```

### 3️⃣ Install dependencies

Use the minimal, safe dependencies (no heavy libs):

```bash
pip install -r requirements.txt
```

### 4️⃣ Set your OpenRouter API key

Create a `.env` file:

```
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=gpt-4o-mini
OPENROUTER_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
```

Get your API key from:
🔗 [https://openrouter.ai](https://openrouter.ai)

---

## ▶️ **Running the App**

```bash
python app.py
```

Now open in your browser:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🖼 **Screenshots**

*(Add your project screenshots here)*

```
/screenshots
   homepage.png
   result-page.png
```

---

## 🧩 **LLM JSON Output Format**

The LLM is instructed to return:

```json
{
  "claim": "...",
  "label": "Real|Fake|Misleading|Biased",
  "confidence": 0.0,
  "explanation": "...",
  "evidence_urls": ["...", "..."]
}
```

TruthLens parses this output and displays it cleanly in your UI.

---

## ⚠️ Limitations

* LLM reasoning may hallucinate evidence URLs
* Scraping depends on article HTML quality
* Not a full fact-checking system — this is a **first-stage verifier**
* Requires internet (OpenRouter API)
* No native ML model (LLM-based instead)

---

## 🌱 Future Improvements

* Add Transformer-based offline model (DistilBERT / RoBERTa)
* Fact-check cross-referencing via Google Search API
* Domain credibility scoring
* Highlighting suspicious phrases
* Browser extension
* Model fine-tuning on fake news datasets (LIAR / FakeNewsNet)
* Caching for repeated URLs

---

## 📄 License

MIT License — Free for academic & personal use.

