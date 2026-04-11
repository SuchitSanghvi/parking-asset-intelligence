"""Metrics Reference tab — catalog sourced from MetricFlow CLI via catalog.py."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
from app.utils.catalog import get_metrics, pretty_dim


def render():
    st.markdown(
        "<div style='font-size:0.85rem;color:#64748b;margin-bottom:1.5rem'>"
        "All metrics available in the semantic layer and the dimensions you can slice them by."
        "</div>",
        unsafe_allow_html=True
    )

    try:
        catalog = get_metrics()
    except Exception as e:
        st.error(f"Error loading catalog from MetricFlow: {e}")
        return

    for metric in catalog:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                st.markdown(
                    f"<div style='font-size:1rem;font-weight:600;color:#0f172a'>"
                    f"{metric['label']}</div>"
                    f"<div style='font-size:0.78rem;color:#64748b;margin-top:4px'>"
                    f"{metric['description']}</div>",
                    unsafe_allow_html=True
                )
                if metric["example"]:
                    st.markdown(
                        f"<div style='font-size:0.75rem;color:#2563eb;margin-top:8px'>"
                        f"💬 {metric['example']}</div>",
                        unsafe_allow_html=True
                    )
            with right:
                st.markdown(
                    "<div style='font-size:0.72rem;font-weight:600;color:#64748b;"
                    "text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px'>"
                    "Available Dimensions</div>",
                    unsafe_allow_html=True
                )
                badges = " ".join(
                    f'<span class="dim-badge">{pretty_dim(d)}</span>'
                    for d in metric["dims"]
                )
                st.markdown(badges, unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<div style='font-size:0.75rem;color:#94a3b8;margin-top:1rem'>"
        "Questions outside these metrics will return a helpful explanation of "
        "what is available closest to what you asked."
        "</div>",
        unsafe_allow_html=True
    )
