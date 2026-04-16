import streamlit as st

def render_spec_form():
    """Render the initial project specification form for world, plot, and style."""
    state = st.session_state.state
    
    st.header("Step 1: Project Identity & Plot Core")
    col1, col2 = st.columns(2)
    state.plot.book_title = col1.text_input(
        "Project / Book Title", 
        state.plot.book_title,
        help="The working title of your project. This will be used in all exports."
    )
    state.plot.philosophy = col2.text_input(
        "Underlying Message / Philosophy", 
        state.plot.philosophy,
        help="The core thematic or philosophical driver behind the story."
    )
    
    col3, col4, col5 = st.columns(3)
    state.plot.goals = col3.text_area(
        "Plot Goals", 
        state.plot.goals, 
        height=100,
        help="What are the essential plot milestones or structural goals of the book?"
    )
    state.plot.conflicts = col4.text_area(
        "Core Conflicts", 
        state.plot.conflicts, 
        height=100,
        help="The primary internal and external struggles driving the narrative."
    )
    state.plot.stakes = col5.text_area(
        "Stakes", 
        state.plot.stakes, 
        height=100,
        help="What is at risk if the characters fail to achieve their goals?"
    )
    
    state.plot.twists = st.text_area(
        "Key Twists", 
        state.plot.twists, 
        height=100,
        help="List specific revelations or plot turns you want the AI to incorporate."
    )
    
    st.divider()
    
    st.header("Step 2: World Building")
    w_col1, w_col2 = st.columns(2)
    state.world.setting = w_col1.text_area(
        "Setting / Geography", 
        state.world.setting, 
        height=150,
        help="Describe the physical environment, locations, and geography."
    )
    state.world.history = w_col2.text_area(
        "History / Timeline", 
        state.world.history, 
        height=150,
        help="Key historical events or the immediate backstory leading into the book."
    )
    
    w_col3, w_col4 = st.columns(2)
    state.world.rules = w_col3.text_area(
        "Societal / Magic / Tech Rules", 
        state.world.rules, 
        height=150,
        help="The 'laws of the land'—how magic, technology, or society functions."
    )
    state.world.other = w_col4.text_area(
        "Other Details", 
        state.world.other, 
        height=150,
        help="Any additional world-building data (factions, flora/fauna, etc.)."
    )
    
    st.divider()
    
    st.header("Step 3: Style Guide")
    s_col1, s_col2, s_col3 = st.columns(3)
    state.style.tone = s_col1.text_input(
        "Tone (e.g. Gritty, Whimsical)", 
        state.style.tone,
        help="The overall emotional feel of the prose."
    )
    state.style.voice = s_col2.text_input(
        "Voice (e.g. First Person, Cynical)", 
        state.style.voice,
        help="The personality of the narrator or the narrative perspective."
    )
    state.style.vocabulary = s_col3.text_input(
        "Vocabulary Constraints", 
        state.style.vocabulary,
        help="Specific word choices, dialects, or level of complexity to use/avoid."
    )
    
    s_col4, s_col5 = st.columns(2)
    state.style.pov_global = s_col4.selectbox(
        "Global POV", 
        ["Third Person Limited", "Third Person Omniscient", "First Person"], 
        index=0,
        help="The default point-of-view strategy for the entire book."
    )
    state.style.tense = s_col5.selectbox(
        "Tense", 
        ["Past", "Present"], 
        index=0,
        help="The default narrative tense for the book."
    )

    st.success("Specifications updated in memory. Switch to Chapter Planning to begin architecting.")

