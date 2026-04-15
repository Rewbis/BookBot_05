import streamlit as st

def render_spec_form():
    state = st.session_state.state
    
    st.header("Step 1: Project Identity & Plot Core")
    col1, col2 = st.columns(2)
    state.plot.book_title = col1.text_input("Project / Book Title", state.plot.book_title)
    state.plot.philosophy = col2.text_input("Underlying Message / Philosophy", state.plot.philosophy)
    
    col3, col4, col5 = st.columns(3)
    state.plot.goals = col3.text_area("Plot Goals", state.plot.goals, height=100)
    state.plot.conflicts = col4.text_area("Core Conflicts", state.plot.conflicts, height=100)
    state.plot.stakes = col5.text_area("Stakes", state.plot.stakes, height=100)
    
    state.plot.twists = st.text_area("Key Twists", state.plot.twists, height=100)
    
    st.divider()
    
    st.header("Step 2: World Building")
    w_col1, w_col2 = st.columns(2)
    state.world.setting = w_col1.text_area("Setting / Geography", state.world.setting, height=150)
    state.world.history = w_col2.text_area("History / Timeline", state.world.history, height=150)
    
    w_col3, w_col4 = st.columns(2)
    state.world.rules = w_col3.text_area("Societal / Magic / Tech Rules", state.world.rules, height=150)
    state.world.other = w_col4.text_area("Other Details", state.world.other, height=150)
    
    st.divider()
    
    st.header("Step 3: Style Guide")
    s_col1, s_col2, s_col3 = st.columns(3)
    state.style.tone = s_col1.text_input("Tone (e.g. Gritty, Whimsical)", state.style.tone)
    state.style.voice = s_col2.text_input("Voice (e.g. First Person, Cynical)", state.style.voice)
    state.style.vocabulary = s_col3.text_input("Vocabulary Constraints", state.style.vocabulary)
    
    s_col4, s_col5 = st.columns(2)
    state.style.pov_global = s_col4.selectbox("Global POV", ["Third Person Limited", "Third Person Omniscient", "First Person"], index=0)
    state.style.tense = s_col5.selectbox("Tense", ["Past", "Present"], index=0)

    st.success("Specifications updated in memory. Switch to Chapter Planning to begin architecting.")
