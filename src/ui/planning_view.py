import streamlit as st
import json
import os
import re
from datetime import datetime
from src.core.state import ChapterMetadata, ProjectState
from src.core.agents import BookBotAgents
from src.core.workflow import NarrativeWorkflow

def clean_narrative_text(content):
    """Cleans JSON artifacts like brackets and quotes from AI narrative output."""
    if isinstance(content, list):
        return "\n".join([clean_narrative_text(item) for item in content])
    if not isinstance(content, str):
        return str(content)
    content = content.strip()
    if content.startswith("[") and content.endswith("]"):
        content = content[1:-1].strip()
    if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
        content = content[1:-1].strip()
    return content

def render_planning_view(workflow, agents, subphase="skeleton"):
    """Render the chapter planning interface (Phase 2 Skeleton or Phase 3 Architect)."""
    state = st.session_state.state

    if subphase == "skeleton":
        render_skeleton_phase(state, workflow, agents)
    else:
        render_architect_phase(state, workflow, agents)

def render_skeleton_phase(state, workflow, agents):
    st.header("🦴 Phase 2: Narrative Skeleton")
    st.info("Design the high-level narrative flow. You can add, insert, or delete chapters like cells in a notebook.")

    # Initialize if empty
    if not state.chapters:
        if st.button("Initialize Skeleton from Project Count", help=f"Create {state.chapter_count} empty chapters."):
            state.chapters = [ChapterMetadata(chapter_number=i+1) for i in range(state.chapter_count)]
            st.rerun()

    # --- TOP ACTIONS ---
    c1, c2, c3 = st.columns([2, 1, 1])
    
    # Token estimate for skeleton
    spec_str = f"{state.plot.book_title} {state.world.setting} {state.plot.goals} {state.plot.conflicts}"
    est_tokens = agents.estimate_tokens(spec_str)
    
    if c1.button("🚀 Generate Phase 2 Skeleton", key="btn_gen_skeleton", help=f"Run the automated 5-step agent workflow. (Est context: {est_tokens:,} tokens)"):
        with st.status("Plotting Book Skeleton...", expanded=True) as status:
            result = workflow.run_skeleton_generation(state, state.chapter_count, st.write)
            if "error" in result:
                st.error(f"Generation Error: {result['error']}")
                return
            state.temp_skel_draft = result["chapters"]
            state.temp_skel_critic = result["final_qa"]
            state.temp_skel_prose = result["refined_prose"]
            # Tracking tokens for the result output
            st.session_state["last_skel_tokens"] = result.get("total_tokens", 0)
            status.update(label=f"Skeleton Draft Ready! ({result.get('total_tokens', 0):,} tokens)", state="complete", expanded=False)
            st.rerun()

    if state.temp_skel_draft:
        if c2.button("✅ Accept AI Draft", key="btn_accept_skel_draft"):
            new_chaps = []
            for i, d in enumerate(state.temp_skel_draft):
                new_chaps.append(ChapterMetadata(
                    chapter_number=i+1,
                    title=d.get("title", ""),
                    summary=d.get("summary", "")
                ))
            state.chapters = new_chaps
            state.temp_skel_draft = None
            st.success("AI draft accepted into registry!")
            st.rerun()
        if c3.button("🗑️ Discard Draft", key="btn_discard_skel_draft"):
            state.temp_skel_draft = None
            st.rerun()

    # --- SKELETON EDITOR ---
    st.divider()
    
    # If we have a draft, show it for review
    if state.temp_skel_draft:
        st.subheader("📝 Review AI Skeleton Draft")
        with st.expander("🔍 View AI Critique for this Draft"):
            st.markdown(state.temp_skel_critic)
        for i, chap in enumerate(state.temp_skel_draft):
            with st.expander(f"Draft Ch {i+1}: {chap.get('title', 'Untitled')}"):
                st.write(chap.get("summary", "No summary."))

    # The Registry (Source of Truth)
    st.subheader("🗂️ Active Chapter Registry")
    
    if not state.chapters:
        st.caption("Registry is empty. Use the buttons above to initialize or generate.")
        return

    # Chapter List with Move/Add/Delete
    for i, chap in enumerate(state.chapters):
        with st.container(border=True):
            col_main, col_ctrl = st.columns([5, 1])
            with col_main:
                c_head_1, c_head_2 = st.columns([1, 4])
                c_head_1.markdown(f"### Ch {chap.chapter_number}")
                chap.title = c_head_2.text_input("Title", chap.title, key=f"title_{i}")
                chap.summary = st.text_area("High-level Summary", chap.summary, key=f"sum_{i}", height=100)
            
            with col_ctrl:
                st.write("") # Spacer
                if st.button("➕ Above", key=f"add_above_{i}", use_container_width=True):
                    state.chapters.insert(i, ChapterMetadata(chapter_number=0))
                    reorder_chapters(state)
                    st.rerun()
                if st.button("➕ Below", key=f"add_below_{i}", use_container_width=True):
                    state.chapters.insert(i+1, ChapterMetadata(chapter_number=0))
                    reorder_chapters(state)
                    st.rerun()
                if st.button("🗑️ Del", key=f"del_{i}", use_container_width=True):
                    state.chapters.pop(i)
                    reorder_chapters(state)
                    st.rerun()
                if st.button("⚖️ Run Impact Analysis", key=f"impact_skel_{i}", help="Check if this change breaks later chapters."):
                    with st.spinner("Analyzing ripple effects..."):
                        impact = agents.run_architect_impact_analysis_turn(state, i, chap.summary)
                        st.info(impact)

    st.divider()
    if st.button("💾 Sync & Save Skeleton", key="btn_sync_skel", type="primary", use_container_width=True):
        st.session_state.exporter.save_log(state)
        st.success("Skeleton synchronized and saved!")
        st.rerun()

