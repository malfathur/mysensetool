# MYSense — Paid Social Performance Tool

A small internal tool that turns two weeks of paid-social campaign data into
metrics, charts, evidence-based recommendations, and an LLM-written summary a
campaign manager can act on.

Built for the MYSense AI Automation Engineer practical assessment.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # then add a Groq key (free: console.groq.com)
streamlit run app.py
```

The app loads `data/campaign_data.csv` automatically; upload another CSV (same
columns) from the sidebar to analyse a different period. The dashboard works
without a Groq key — only the AI summary needs one.

## Pipeline

`ingest → validate → objective-aware metrics → charts → recommendations → AI summary`

The data is **validated before any metric is trusted** (CTR recomputed from raw
counts, funnel/null/negative checks, and an explicit guard that *Awareness*
campaigns are judged on reach/CPM, not ROAS).

## Project layout

```
mysensetool/
├── app.py                 # Streamlit UI (entry point)
├── mysense/               # importable package
│   ├── __init__.py
│   ├── data_io.py         # I/O: CSV load + Groq call (key rotation)
│   └── logic.py           # analytics: validation, metrics, charts, recs, prompt
├── data/
│   └── campaign_data.csv  # source data
├── docs/
│   ├── brief.md           # the assessment brief
│   ├── INSIGHT_NOTE.md    # half-page findings + recommendations
│   └── GLOSSARY.md        # metric definitions / context
├── tests/
│   └── test_logic.py      # unit tests for the pure analytics layer
├── .streamlit/config.toml # dark theme
├── requirements.txt
└── .env.example
```

**Why three layers:** a new data source touches `data_io.py` only; a new metric
or chart touches `logic.py` only; a new screen touches `app.py` only. `logic.py`
is pure (no Streamlit, no I/O) so it is unit-testable in isolation.

## Tests

```bash
pip install pytest
pytest
```

## Key findings

See [`docs/INSIGHT_NOTE.md`](docs/INSIGHT_NOTE.md). Headline: blended ROAS 2.82×;
scale Mother's Day Sale (8.3×), refresh the fatiguing Retargeting line
(CTR −61% over 14 days), and re-justify the Awareness spend on reach not sales.
