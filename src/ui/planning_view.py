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
        # Convert list of notes to newline-separated string
        return "\n".join([clean_narrative_text(item) for item in content])
    if not isinstance(content, str):
        return str(content)
    
    # Strip leading/trailing brackets if it looks like a single-item list that was stringified
    content = content.strip()
    if content.startswith("[") and content.endswith("]"):
        content = content[1:-1].strip()
    
    # Strip leading/trailing quotes if it was stringified poorly
    if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
        content = content[1:-1].strip()
        
    return content

def render_planning_view():
    """Render the dual-phase chapter planning interface."""
    state = st.session_state.state
    client = st.session_state.client
    st.header("Chapter Architect")
    agents = BookBotAgents(client)
    exporter = st.session_state.exporter
    workflow = NarrativeWorkflow(agents, exporter)
    
    # --- TOKEN TRACKING HEADER ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        spec_text = f"{state.world.setting} {state.world.history} {state.plot.goals} {state.plot.conflicts}"
        spec_tokens = agents.estimate_tokens(spec_text)
        context_text = agents.get_context_summary(state.chapters, count=5)
        context_tokens = agents.estimate_tokens(context_text)
        total_window = 32768
        remaining = total_window - (spec_tokens + context_tokens)
        c1.metric("Spec Tokens", f"~{spec_tokens}")
        c2.metric("Context Tokens", f"~{context_tokens}")
        c3.metric("Remaining Window", f"~{remaining}")

    st.divider()

    # --- PROJECT CONTINUITY SECTION ---
    with st.expander("🛡️ Project Continuity & Checkpoints", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            checkpoint_tag = st.text_input(
                "Checkpoint Tag", 
                placeholder="e.g. Phase 1 Done, After Twist Polish",
                help="A descriptive name for this save (e.g., 'Act 1 Polished')."
            )
            if st.button("💾 Save Project Checkpoint", use_container_width=True, help="Create a named backup of the entire project state."):
                path = st.session_state.exporter.save_log(state, checkpoint_tag)
                st.success(f"Checkpoint saved: {os.path.basename(path)}")
        
        with c2:
            all_logs = st.session_state.exporter.list_logs()
            selected_checkpoint = st.selectbox(
                "Restore from Checkpoint", 
                [""] + all_logs,
                help="Select a previous save to restore the project state."
            )
            if selected_checkpoint and st.button("📂 Restore Project", use_container_width=True, help="Load the selected checkpoint and refresh the session."):
                try:
                    data = st.session_state.exporter.load_log(selected_checkpoint)
                    st.session_state.state = ProjectState.model_validate(data['data'])
                    st.success("Project checkpoint restored!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Restoration failed: {e}")

    st.divider()

    # --- PHASE SELECTION ---
    phase = st.radio("Select Planning Phase", ["Step 1: Book Skeleton", "Step 2: Detailed Architect"], horizontal=True)

    if phase == "Step 1: Book Skeleton":
        st.subheader("🦴 Phase 1: Book Skeleton")
        st.info("Design the high-level narrative flow (the 'skeleton') for your entire book.")
        
        # Local state for skeleton if not yet populated
        if not state.chapters:
            if st.button("Initialize Skeleton (20 Chapters)", help="Create empty chapter slots to begin planning."):
                state.chapters = [ChapterMetadata(chapter_number=i+1) for i in range(20)]
                st.rerun()
        
        target_count = st.number_input("Target Chapter Count", min_value=5, max_value=40, value=20, key="skeleton_target_count", help="How many chapters should the AI generate for your skeleton?")
        
        col_gen, col_save, col_load = st.columns([2, 1, 1])
        
        if col_gen.button("🚀 Generate Skeleton Suggestion", help="Run the automated 5-step agent workflow to draft a full book skeleton."):
            # Thorough State Reset
            prefixes = ["temp_title_", "temp_sum_", "skel_title_", "skel_sum_"]
            keys_to_clear = [k for k in st.session_state.keys() if any(k.startswith(p) for p in prefixes)]
            for k in keys_to_clear:
                del st.session_state[k]
                
            with st.status("Plotting Book Skeleton...", expanded=True) as status:
                result = workflow.run_skeleton_generation(state, target_count, st.write)
                
                if "error" in result:
                    st.error(f"Generation Error: {result['error']}")
                    return

                status.update(label="Skeleton Generation Complete!", state="complete", expanded=False)
                st.toast(f"Skeleton saved to {os.path.basename(result['save_path'])}")

                st.session_state.temp_skel = result["chapters"]
                st.session_state.temp_skel_critic = result["final_qa"]
                st.session_state.temp_skel_initial_critique = result["initial_critique"]
                st.session_state.temp_skel_refined_prose = result["refined_prose"]
                st.rerun()


        if col_save.button("💾 Save Current", help="Save the currently visible skeleton draft as a reusable file."):
            if "temp_skel" in st.session_state:
                formatted_txt = st.session_state.exporter.format_skeleton_as_text(st.session_state.temp_skel)
                j, t = st.session_state.exporter.save_skeleton_draft(
                    st.session_state.temp_skel, 
                    formatted_txt, 
                    f"manual_skel_{datetime.now().strftime('%H%M%S')}"
                )
                st.success(f"Saved: {os.path.basename(j)}")

            else:
                st.warning("No draft to save.")

        # Load UI
        skels = st.session_state.exporter.list_skeletons()
        if skels:
            selected = col_load.selectbox(
                "📂 Load...", 
                ["-- Select --"] + skels,
                help="Load a previously saved skeleton draft from file."
            )
            if selected != "-- Select --":
                try:
                    loaded_data = st.session_state.exporter.load_skeleton(selected)
                    st.session_state.temp_skel = loaded_data
                    st.success(f"Loaded {len(loaded_data)} chapters.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Load failed: {e}")

        if "temp_skel" in st.session_state:
            st.markdown("### 📝 Review Skeleton Draft")
            
            # Final Analysis Highlights
            qa_text = st.session_state.get("temp_skel_critic", "")
            if qa_text:
                c1, c2 = st.columns(2)
                # Simple extraction for UI highlights: find the list items after the headers
                strengths = re.findall(r'Strengths.*?\n(.*?)(?=\n\n|\Z|\[)', qa_text, re.DOTALL | re.IGNORECASE)
                improvements = re.findall(r'Areas for Tightening.*?\n(.*?)(?=\n\n|\Z|\[)', qa_text, re.DOTALL | re.IGNORECASE)
                
                with c1:
                    st.markdown("**⭐ Key Strengths:**")
                    if strengths:
                        st.markdown(strengths[0].strip())
                    else:
                        st.caption("Check Full QA below")
                with c2:
                    st.markdown("**⚠️ Areas for Tightening:**")
                    if improvements:
                        st.markdown(improvements[0].strip())
                    else:
                        st.caption("Check Full QA below")

            with st.expander("🔍 View Full Critic QA Assessment (Step 5)"):
                st.info(qa_text)

            # --- TARGETED REFINEMENT DASHBOARD ---
            initial_critique = st.session_state.get("temp_skel_initial_critique", "")
            if initial_critique:
                with st.container(border=True):
                    st.subheader("🛠️ Narrative Refinement Dashboard")
                    st.info("Select specific improvements from the initial AI critique to apply to this draft.")
                    
                    recs = agents.extract_recommendations(initial_critique)
                    selected_recs = []
                    if recs:
                        for i, rec in enumerate(recs):
                            if st.checkbox(rec, key=f"rec_check_{i}"):
                                selected_recs.append(rec)
                    else:
                        st.caption("No specific bullet-point recommendations extracted. Use the custom box below.")
                    
                    custom_feedback = st.text_area("Additional Custom Adjustments", help="Add your own plot twists or style changes here.")
                    
                    if st.button("🚀 Execute Targeted Refinement", help="Re-run the generation logic focusing specifically on the points selected above."):
                        if not selected_recs and not custom_feedback:
                            st.warning("Please select at least one recommendation or add custom feedback.")
                        else:
                            with st.status("Refining Skeleton...", expanded=True) as status:
                                # Construct the combined critique
                                combined_critique = ""
                                if selected_recs:
                                    combined_critique += "### SELECTED RECOMMENDATIONS:\n- " + "\n- ".join(selected_recs) + "\n\n"
                                if custom_feedback:
                                    combined_critique += f"### USER CUSTOM FEEDBACK:\n{custom_feedback}\n"
                                
                                current_prose = st.session_state.get("temp_skel_refined_prose", json.dumps(st.session_state.temp_skel))
                                result = workflow.run_skeleton_refinement(state, target_count, combined_critique, current_prose, st.write)
                                
                                if "error" in result:
                                    st.error(f"Refinement Error: {result['error']}")
                                    return

                                st.session_state.temp_skel = result["chapters"]
                                st.session_state.temp_skel_critic = result["final_qa"]
                                st.session_state.temp_skel_refined_prose = result["refined_prose"]
                                
                                st.toast(f"Refined skeleton saved as {os.path.basename(result['save_path'])}")
                                status.update(label="Targeted Refinement Complete!", state="complete", expanded=False)
                                st.rerun()

            
            for i, chap in enumerate(st.session_state.temp_skel):
                with st.expander(f"Ch {chap['chapter_number']}: {chap['title']}"):
                    chap['title'] = st.text_input("Title", chap['title'], key=f"temp_title_{i}")
                    chap['summary'] = st.text_area("High-level Summary", chap['summary'], key=f"temp_sum_{i}")
            
            if st.button("✅ Accept & Lock In Skeleton", help="Move this draft into the main chapter registry. WARNING: This overwrites current planning progress."):
                # Overwrite existing chapters with the skeleton
                new_chapters = []
                for chap in st.session_state.temp_skel:
                    new_chapters.append(ChapterMetadata(
                        chapter_number=chap['chapter_number'],
                        title=chap['title'],
                        summary=chap['summary']
                    ))
                state.chapters = new_chapters
                del st.session_state.temp_skel
                st.success("Skeleton locked in! Proceed to Phase 2.")
                st.rerun()

        # Manual Editor for existing Skeleton
        if state.chapters:
            st.markdown("### 🛠️ Current Skeleton (Manual Edit)")
            for i, chap in enumerate(state.chapters):
                with st.expander(f"Ch {chap.chapter_number}: {chap.title}"):
                    chap.title = st.text_input("Title", chap.title, key=f"skel_title_{i}")
                    chap.summary = st.text_area("Summary", chap.summary, key=f"skel_sum_{i}")

        st.divider()
        with st.expander("🛠️ Debug: View Session State"):
            st.write("**temp_skel:**")
            st.json(st.session_state.get("temp_skel", []))
            st.write("**state.chapters samples:**")
            if state.chapters:
                st.json([{"n": c.chapter_number, "t": c.title} for c in state.chapters[:3]])

    else:
        st.subheader("🏗️ Phase 2: Detailed Architect")
        st.info("Flesh out each chapter's detailed metadata using the skeleton as a guide.")
        
        if not state.chapters:
            st.warning("Please finalize your skeleton in Phase 1 first.")
            return

        # Next chapter selector
        completed = [c for c in state.chapters if c.pov and c.scene_notes]
        next_idx = len(completed)
        if next_idx < len(state.chapters):
            target_chap = state.chapters[next_idx]
            st.markdown(f"### Next: Chapter {target_chap.chapter_number} - {target_chap.title}")
            st.caption(f"**Skeleton Guide:** {target_chap.summary}")
            
            if st.button(f"Generate Details for Chapter {target_chap.chapter_number}", help="Ask the agents to draft POV, revelations, and scene notes for this chapter."):
                with st.status(f"Architecting Chapter {target_chap.chapter_number}...", expanded=True) as status:
                    context = agents.get_context_summary(state.chapters[:next_idx], count=5)
                    result = workflow.run_chapter_detailing(state, target_chap.chapter_number, context, st.write)
                    
                    if "error" in result:
                        st.error(f"Detailing Error: {result['error']}")
                        return

                    status.update(label="Detailed Draft Ready!", state="complete", expanded=False)
                    # Clean the draft data once before loading into UI
                    cleaned_draft = {}
                    for k, v in result["draft_json"].items():
                        cleaned_draft[k] = clean_narrative_text(v)
                    
                    st.session_state.active_draft = cleaned_draft
                    st.session_state.active_critic = result["final_qa"]
                    st.session_state.active_chap_idx = next_idx

        # Interaction loop for proposed details
        if "active_draft" in st.session_state:
            with st.container(border=True):
                st.success(f"### Proposed Details: Ch {state.chapters[st.session_state.active_chap_idx].chapter_number}")
                c1, c2 = st.columns([2, 1])
                with c1:
                    d = st.session_state.active_draft
                    title = st.text_input("Title", d.get("title", ""), key="det_title", help="Chapter Title.")
                    summary = st.text_area("Skeleton Summary (Update if needed)", state.chapters[st.session_state.active_chap_idx].summary, key="det_sum", help="The high-level summary from the skeleton.")
                    pov = st.text_input("POV", d.get("pov", ""), key="det_pov", help="The point-of-view character for this chapter.")
                    rev = st.text_input("Revelation", d.get("key_revelation", ""), key="det_rev", help="What key discovery or plot twist occurs?")
                    a = st.text_area("Thread A", d.get("plot_thread_a", ""), key="det_a", help="The primary narrative sequence.")
                    b = st.text_area("Thread B", d.get("plot_thread_b", ""), key="det_b", help="Subplots, thematic mirrors, or secondary sequences.")
                    notes = st.text_area("Scene Notes", d.get("scene_notes", ""), key="det_notes", help="Detailed beat-by-beat scene directions.")
                with c2:
                    st.info(st.session_state.active_critic)
                    if st.button("🔍 Check for Ripple Effects", help="Analyze how these chapter changes might break consistency in later parts of the book."):
                        with st.spinner("Analyzing impacts..."):
                            impact = agents.analyze_impact(state, st.session_state.active_chap_idx, f"{a}\n{b}\n{rev}")
                            st.session_state.ripple_alert = impact
                    
                    if st.session_state.get("ripple_alert"):
                        st.warning("⚠️ **Impact Analysis:**")
                        st.markdown(st.session_state.ripple_alert)

                if st.button("✅ Approve & Update Registry"):
                    chap = state.chapters[st.session_state.active_chap_idx]
                    chap.title, chap.summary, chap.pov = title, summary, pov
                    chap.key_revelation, chap.plot_thread_a, chap.plot_thread_b = rev, a, b
                    chap.scene_notes = notes
                    del st.session_state.active_draft
                    if "ripple_alert" in st.session_state:
                        del st.session_state.ripple_alert
                    st.rerun()

        st.divider()
        st.subheader("Registry")
        for i, chap in enumerate(state.chapters):
            with st.expander(f"Ch {chap.chapter_number}: {chap.title} {'(Detailed)' if chap.scene_notes else '(Skeleton Only)'}"):
                chap.title = st.text_input("Title", chap.title, key=f"v_title_{i}")
                chap.summary = st.text_area("Summary", chap.summary, key=f"v_sum_{i}")
                if chap.scene_notes:
                    chap.pov = st.text_input("POV", chap.pov, key=f"v_pov_{i}")
                    chap.plot_thread_a = st.text_area("Thread A", chap.plot_thread_a, key=f"v_a_{i}")
                    chap.plot_thread_b = st.text_area("Thread B", chap.plot_thread_b, key=f"v_b_{i}")
                    chap.scene_notes = st.text_area("Notes", chap.scene_notes, key=f"v_notes_{i}")
