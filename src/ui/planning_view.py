import streamlit as st
import json
import os
import re
from datetime import datetime
from src.core.state import ChapterMetadata
from src.core.agents import BookBotAgents

def render_planning_view():
    state = st.session_state.state
    client = st.session_state.client
    st.header("Chapter Architect")
    agents = BookBotAgents(client)
    
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

    # --- PHASE SELECTION ---
    phase = st.radio("Select Planning Phase", ["Step 1: Book Skeleton", "Step 2: Detailed Architect"], horizontal=True)

    if phase == "Step 1: Book Skeleton":
        st.subheader("🦴 Phase 1: Book Skeleton")
        st.info("Design the high-level narrative flow (the 'skeleton') for your entire book.")
        
        # Local state for skeleton if not yet populated
        if not state.chapters:
            if st.button("Initialize Skeleton (20 Chapters)"):
                state.chapters = [ChapterMetadata(chapter_number=i+1) for i in range(20)]
                st.rerun()
        
        target_count = st.number_input("Target Chapter Count", min_value=5, max_value=40, value=20, key="skeleton_target_count", help="How many chapters should the AI generate for your skeleton?")
        
        col_gen, col_save, col_load = st.columns([2, 1, 1])
        
        if col_gen.button("🚀 Generate Skeleton Suggestion"):
            # Thorough State Reset: Clear all possible widget keys to force fresh rendering
            prefixes = ["temp_title_", "temp_sum_", "skel_title_", "skel_sum_"]
            keys_to_clear = [k for k in st.session_state.keys() if any(k.startswith(p) for p in prefixes)]
            for k in keys_to_clear:
                del st.session_state[k]
                
            with st.status("Plotting Book Skeleton...", expanded=True) as status:
                st.write("🤖 **01a_skeleton_plotter** drafting skeleton...")
                skel_json = agents.run_skeleton_plotter_turn(state, target_count)
                raw_skel = skel_json.get('raw', 'N/A')
                if "error" in skel_json: 
                    st.error(f"Plotter Error: {skel_json['error']}")
                    st.session_state.exporter.save_skeleton_draft([], raw_skel, f"ERROR_skel_{datetime.now().strftime('%H%M%S')}")
                    return
                skel_text = json.dumps(skel_json, indent=2)

                st.write("🧐 **01b_skeleton_critic** reviewing structure...")
                critique = agents.run_skeleton_critic_turn(state, skel_text)
                
                st.write("🛠️ **01a_skeleton_plotter** refining skeleton...")
                refined_json = agents.run_skeleton_plotter_turn(state, target_count, critique, skel_text)
                raw_refined = refined_json.get('raw', json.dumps(refined_json))
                if "error" in refined_json: 
                    st.error(f"Refinement Error: {refined_json['error']}")
                    st.session_state.exporter.save_skeleton_draft([], raw_refined, f"ERROR_refined_{datetime.now().strftime('%H%M%S')}")
                    return
                
                st.write("🔄 **01c_skeleton_formatter** extracting structured JSON...")
                formatted_json = agents.run_skeleton_formatter_turn(raw_refined, target_count)
                if "error" in formatted_json:
                    st.error(f"Formatting Error: {formatted_json['error']}")
                    return
                formatted_text = json.dumps(formatted_json, indent=2)

                st.write("⚖️ **01b_skeleton_critic** final JSON assessment...")
                final_qa = agents.run_skeleton_critic_turn(state, formatted_text, is_final=True)
                
                status.update(label="Skeleton Generation Complete!", state="complete", expanded=False)
                
                # Save to skeleton_output directory
                j_path, t_path = st.session_state.exporter.save_skeleton_draft(
                    formatted_json.get("chapters", []), 
                    f"FINAL JSON:\n{formatted_text}\n\nFINAL QA:\n{final_qa}\n\nREFINED PROSE:\n{raw_refined}\n\nINITIAL CRITIQUE:\n{critique}"
                )
                st.toast(f"Skeleton saved to {os.path.basename(j_path)}")

                st.session_state.temp_skel = formatted_json.get("chapters", [])
                st.session_state.temp_skel_critic = final_qa
                st.rerun()

        if col_save.button("💾 Save Current"):
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
            selected = col_load.selectbox("📂 Load...", ["-- Select --"] + skels)
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
            
            for i, chap in enumerate(st.session_state.temp_skel):
                with st.expander(f"Ch {chap['chapter_number']}: {chap['title']}"):
                    chap['title'] = st.text_input("Title", chap['title'], key=f"temp_title_{i}")
                    chap['summary'] = st.text_area("High-level Summary", chap['summary'], key=f"temp_sum_{i}")
            
            if st.button("✅ Accept & Lock In Skeleton"):
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
            
            if st.button(f"Generate Details for Chapter {target_chap.chapter_number}"):
                with st.status(f"Architecting Chapter {target_chap.chapter_number}...", expanded=True) as status:
                    context = agents.get_context_summary(state.chapters[:next_idx], count=5)
                    st.write("🤖 **02a_plotter** Drafting...")
                    draft_json = agents.run_plotter_turn(state, target_chap.chapter_number, context)
                    draft_text = json.dumps(draft_json, indent=2)
                    st.write("🧐 **02b_critic** Critiquing...")
                    critique = agents.run_critic_turn(state, target_chap.chapter_number, context, draft_text)
                    st.write("🛠️ **02a_plotter** Refining...")
                    refined_json = agents.run_plotter_turn(state, target_chap.chapter_number, context, critique, draft_text)
                    refined_text = json.dumps(refined_json, indent=2)
                    st.write("⚖️ **02b_critic** Final Assessment...")
                    final_thoughts = agents.run_critic_turn(state, target_chap.chapter_number, context, refined_text, is_final=True)
                    
                    status.update(label="Detailed Draft Ready!", state="complete", expanded=False)
                    st.session_state.active_draft = refined_json
                    st.session_state.active_critic = final_thoughts
                    st.session_state.active_chap_idx = next_idx

        # Interaction loop for proposed details
        if "active_draft" in st.session_state:
            with st.container(border=True):
                st.success(f"### Proposed Details: Ch {state.chapters[st.session_state.active_chap_idx].chapter_number}")
                c1, c2 = st.columns([2, 1])
                with c1:
                    d = st.session_state.active_draft
                    title = st.text_input("Title", d.get("title", ""), key="det_title")
                    summary = st.text_area("Skeleton Summary (Update if needed)", state.chapters[st.session_state.active_chap_idx].summary, key="det_sum")
                    pov = st.text_input("POV", d.get("pov", ""), key="det_pov")
                    rev = st.text_input("Revelation", d.get("key_revelation", ""), key="det_rev")
                    a = st.text_area("Thread A", d.get("plot_thread_a", ""), key="det_a")
                    b = st.text_area("Thread B", d.get("plot_thread_b", ""), key="det_b")
                    notes = st.text_area("Scene Notes", d.get("scene_notes", ""), key="det_notes")
                with c2:
                    st.info(st.session_state.active_critic)
                    if st.button("🔍 Check for Ripple Effects"):
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
