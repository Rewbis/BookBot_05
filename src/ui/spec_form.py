import streamlit as st
import pandas as pd
from src.core.state import CharacterProfile

def render_spec_form(workflow):
    """Render the Phase 1: Project Configuration form."""
    state = st.session_state.state
    
    st.header("🎯 Phase 1: Project Configuration")
    
    # --- SECTION 1: IDENTITY ---
    with st.container(border=True):
        st.subheader("Project Identity")
        c1, c2 = st.columns(2)
        state.plot.book_title = c1.text_input("Project / Book Title", state.plot.book_title, help="The working name for your book or series.")
        state.plot.genre = c2.text_input("Genre / Series Type", state.plot.genre, placeholder="e.g. Epic Fantasy", help="Helps the AI select appropriate tropes and vocabulary.")
        state.plot.philosophy = st.text_area("Core Message / Philosophy", state.plot.philosophy, height=68, help="The underlying theme or message you want the story to convey.")

    # --- SECTION 2: ESTIMATES & SCALE ---
    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Scale Estimates")
        state.target_word_count = st.number_input("Target Total Word Count", min_value=1000, max_value=500000, value=state.target_word_count, step=5000, help="Total length for the book. AI will adjust pacing accordingly.")
        state.chapter_count = st.number_input("Target Chapter Count", min_value=1, max_value=100, value=state.chapter_count, help="The total number of chapters the AI will plan for.")
        
        st.caption("Main Character Limits (01a Guide)")
        lc1, lc2 = st.columns(2)
        state.min_main_chars = lc1.number_input("Min", 1, 50, state.min_main_chars, help="Minimum main characters for 01a to brainstorm.")
        state.max_main_chars = lc2.number_input("Max", state.min_main_chars, 100, state.max_main_chars, help="Maximum main characters for 01a to brainstorm.")
        
        rough_wc = state.target_word_count // state.chapter_count if state.chapter_count > 0 else 0
        st.metric("Rough Wordcount per Chapter", f"~{rough_wc} words")

    with c2:
        st.caption("📚 **Book Length & Chapter Estimates Guide**")
        guide_data = {
            "Category": ["Picture Book", "Early Reader", "Chapter Book", "Middle Grade (MG)", "Young Adult (YA)", "Fiction", "Thriller/Mystery", "Fantasy/Sci-Fi", "Non-Fiction"],
            "Word Count": ["500–1k", "1k–3k", "5k–15k", "25k–50k", "50k–80k", "70k–100k", "70k–90k", "90k–120k", "50k–80k"],
            "Chapters": ["N/A", "5–10", "10–15", "15–25", "20–30", "25–40", "40–60", "25–35", "10–15"],
            "Words/Chap": ["N/A", "200–500", "500–1k", "1.5k–2.5k", "2k–3k", "2.5k–4k", "1k–2k", "3k–5k", "4k–6k"]
        }
        st.table(pd.DataFrame(guide_data))

    # --- SECTION 3: WORLD BUILDING ---
    st.divider()
    st.subheader("World Building")
    with st.expander("Expand World Details", expanded=True):
        w1, w2 = st.columns(2)
        state.world.setting = w1.text_area("Geography & Setting", state.world.setting, height=150, help="Where the story takes place.")
        state.world.history = w2.text_area("History & Backdrop", state.world.history, height=150, help="The events leading up to the story start.")
        w3, w4 = st.columns(2)
        state.world.rules = w3.text_area("Magic / Tech / Social Rules", state.world.rules, height=150, help="The 'laws' of your world (e.g. how magic works).")
        state.world.other = w4.text_area("Other Details", state.world.other, height=150, help="Culture, religion, or other world-building notes.")
        
        if st.button("🪄 Ask Plotter to Summarize World Building", key="btn_summarize_world", use_container_width=True):
            # Future integration: workflow.run_world_summary(state)
            st.info("The plotter is currently analyzing your world notes to provide a cohesive summary...")

    # --- SECTION 4: CHARACTER PROFILES ---
    st.divider()
    st.subheader("👥 Character Profiles")
    for i, char in enumerate(state.characters):
        with st.expander(f"Character {i+1}: {char.name or 'Unnamed'}", expanded=False):
            cc1, cc2 = st.columns(2)
            char.name = cc1.text_input("Name", char.name, key=f"char_name_{i}", help="Character name.")
            char.archetype = cc2.text_input("Archetype", char.archetype, key=f"char_arch_{i}", help="e.g. The Mentor, The Rogue.")
            char.motivation = st.text_area("Motivation", char.motivation, key=f"char_mot_{i}", height=68, help="What drives this character?")
            char.notes = st.text_area("Notes", char.notes, key=f"char_notes_{i}", height=68, help="Personality, appearance, or background.")
            if st.button(f"🗑️ Remove {char.name}", key=f"char_del_{i}"):
                state.characters.pop(i)
                st.rerun()
    
    if st.button("➕ Add New Character", key="btn_add_char", use_container_width=True):
        state.characters.append(CharacterProfile())
        st.rerun()

    # --- SECTION 5: STYLE & ARCS ---
    st.divider()
    coll1, coll2 = st.columns(2)
    with coll1:
        st.subheader("Style Guide")
        state.style.tone = st.text_input("Tone", state.style.tone, help="e.g. Dark, Snarky, Whimsical.")
        state.style.voice = st.text_input("Voice", state.style.voice, help="e.g. First Person Present, Cinematic Third.")
        state.style.vocabulary = st.text_input("Vocabulary Constraints", state.style.vocabulary, help="e.g. No modern slang, scientific terms only.")
        
        prose_len = len(state.style.example_paragraphs)
        color = "red" if prose_len > 1500 else "gray"
        st.markdown(f"**Example Prose Paragraphs** :{color}[({prose_len}/1,500 characters)]")
        state.style.example_paragraphs = st.text_area("Example Prose", state.style.example_paragraphs, height=200, label_visibility="collapsed")
        
    with coll2:
        st.subheader("Narrative Arcs")
        state.plot.goals = st.text_area("Primary Plot Goals", state.plot.goals, height=68)
        state.plot.conflicts = st.text_area("Core Conflicts", state.plot.conflicts, height=68)
        state.plot.stakes = st.text_area("Stakes", state.plot.stakes, height=68)
        state.plot.twists = st.text_area("Key Twists / Revelations", state.plot.twists, height=68)

    # --- SECTION 6: AI COLLABORATION WORKSHOP ---
    st.divider()
    st.subheader("🧠 AI Collaboration Workshop")
    st.info("Use these agents to expand your ideas or audit your configurations before moving to Phase 2.")
    
    awc1, awc2 = st.columns(2)
    
    if awc1.button("🚀 Brainstorm Expansion (01a)", key="btn_workshop_brainstorm", help="Expands characters and world details based on your current notes.", use_container_width=True):
        with st.status("Workshop: 01a_brainstormer is ideating...", expanded=True) as status:
            result = workflow.run_brainstorm_ideation(state, st.write)
            state.workshop_suggestions = result.get("suggestion", "")
            status.update(label="Ideation Complete!", state="complete", expanded=True)
            st.rerun()

    if awc2.button("⚖️ Audit Continuity (01b)", key="btn_workshop_audit", help="Checks for contradictions or logic gaps in your setup.", use_container_width=True):
        with st.status("Workshop: 01b_continuity_expert is auditing...", expanded=True) as status:
            result = workflow.run_continuity_audit(state, st.write)
            state.workshop_suggestions = result.get("audit", "")
            status.update(label="Audit Complete!", state="complete", expanded=True)
            st.rerun()

    if state.workshop_suggestions:
        with st.container(border=True):
            st.markdown("### 📝 Workshop Results")
            st.markdown(state.workshop_suggestions)
            if st.button("🗑️ Clear Results", key="btn_clear_workshop"):
                state.workshop_suggestions = ""
                st.rerun()

    # --- SECTION 7: SYNC ---
    st.divider()
    if st.button("💾 Sync & Save Progress", key="btn_sync_config", type="primary", use_container_width=True):
        st.session_state.exporter.save_log(state)
        st.success("State synchronized and saved to logs!")
        st.rerun()

    st.success("Configuration updated in memory. Proceed to Phase 2: Narrative Skeleton.")