def reorder_chapters(state):
    """Ensure chapter numbers are sequential 1..N and update project count."""
    for i, chap in enumerate(state.chapters):
        chap.chapter_number = i + 1
    state.chapter_count = len(state.chapters)

def render_architect_phase(state, workflow, agents):
    st.header("🏗️ Phase 3: Chapter Architect")
    st.info("Flesh out each chapter's detailed metadata (POV, Tense, Scene Beats) using the skeleton as a guide.")

    if not state.chapters:
        st.warning("Please finalize your skeleton in Phase 2 first.")
        return

    # Next chapter selector
    completed = [c for c in state.chapters if c.pov and c.scene_notes]
    next_idx = len(completed)
    
    # --- BULK ARCHITECTING ---
    with st.expander("📦 Bulk Architecting (Range Generation)", expanded=False):
        st.info("Directly architect multiple chapters sequentially. Results will be saved to the registry immediately.")
        col_b1, col_b2 = st.columns(2)
        start_ch = col_b1.number_input("Start Chapter", min_value=1, max_value=len(state.chapters), value=min(next_idx + 1, len(state.chapters)))
        end_ch = col_b2.number_input("End Chapter", min_value=1, max_value=len(state.chapters), value=len(state.chapters))
        
        if st.button("🚀 Run Bulk Architecture", key="btn_bulk_arch", use_container_width=True):
            st.session_state["stop_bulk"] = False # Reset flag
            with st.status("Initializing Bulk Draft...", expanded=True) as status:
                bar = st.progress(0, text="Starting...")
                
                # We show the stop button in the status area or as a separate UI element
                # In Streamlit, a button click triggers a rerun. We can use st.empty to show it.
                stop_btn_placeholder = st.empty()
                if stop_btn_placeholder.button("🛑 Stop Generation", key="stop_bulk_btn"):
                    st.session_state["stop_bulk"] = True
                    st.warning("Stop requested. Finishing current chapter...")

                result = workflow.run_bulk_detailing(
                    state, 
                    int(start_ch), 
                    int(end_ch), 
                    st.write, 
                    bar.progress,
                    stop_check=lambda: st.session_state.get("stop_bulk", False)
                )
                
                if "error" in result:
                    st.error(result["error"])
                elif result.get("interrupted"):
                    st.warning(f"Generation stopped by user. {result['success_count']} chapters were successfully architected.")
                else:
                    st.success(f"Successfully architected {result['success_count']} chapters!")
                
                if "total_tokens" in result:
                    st.metric("Total Tokens Used", f"{result['total_tokens']:,}")
                status.update(label="Bulk Architecting Complete!", state="complete", expanded=False)
                st.rerun()

    st.divider()

    # --- INDIVIDUAL ARCHITECTING ---
    if next_idx < len(state.chapters):
        target_chap = state.chapters[next_idx]
        
        # Token Meter for context
        context_str = agents.get_context_summary(state.chapters[:next_idx], count=5)
        spec_str = f"{state.plot.book_title} {state.world.setting} {state.style.tone}"
        total_context_tokens = agents.estimate_tokens(context_str + spec_str)
        
        c_meta_1, c_meta_2 = st.columns([3, 1])
        c_meta_1.markdown(f"### Next: Phase 3 | Chapter {target_chap.chapter_number} - {target_chap.title}")
        c_meta_2.metric("Prompt Context", f"{total_context_tokens:,} tokens", help="Estimated tokens being sent to the LLM for this turn. Larger context is better for continuity but uses more local resources.")
        
        st.caption(f"**Skeleton Guide:** {target_chap.summary}")
        
        if st.button(f"🚀 Generate Details for Chapter {target_chap.chapter_number}", key=f"gen_det_{target_chap.chapter_number}"):
            with st.status(f"Architecting Chapter {target_chap.chapter_number}...", expanded=True) as status:
                result = workflow.run_chapter_detailing(state, target_chap.chapter_number, context_str, st.write)
                if "error" in result:
                    st.error(f"Detailing Error: {result['error']}")
                    return
                
                cleaned_draft = {k: clean_narrative_text(v) for k, v in result["draft_json"].items()}
                state.active_chapter_draft = cleaned_draft
                state.active_chapter_critic = result["final_qa"]
                state.active_chapter_idx = next_idx
                # Store tokens for the last turn to show feedback
                st.session_state["last_tokens"] = result.get("total_tokens", 0)
                status.update(label=f"Draft Ready! ({result.get('total_tokens', 0):,} tokens)", state="complete", expanded=False)
                st.rerun()

    # Interaction loop for proposed details
    if state.active_chapter_draft is not None:
        idx = state.active_chapter_idx
        with st.container(border=True):
            st.success(f"### Proposed Details: Ch {state.chapters[idx].chapter_number}")
            c1, c2 = st.columns([2, 1])
            with c1:
                d = state.active_chapter_draft
                title = st.text_input("Title", d.get("title", ""), key="det_title")
                summary = st.text_area("Skeleton Summary (Update if needed)", state.chapters[idx].summary, key="det_sum")
                pov = st.text_input("POV", d.get("pov", ""), key="det_pov")
                tense = st.selectbox("Tense", ["Past", "Present"], index=0 if d.get("tense", "").lower() == "past" else 1, key="det_tense")
                rev = st.text_input("Revelation", d.get("key_revelation", ""), key="det_rev")
                a = st.text_area("Plot Thread A", d.get("plot_thread_a", ""), key="det_a")
                b = st.text_area("Plot Thread B", d.get("plot_thread_b", ""), key="det_b")
                notes = st.text_area("Scene Notes (Beats)", d.get("scene_notes", ""), key="det_notes", height=200)
            
            with c2:
                st.info(state.active_chapter_critic)
                if st.button("🗑️ Discard Draft", key="btn_discard_arch_draft"):
                    state.active_chapter_draft = None
                    st.rerun()

            if st.button("✅ Approve & Update Registry", key="btn_approve_arch", use_container_width=True):
                chap = state.chapters[idx]
                chap.title, chap.summary, chap.pov, chap.tense = title, summary, pov, tense
                chap.key_revelation, chap.plot_thread_a, chap.plot_thread_b = rev, a, b
                chap.scene_notes = notes
                state.active_chapter_draft = None
                st.success(f"Chapter {chap.chapter_number} Map updated!")
                st.rerun()

    st.divider()
    st.subheader("📚 Chapter Map Registry")
    for i, chap in enumerate(state.chapters):
        status_icon = "✅" if chap.scene_notes else "🦴"
        with st.expander(f"{status_icon} Ch {chap.chapter_number}: {chap.title}"):
            chap.title = st.text_input("Title", chap.title, key=f"v_title_{i}")
            chap.summary = st.text_area("Summary", chap.summary, key=f"v_summary_{i}")
            if chap.scene_notes:
                chap.pov = st.text_input("POV", chap.pov, key=f"v_pov_{i}")
                chap.tense = st.selectbox("Tense", ["Past", "Present"], index=0 if chap.tense.lower() == "past" else 1, key=f"v_tense_{i}")
                chap.plot_thread_a = st.text_area("Thread A", chap.plot_thread_a, key=f"v_a_{i}")
                chap.plot_thread_b = st.text_area("Thread B", chap.plot_thread_b, key=f"v_b_{i}")
                chap.scene_notes = st.text_area("Notes", chap.scene_notes, key=f"v_notes_{i}", height=150)
