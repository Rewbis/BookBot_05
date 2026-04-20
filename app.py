import streamlit as st
import os
from src.core.state import ProjectState
from src.core.llm_client import OllamaClient
from src.core.exporter import Exporter
from src.ui.spec_form import render_spec_form
from src.ui.planning_view import render_planning_view
from src.ui.drafting_view import render_drafting_view
from src.core.workflow import NarrativeWorkflow

st.set_page_config(page_title="BookBot 05", layout="wide")

# Initialize Session State
if "state" not in st.session_state:
    st.session_state.state = ProjectState()
if "client" not in st.session_state:
    st.session_state.client = OllamaClient()
if "exporter" not in st.session_state:
    st.session_state.exporter = Exporter()

state = st.session_state.state
client = st.session_state.client
exporter = st.session_state.exporter
agents = st.session_state.get("agents")
if not agents:
    from src.core.agents import BookBotAgents
    agents = BookBotAgents(client)
    st.session_state.agents = agents

workflow = NarrativeWorkflow(agents, exporter)

st.title("📖 BookBot 05: Narrative Engineering Suite")

# --- GLOBAL SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Project Controls")
    st.subheader(state.plot.book_title)
    
    if st.button("💾 Save Project State", key="sidebar_save_btn", use_container_width=True, help="Save a unified JSON snapshot of the entire project."):
        # Sync current tab before saving
        path = st.session_state.exporter.save_log(state)
        st.success(f"Log saved: {os.path.basename(path)}")
    
    st.divider()
    st.header("Load Progress")
    logs = st.session_state.exporter.list_logs()
    if logs:
        selected_log = st.selectbox(
            "Select a log to load", 
            logs,
            index=0,
            key="sidebar_load_select",
            help="Choose a previous project snapshot to restore."
        )
        if st.button("📂 Load Selected Log", key="sidebar_load_btn", use_container_width=True):
            try:
                data = st.session_state.exporter.load_log(selected_log)
                st.session_state.state = ProjectState.model_validate(data['data'])
                st.success("Project loaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading log: {e}")
    else:
        st.info("No logs found in /logs.")
    
    st.divider()
    if st.button("📄 Export to TXT", key="sidebar_export_btn", use_container_width=True):
        files = st.session_state.exporter.export_txt_files(state)
        st.success(f"Exported {len(files)} files to /exports")
    
    st.divider()
    st.markdown(f"### Model: `{st.session_state.client.model}`")

# --- 4-PHASE TABS ---
tabs = [
    "Phase 1: Configuration", 
    "Phase 2: Narrative Skeleton", 
    "Phase 3: Chapter Architect", 
    "Phase 4: NarrativeEngine"
]

# Attempt to find the index of the saved tab
try:
    default_tab_idx = tabs.index(state.current_tab)
except ValueError:
    default_tab_idx = 0

active_tab = st.tabs(tabs)

# We use state.current_tab to keep track of which tab was active
with active_tab[0]:
    state.current_tab = tabs[0]
    render_spec_form(workflow)

with active_tab[1]:
    state.current_tab = tabs[1]
    render_planning_view(workflow, agents, subphase="skeleton")

with active_tab[2]:
    state.current_tab = tabs[2]
    render_planning_view(workflow, agents, subphase="architect")

with active_tab[3]:
    state.current_tab = tabs[3]
    render_drafting_view(state, workflow, agents)
