"""Ask Your Data tab — question-first layout with collapsible metrics catalog."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
from app.utils.catalog import get_metrics, pretty_dim
from app.utils.llm import translate_to_metric_spec, summarize_result
from app.utils.mf  import run_metric_query

def render():
    if "prefill" not in st.session_state:
        st.session_state["prefill"] = ""

    # ── Subtitle ───────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.85rem;color:#64748b;margin-bottom:1.4rem'>"
        "Ask any question about revenue, occupancy, or session patterns — "
        "answered by a trusted semantic layer."
        "</div>",
        unsafe_allow_html=True
    )

    # ── Load catalog once ──────────────────────────────────────────────────────
    try:
        catalog = get_metrics()
    except Exception as e:
        st.error(f"Error loading metrics catalog: {e}")
        catalog = []

    # ── Question input (primary, full-width) ───────────────────────────────────
    # Use value= (not key=) so example buttons can freely set st.session_state["prefill"]
    # without Streamlit complaining about modifying a widget-owned key.
    with st.form("ask_form", clear_on_submit=False):
        question = st.text_input(
            "Question",
            value=st.session_state["prefill"],
            placeholder="e.g. Which city had the highest revenue in February 2024?",
            label_visibility="collapsed",
        )
        ask = st.form_submit_button("Ask", type="primary")

    # ── Example chips (below input, pull from catalog) ─────────────────────────
    examples = [m["example"] for m in catalog if m["example"]]
    if examples:
        chip_cols = st.columns(len(examples))
        for col, ex in zip(chip_cols, examples):
            if col.button(ex, use_container_width=True):
                st.session_state["prefill"] = ex
                st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Results ────────────────────────────────────────────────────────────────
    if ask and question.strip():
        with st.spinner("Translating question…"):
            try:
                spec = translate_to_metric_spec(question)
            except Exception as e:
                st.error(f"Translation error: {e}")
                return

        if spec.get("error"):
            st.warning(spec.get("message", "That question is outside the available metrics."))
        else:
            with st.spinner("Querying semantic layer…"):
                try:
                    df = run_metric_query(spec)
                except ValueError as e:
                    st.warning(str(e))
                    return
                except RuntimeError as e:
                    st.error(f"MetricFlow error: {e}")
                    return

            with st.container(border=True):
                st.dataframe(df, use_container_width=True, hide_index=True)
                with st.spinner("Summarising…"):
                    try:
                        summary = summarize_result(question, df)
                        st.markdown(
                            f"<div style='font-size:0.8rem;color:#64748b;padding:6px 0'>"
                            f"💡 {summary}</div>",
                            unsafe_allow_html=True
                        )
                    except Exception:
                        pass

            with st.expander("View query spec"):
                st.json(spec)

    elif ask and not question.strip():
        st.warning("Please enter a question first.")

    # ── Metrics catalog (collapsed by default, below results) ──────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.expander("Browse available metrics"):
        if not catalog:
            st.caption("No metrics found.")
        else:
            c1, c2 = st.columns(2)
            for i, metric in enumerate(catalog):
                col = c1 if i % 2 == 0 else c2
                with col:
                    with st.container(border=True):
                        st.markdown(
                            f"<div style='font-size:0.85rem;font-weight:600;color:#0f172a'>"
                            f"{metric['label']}</div>"
                            f"<div style='font-size:0.75rem;color:#64748b;"
                            f"margin-top:2px;margin-bottom:6px'>"
                            f"{metric['description']}</div>",
                            unsafe_allow_html=True
                        )
                        badges = " ".join(
                            f'<span class="dim-badge">{pretty_dim(d)}</span>'
                            for d in metric["dims"]
                        )
                        st.markdown(badges, unsafe_allow_html=True)

            st.markdown(
                "<div style='font-size:0.73rem;color:#94a3b8;margin-top:0.75rem'>"
                "Questions outside these metrics return a helpful message "
                "explaining what is available."
                "</div>",
                unsafe_allow_html=True
            )
