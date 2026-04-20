import streamlit as st
from .planning_view import clean_narrative_text

def render_drafting_view(state, workflow, agents):
    """Render the Phase 4: NarrativeEngine drafting interface."""
    st.header("🪶 Phase 4: NarrativeEngine")
    
    with st.expander("❓ How does this work? (Learn More)", expanded=False):
        st.markdown("""
        **Continuity & Sequential Flow**
        Phase 4 uses two main mechanisms to ensure your book flows like a single, cohesive narrative:
        
        1.  **🌉 The Prose Bridge**: The AI reads the last 1,000 words of the previous chapter to match the prose style, emotional resonance, and immediate scene transition.
        2.  **📌 Continuity Memos**: Every time you approve a chapter, Agent 04c creates a 3-sentence summary of key events (items lost, injuries, shifts in relationships). These are fed into the 'memory' of all future chapters.
        """)
    
    st.info("Draft your chapter prose. The AI uses your detailed architect maps and previous chapter context.")

    if not state.chapters or not any(c.pov for c in state.chapters):
        st.warning("Please finalize your Chapter Architect maps in Phase 3 before drafting prose.")
        return

    # Tracking current drafting project
    completed_prose = [c for c in state.chapters if c.draft.final_prose or c.draft.user_approved]
    next_idx = len(completed_prose)

    # --- BULK DRAFTING ---
    with st.expander("📦 Bulk Drafting (Range Generation)", expanded=False):
        st.info("Draft multiple chapters sequentially. Each chapter will wait for approval or auto-commit.")
        col_b1, col_b2 = st.columns(2)
        start_ch = col_b1.number_input("Start Ch", min_value=1, max_value=len(state.chapters), value=next_idx + 1, key="bulk_prose_start", help="First chapter to draft in this batch.")
        end_ch = col_b2.number_input("End Ch", min_value=start_ch, max_value=len(state.chapters), value=min(start_ch + 1, len(state.chapters)), key="bulk_prose_end", help="Last chapter to draft in this batch.")
        
        if st.button("🚀 Run Bulk Draft", key="btn_bulk_prose", use_container_width=True, help="Draft the entire range sequentially. AI will wait for approved 'Memos' to proceed correctly."):
            st.session_state["stop_bulk"] = False # Reset flag
            with st.status("Bulk Drafting prose...", expanded=True) as status:
                bar = st.progress(0, text="Initializing...")
                
                # Stop button placeholder
                stop_btn_placeholder = st.empty()
                if stop_btn_placeholder.button("🛑 Stop Generation", key="stop_bulk_prose_btn"):
                    st.session_state["stop_bulk"] = True
                    st.warning("Stop requested. Finishing current chapter...")

                result = workflow.run_bulk_prose_generation(
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
                    st.warning(f"Generation stopped by user. {result['success_count']} chapters were successfully drafted.")
                else:
                    st.success(f"Successfully drafted {result['success_count']} chapters!")
                
                if "total_tokens" in result:
                    st.metric("Total Tokens Used", f"{result['total_tokens']:,}")
                
                status.update(label="Bulk Drafting Complete!", state="complete", expanded=False)
                st.rerun()

    st.divider()

    # --- INDIVIDUAL DRAFTING ---
    if next_idx < len(state.chapters):
        target_chap = state.chapters[next_idx]
        st.subheader(f"Next: Chapter {target_chap.chapter_number} - {target_chap.title}")
        
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.caption("### 📝 Chapter Architect Map")
            st.write(f"**POV:** {target_chap.pov}")
            st.write(f"**Revelation:** {target_chap.key_revelation}")
            st.markdown(f"**Scene Beats:**\n{target_chap.scene_notes}")
            
        with col_c2:
            st.caption("### 🤖 Narrative Engine")
            if st.button(f"✍️ Draft Chapter {target_chap.chapter_number}", key=f"btn_draft_{target_chap.chapter_number}", type="primary", use_container_width=True, help="Start the 04a drafting loop for this chapter."):
                with st.status("Generating Prose...", expanded=True) as status:
                    result = workflow.run_prose_drafting(state, target_chap.chapter_number, st.write)
                    
                    target_chap.draft.v1_raw = result["v1_raw"]
                    target_chap.draft.critic_notes = result["critic_notes"]
                    target_chap.draft.v2_refined = result["v2_refined"]
                    target_chap.draft.final_prose = result["v2_refined"]
                    
                    status.update(label="Draft Ready!", state="complete", expanded=False)
                    st.rerun()

    # --- REVIEW & EDITING ---
    st.divider()
    st.subheader("📚 Drafting Registry")
    
    for i, chap in enumerate(state.chapters):
        if not chap.draft.v1_raw:
            continue
            
        status_label = "✅ Approved" if chap.draft.user_approved else "💡 Unapproved"
        with st.expander(f"Ch {chap.chapter_number}: {chap.title} ({status_label})"):
            t1, t2, t3 = st.tabs(["Draft v2 (Refined)", "Drafting History", "Continuity Memo"])
            
            with t1:
                chap.draft.final_prose = st.text_area("Final Prose", chap.draft.final_prose, height=400, key=f"prose_{i}")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve Chapter", key=f"app_{i}", help="Lock this prose and generate a Continuity Memo for future chapters."):
                    chap.draft.user_approved = True
                    # Generate Memo if missing
                    if not chap.draft.continuity_memo:
                        with st.status("Generating memo...", expanded=False):
                            cleanup = workflow.run_prose_cleanup(state, chap.chapter_number, chap.draft.final_prose, st.write)
                            chap.draft.continuity_memo = cleanup["memo"]
                    st.rerun()
                if c2.button("💾 Sync & Save", key=f"save_{i}"):
                    st.success("Draft saved.")
            
            with t2:
                st.info("Drafting History & Critic Feedback")
                st.markdown("**Version 1 (Initial Draft)**")
                st.code(chap.draft.v1_raw, language="text", wrap_lines=True)
                st.markdown("**Critic Recommendations (04b)**")
                st.write(chap.draft.critic_notes)
                st.markdown("**Version 2 (Refined)**")
                st.code(chap.draft.v2_refined, language="text", wrap_lines=True)
                
            with t3:
                st.info("This memo is fed into the context of ALL future chapters to maintain continuity.")
                chap.draft.continuity_memo = st.text_area("3-Sentence Continuity Memo", chap.draft.continuity_memo, height=100, key=f"memo_{i}")
                if st.button("🔄 Regerate Memo", key=f"reg_memo_{i}"):
                    with st.status("Updating memo...", expanded=True):
                        cleanup = workflow.run_prose_cleanup(state, chap.chapter_number, chap.draft.final_prose, st.write)
                        chap.draft.continuity_memo = cleanup["memo"]
                    st.rerun()
