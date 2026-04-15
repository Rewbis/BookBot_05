import streamlit as st
from src.core.state import ChapterMetadata

def render_planning_view():
    state = st.session_state.state
    client = st.session_state.client
    
    st.header("Chapter Architect")
    st.info("Define your chapters here. You can generate suggestions based on your specs or edit them manually.")

    if st.button("Add New Chapter"):
        new_num = len(state.chapters) + 1
        state.chapters.append(ChapterMetadata(chapter_number=new_num, pov=state.style.pov_global))
        st.rerun()

    if not state.chapters:
        st.warning("No chapters added yet. Click the button above to start.")
        return

    for i, chap in enumerate(state.chapters):
        with st.expander(f"📖 Chapter {chap.chapter_number}: {chap.title or 'Untitled'}"):
            c1, c2 = st.columns([3, 1])
            chap.title = c1.text_input("Chapter Title", chap.title, key=f"title_{i}")
            if c2.button("Remove", key=f"rem_{i}"):
                state.chapters.pop(i)
                st.rerun()

            p1, p2 = st.columns(2)
            chap.pov = p1.text_input("POV Character", chap.pov, key=f"pov_{i}")
            chap.key_revelation = p2.text_input("Key Revelation", chap.key_revelation, key=f"rev_{i}")

            t1, t2 = st.columns(2)
            chap.plot_thread_a = t1.text_area("Plot Thread A (Sequence)", chap.plot_thread_a, key=f"thread_a_{i}", height=100)
            chap.plot_thread_b = t2.text_area("Plot Thread B (Subplot/Setup)", chap.plot_thread_b, key=f"thread_b_{i}", height=100)

            chap.scene_notes = st.text_area("Detailed Scene Notes", chap.scene_notes, key=f"notes_{i}", height=200)

            if st.button(f"Generate Suggestion for Chapter {chap.chapter_number}", key=f"gen_{i}"):
                with st.spinner("Qwen3 is thinking..."):
                    system_prompt = (
                        f"You are a master story architect. Project: {state.plot.book_title}. "
                        f"World: {state.world.setting}. Philosophy: {state.plot.philosophy}. "
                        f"Style: {state.style.tone}, {state.style.voice}. Tense: {state.style.tense}.\n"
                        "Generate detailed chapter metadata. Focus on logic, pacing, and emotional impact."
                    )
                    user_prompt = (
                        f"Generate metadata for Chapter {chap.chapter_number}. "
                        f"Existing Plot Goals: {state.plot.goals}. Conflicts: {state.plot.conflicts}. "
                        f"Previous chapters context: {[c.title for c in state.chapters[:i]]}.\n"
                        "Return your response in these parts:\n"
                        "[TITLE]: Suggested Title\n"
                        "[POV]: The POV character\n"
                        "[THREAD_A]: What happens in the primary plot line\n"
                        "[THREAD_B]: What happens in the secondary plot line\n"
                        "[REVELATION]: The key revelation or twist for this chapter\n"
                        "[SCENE_NOTES]: Step-by-step beats for this chapter."
                    )
                    response = client.prompt(system_prompt, user_prompt)
                    st.text_area("Raw AI Suggestion (Copy/Paste if you like or use button below)", response, height=200)
                    # Simple parsing attempt (Agentic refinement could improve this)
                    if "[TITLE]:" in response:
                        try:
                            chap.title = response.split("[TITLE]:")[1].split("[")[0].strip()
                            chap.pov = response.split("[POV]:")[1].split("[")[0].strip()
                            chap.plot_thread_a = response.split("[THREAD_A]:")[1].split("[")[0].strip()
                            chap.plot_thread_b = response.split("[THREAD_B]:")[1].split("[")[0].strip()
                            chap.key_revelation = response.split("[REVELATION]:")[1].split("[")[0].strip()
                            chap.scene_notes = response.split("[SCENE_NOTES]:")[1].strip()
                            st.success("Parsed and updated chapter fields!")
                            st.rerun()
                        except:
                            st.error("Could not auto-parse the AI response. Please copy/paste manually.")
