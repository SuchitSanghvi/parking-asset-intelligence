"""Metrics Reference tab — redirects to Ask Your Data."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st


def render():
    st.info(
        "Metrics reference is now available directly on the **Ask Your Data** tab.",
        icon="ℹ️"
    )
