"""
data_io.py — all I/O lives here (CSV in, LLM out).

Keeping the data layer separate from the analytics (`logic.py`) and the UI
(`app.py`) means new sources — a new file format, a different LLM provider, a
live ad-platform API — are a change in THIS file only.
"""

import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# --- LLM config -------------------------------------------------------------
_GROQ_KEYS = [os.getenv("GROQ_KEY_1"), os.getenv("GROQ_KEY_2"), os.getenv("GROQ_KEY_3")]
_MODEL = "llama-3.3-70b-versatile"


def load_csv(source) -> pd.DataFrame:
    """Read a campaign CSV from a path or an uploaded file object.

    Swap-point for other sources: add load_excel / load_pdf / load_api here and
    nothing downstream changes.
    """
    df = pd.read_csv(source)
    df.columns = [c.strip() for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def call_groq(prompt: str) -> str:
    """Call Groq with key rotation. Raises if no key is set or all keys fail.

    Decoupled on purpose: if this raises, the dashboard still renders — only the
    AI summary section degrades.
    """
    from groq import Groq

    keys = [k for k in _GROQ_KEYS if k]
    if not keys:
        raise ValueError("No Groq API key in .env (set GROQ_KEY_1).")
    last_err = None
    for key in keys:
        try:
            resp = Groq(api_key=key).chat.completions.create(
                model=_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            return resp.choices[0].message.content
        except Exception as e:  # try the next key
            last_err = e
            continue
    raise RuntimeError(f"All Groq keys failed: {last_err}")
