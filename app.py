import streamlit as st
import os
from src.core.state import ProjectState, WorldSpecs, StyleSpecs, PlotSpecs
from src.core.llm_client import OllamaClient
from src.core.exporter import Exporter
from src.ui.spec_form import render_spec_form
from src.ui.planning_view import render_planning_view

st.set_page_config(page_title="BookBot 05", layout="wide")

# Initialize Session State
if "state" not in st.session_state:
    st.session_state.state = ProjectState()
if "client" not in st.session_state:
    st.session_state.client = OllamaClient()
if "exporter" not in st.session_state:
    st.session_state.exporter = Exporter()

st.title("📖 BookBot 05: Plot & Chapter Architect")

tab1, tab2 = st.tabs(["1. Initial Specifications", "2. Chapter Planning"])

with tab1:
    render_spec_form()

with tab2:
    render_planning_view()

# Sidebar for global controls and save/export
with st.sidebar:
    st.header("Project Controls")
    st.subheader(st.session_state.state.plot.book_title)
    
    if st.button("Save Log Entry", help="Save a JSON snapshot of current state to /logs"):
        path = st.session_state.exporter.save_log(st.session_state.state)
        st.success(f"Log saved: {os.path.basename(path)}")
    
    if st.button("Export to TXT", help="Generate ready-to-use .txt files in /exports"):
        files = st.session_state.exporter.export_txt_files(st.session_state.state)
        st.success(f"Exported {len(files)} files to /exports")
    
    st.divider()
    st.markdown("### Model Config")
    st.info(f"Targeting: `{st.session_state.client.model}`")
