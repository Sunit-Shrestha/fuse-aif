import os
import time

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AG_NEWS Topic Router", page_icon="📰")
st.title("📰 AG_NEWS Topic Router")
st.caption("Productionized Week 13 LSTM classifier — ONNX-optimized, with a Gemini fallback.")

headline = st.text_area("News headline / snippet", placeholder="e.g. The central bank raised interest rates today.")

if st.button("Classify", type="primary") and headline.strip():
    start = time.time()
    try:
        resp = requests.post(f"{BACKEND_URL}/predict", json={"text": headline}, timeout=30)
        resp.raise_for_status()
        result = resp.json()
    except Exception as exc:
        st.error(f"Request failed: {exc}")
    else:
        client_latency = (time.time() - start) * 1000

        badge = {"onnx_local": "🟢 local ONNX", "gemini_fallback": "🟡 Gemini fallback", "degraded": "🔴 degraded"}
        st.subheader(f"Category: {result['category']}")
        st.write(f"Served by: {badge.get(result['provider_used'], result['provider_used'])}"
                 + (" (cached)" if result.get("cached") else ""))

        if result.get("confidence") is not None:
            st.progress(result["confidence"], text=f"Confidence: {result['confidence']:.1%}")
        if result.get("probabilities"):
            st.bar_chart(result["probabilities"])

        st.caption(f"Server latency: {result['latency_ms']:.2f}ms | Round-trip: {client_latency:.1f}ms")

st.divider()
st.subheader("Batch classification")
batch_text = st.text_area("One headline per line", height=120)
if st.button("Classify batch") and batch_text.strip():
    lines = [l for l in batch_text.splitlines() if l.strip()]
    try:
        resp = requests.post(f"{BACKEND_URL}/predict_batch", json={"texts": lines}, timeout=30)
        resp.raise_for_status()
        results = resp.json()
    except Exception as exc:
        st.error(f"Request failed: {exc}")
    else:
        for line, r in zip(lines, results):
            st.write(f"**{r['category']}** ({r.get('confidence', 0) or 0:.1%}) — {line}")
