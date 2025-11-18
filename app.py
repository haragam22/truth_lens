# app.py
from flask import Flask, render_template_string, request, redirect, url_for
from src.scrapers import scrape_url
from src.preprocess import clean_text, extract_lead, safe_shorten
from src.verify_openrouter import verify_article
import os
import json

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TruthLens — LLM Verifier</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { padding-top: 2rem; background: #f8f9fa; }
    .app-card { border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.04); background: #fff; padding: 1.5rem; }
    textarea { resize: vertical; }
    .badge-label { font-size: 1rem; padding: 0.6rem 0.9rem; }
    .evidence a { word-break: break-all; }
    .raw-box { background:#272c34; color:#e6eef8; padding:1rem; border-radius:6px; overflow:auto; }
    .small-muted { color:#6c757d; font-size:0.92rem; }
  </style>
</head>
<body>
<div class="container">
  <div class="row justify-content-center mb-4">
    <div class="col-md-10">
      <div class="d-flex align-items-center mb-3">
        <h1 class="me-3">TruthLens</h1>
        <span class="small-muted">— LLM Verification (OpenRouter)</span>
      </div>

      <div class="app-card">
        <form id="verify-form" method="post" action="/verify" class="row g-3">
          <div class="col-md-3">
            <label class="form-label">Mode</label>
            <select id="mode" name="mode" class="form-select" onchange="onModeChange()">
              <option value="text" {% if mode=='text' %}selected{% endif %}>Headline / Text</option>
              <option value="url" {% if mode=='url' %}selected{% endif %}>Article URL</option>
            </select>
            <div class="form-text">Choose input type</div>
          </div>

          <div class="col-md-9" id="text-input-col" style="display: {{ 'block' if mode!='url' else 'none' }};">
            <label class="form-label">Headline / Article Text</label>
            <textarea name="text" id="text" class="form-control" rows="6" placeholder="Paste headline or short article (title + 1-2 paragraphs recommended)">{{ request_text or '' }}</textarea>
            <div class="form-text">Tip: Keep text short (1-3 sentences) for faster, cheaper LLM verification.</div>
          </div>

          <div class="col-md-9" id="url-input-col" style="display: {{ 'block' if mode=='url' else 'none' }};">
            <label class="form-label">Article URL</label>
            <input name="text" id="url" class="form-control" placeholder="https://example.com/article" value="{{ request_text if mode=='url' else '' }}">
            <div class="form-text">If a URL is provided the app will attempt to scrape the page.</div>
          </div>

          <div class="col-12 d-flex gap-2">
            <button id="verify-btn" class="btn btn-primary" type="submit">Verify</button>
            <button id="example-btn" class="btn btn-outline-secondary" type="button" onclick="fillExample()">Try example</button>
            <div class="ms-auto small-muted align-self-center">Results may be imperfect — always verify with primary sources.</div>
          </div>
        </form>
      </div>
    </div>
  </div>

  {% if result %}
  <div class="row justify-content-center">
    <div class="col-md-10">
      <div class="app-card">
        <div class="d-flex justify-content-between align-items-start mb-3">
          <div>
            <h3 class="mb-1">Result</h3>
            <div class="small-muted">Claim extracted by the model</div>
          </div>
          <div class="text-end">
            {% set label = result.label or 'Unknown' %}
            {% if label.lower() == 'real' %}
              <span class="badge bg-success badge-label">Real</span>
            {% elif label.lower() == 'fake' %}
              <span class="badge bg-danger badge-label">Fake</span>
            {% elif label.lower() == 'misleading' %}
              <span class="badge bg-warning text-dark badge-label">Misleading</span>
            {% elif label.lower() == 'biased' %}
              <span class="badge bg-info text-dark badge-label">Biased</span>
            {% else %}
              <span class="badge bg-secondary badge-label">Unknown</span>
            {% endif %}
          </div>
        </div>

        <p style="font-size:1.05rem"><strong>Claim:</strong> {{ result.claim or "—" }}</p>

        <div class="row align-items-center mb-3">
          <div class="col-md-8">
            <p class="mb-1"><strong>Explanation:</strong> {{ result.explanation or "—" }}</p>
          </div>
          <div class="col-md-4 text-md-end small-muted">
            <strong>Confidence:</strong>
            {% if result.confidence is not none %}
              {{ "{:.2f}".format(result.confidence) }}
            {% else %}
              N/A
            {% endif %}
          </div>
        </div>

        <div class="mb-3">
          {% if result.confidence is not none %}
          {% set pct = (result.confidence * 100) | round(0) %}
          <div class="progress" style="height:16px;">
            {% if result.label and result.label.lower()=='fake' %}
              <div class="progress-bar bg-danger" role="progressbar" style="width: {{ pct }}%;" aria-valuenow="{{ pct }}" aria-valuemin="0" aria-valuemax="100">{{ pct }}%</div>
            {% elif result.label and result.label.lower()=='real' %}
              <div class="progress-bar bg-success" role="progressbar" style="width: {{ pct }}%;" aria-valuenow="{{ pct }}" aria-valuemin="0" aria-valuemax="100">{{ pct }}%</div>
            {% elif result.label and result.label.lower()=='misleading' %}
              <div class="progress-bar bg-warning text-dark" role="progressbar" style="width: {{ pct }}%;" aria-valuenow="{{ pct }}" aria-valuemin="0" aria-valuemax="100">{{ pct }}%</div>
            {% else %}
              <div class="progress-bar bg-secondary" role="progressbar" style="width: {{ pct }}%;" aria-valuenow="{{ pct }}" aria-valuemin="0" aria-valuemax="100">{{ pct }}%</div>
            {% endif %}
          </div>
          {% endif %}
        </div>

        {% if result.evidence_urls %}
        <div class="mb-3">
          <h5>Evidence</h5>
          <div class="row g-3">
            {% for u in result.evidence_urls %}
            <div class="col-md-6">
              <div class="card evidence">
                <div class="card-body">
                  <h6 class="card-title"><a href="{{ u }}" target="_blank" rel="noopener noreferrer">{{ u }}</a></h6>
                  <p class="card-text small-muted">Click to open source (LLM-suggested evidence).</p>
                </div>
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
        {% endif %}

        <div class="mb-2">
          <button class="btn btn-sm btn-outline-dark" type="button" data-bs-toggle="collapse" data-bs-target="#rawJson" aria-expanded="false" aria-controls="rawJson">
            Toggle raw LLM output
          </button>
        </div>
        <div class="collapse" id="rawJson">
          <div class="mt-3 raw-box">
            <pre style="white-space:pre-wrap;">{{ result.raw_llm_text or "" }}</pre>
          </div>
        </div>

      </div>
    </div>
  </div>
  {% endif %}

  <footer class="row justify-content-center mt-4 mb-5">
    <div class="col-md-10 text-center small-muted">
      <p>Automated first-pass verification. LLM results may be imperfect — always verify with primary sources.</p>
    </div>
  </footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
  function onModeChange(){
    const mode = document.getElementById('mode').value;
    const textCol = document.getElementById('text-input-col');
    const urlCol = document.getElementById('url-input-col');
    if(mode === 'url'){
      textCol.style.display = 'none';
      urlCol.style.display = 'block';
    } else {
      textCol.style.display = 'block';
      urlCol.style.display = 'none';
    }
  }

  // disable verify button while submitting
  document.getElementById('verify-form').addEventListener('submit', function(e){
    const btn = document.getElementById('verify-btn');
    btn.disabled = true;
    btn.innerText = 'Verifying...';
  });

  function fillExample(){
    const modeSelect = document.getElementById('mode');
    modeSelect.value = 'text';
    onModeChange();
    document.getElementById('text').value = "Four courts and two schools in Delhi received bomb threats via an email attributed to Jaish-e-Mohammed.";
  }
</script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    # show blank page (no result)
    return render_template_string(INDEX_HTML, result=None, mode='text', request_text='')

@app.route('/verify', methods=['POST'])
def verify():
    mode = request.form.get('mode') or 'text'
    raw = request.form.get('text') or ''
    text = raw.strip()
    # If mode is url and input is a URL, attempt scraping
    if mode == 'url' and text:
        scraped = scrape_url(text)
        text = scraped or text

    if not text:
        return redirect(url_for('index'))

    # Prepare snippet: prefer lead then safe shorten
    lead = extract_lead(text, sentences=2)
    snippet = lead if lead else text
    snippet = safe_shorten(snippet, max_chars=1500)
    cleaned = clean_text(snippet)

    try:
        res = verify_article(cleaned)
    except Exception as e:
        res = {
            "claim": None,
            "label": None,
            "confidence": None,
            "explanation": f"LLM error: {e}",
            "evidence_urls": [],
            "raw_llm_text": str(e)
        }

    # ensure strings for template safety
    if isinstance(res.get('raw_llm_text'), (dict, list)):
        res['raw_llm_text'] = json.dumps(res['raw_llm_text'], indent=2)

    return render_template_string(INDEX_HTML, result=res, mode=mode, request_text=raw)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8501))
    app.run(host='0.0.0.0', port=port, debug=True)
