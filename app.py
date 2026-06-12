"""
app.py — Streamlit UI for the MYSense paid-social performance tool.

Thin presentation layer only. All data access lives in `data_io.py`, all
analytics in `logic.py`. This file just wires inputs to functions to widgets.

Run:  pip install -r requirements.txt && streamlit run app.py
"""

import os

import numpy as np
import pandas as pd
import streamlit as st

from mysense import data_io as dio
from mysense import logic

st.set_page_config(page_title="MYSense — Campaign Performance", layout="wide")

DATA_FILE = os.path.join("data", "campaign_data.csv")
ICON = {"ok": "✅", "warn": "⚠️", "error": "❌"}


@st.cache_data(show_spinner=False)
def _load(source):
    return dio.load_csv(source)


def _fmt(g: pd.DataFrame) -> pd.DataFrame:
    """Human-readable currency / percentage formatting for a rollup table."""
    s = g.copy()
    s["CTR"] = (s["CTR"] * 100).round(2).astype(str) + "%"
    for col in ["spend", "revenue", "CPC", "CPM", "CPA"]:
        s[col] = s[col].map(lambda v: f"RM {v:,.2f}" if pd.notna(v) else "—")
    s["ROAS"] = s["ROAS"].map(lambda v: f"{v:.2f}×")
    if "spend_share" in s.columns:
        s["spend_share"] = (s["spend_share"] * 100).round(1).astype(str) + "%"
    return s


# --- Header + input ---------------------------------------------------------
st.title("MYSense — Paid Social Performance Tool")

with st.sidebar:
    st.header("Data")
    up = st.file_uploader("Upload campaign CSV", type=["csv"])
    st.caption(f"No upload → loads bundled `{DATA_FILE}`.")

source = up if up is not None else (DATA_FILE if os.path.exists(DATA_FILE) else None)
if source is None:
    st.info("Upload a campaign CSV to begin.")
    st.stop()

try:
    df = _load(source)
except Exception as e:
    st.error(f"Could not read the CSV: {e}")
    st.stop()

# --- Validation (catch misleading data before building on it) ---------------
checks = logic.validate(df)
errors = [m for lvl, m in checks if lvl == "error"]
with st.expander("Data validation  " + ("— ❌ issues found" if errors else "— ✅ passed"),
                 expanded=bool(errors)):
    for lvl, msg in checks:
        st.markdown(f"{ICON[lvl]} {msg}")

if errors:
    st.error("Validation found blocking issues above — fix the data before trusting the metrics.")
    st.stop()

# --- Compute ----------------------------------------------------------------
roll = logic.campaign_rollup(df)
totals = logic.account_totals(df)
notes = logic.fatigue_notes(df, roll)

# --- Headline KPIs ----------------------------------------------------------
st.subheader("Headline metrics")
c = st.columns(5)
c[0].metric("Total spend", f"RM {totals['spend']:,.0f}")
c[1].metric("Revenue", f"RM {totals['revenue']:,.0f}")
c[2].metric("Blended ROAS", f"{totals['blended_roas']:.2f}×")
c[3].metric("Conversions", f"{totals['conversions']:,}")
c[4].metric("Account CTR", f"{totals['ctr']*100:.2f}%")

# --- Budget by objective (the strategic headline) ---------------------------
st.divider()
st.subheader("Where the budget goes — by objective")
obj = logic.objective_rollup(df)
st.plotly_chart(logic.objective_chart(obj), use_container_width=True)
st.dataframe(
    _fmt(obj)[["objective", "campaigns", "spend", "spend_share", "impressions",
               "CTR", "CPM", "conversions", "CPA", "revenue", "ROAS"]],
    use_container_width=True, hide_index=True,
)

# --- Campaign performance ---------------------------------------------------
st.divider()
st.subheader("Campaign performance")
left, right = st.columns(2)
with left:
    st.plotly_chart(logic.roas_chart(roll), use_container_width=True)
with right:
    default_idx = int(np.argmax([logic.daily_trend(df, c)["fatigue"]
                                 for c in roll["campaign_name"]])) if notes else 0
    pick = st.selectbox("Daily trend for", roll["campaign_name"].tolist(), index=default_idx)
    st.plotly_chart(logic.trend_chart(df, pick), use_container_width=True)

with st.expander("Per-campaign metrics table", expanded=False):
    st.dataframe(
        _fmt(roll)[["campaign_name", "objective", "spend", "impressions", "clicks",
                    "CTR", "CPC", "CPM", "conversions", "CPA", "revenue", "ROAS"]],
        use_container_width=True, hide_index=True,
    )

# --- Recommendations (computed) ---------------------------------------------
st.divider()
st.subheader("Recommendations")
for r in logic.recommendations(df, roll):
    st.markdown(f"- {r}")

# --- AI summary -------------------------------------------------------------
st.divider()
st.subheader("AI performance summary")
if st.button("Generate AI summary", type="primary"):
    try:
        with st.spinner("Asking the analyst…"):
            report = dio.call_groq(logic.build_prompt(totals, roll, notes, obj))
        st.markdown(report)
        st.download_button("Download summary (.md)", report,
                           file_name="mysense_performance_summary.md", mime="text/markdown")
    except Exception as e:
        st.warning(f"AI summary unavailable ({e}). The dashboard above is fully usable without it.")
