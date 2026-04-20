from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CharacterProfile(BaseModel):
    """Container for a single character's data."""
    name: str = ""
    motivation: str = ""
    archetype: str = ""
    notes: str = ""

class WorldSpecs(BaseModel):
    """Container for high-level world-building specifications."""
    setting: str = ""
    history: str = ""
    rules: str = ""
    other: str = ""
    ai_summary: str = ""  # For the AI summarization loop

class StyleSpecs(BaseModel):
    """Container for narrative style, tone, and voice constraints."""
    tone: str = ""
    voice: str = ""
    vocabulary: str = ""
    pov_global: str = "Third Person Limited"
    tense: str = "Past"
    example_paragraphs: str = ""

class PlotSpecs(BaseModel):
    """Container for the core plot premise, goals, and conflicts."""
    book_title: str = "Untitled Project"
    genre: str = ""
    goals: str = ""
    conflicts: str = ""
    stakes: str = ""
    twists: str = ""
    philosophy: str = ""

class ChapterDraft(BaseModel):
    """Container for prose drafting iterations and continuity tracking."""
    v1_raw: str = ""
    critic_notes: str = ""
    v2_refined: str = ""
    user_approved: bool = False
    final_prose: str = ""
    continuity_memo: str = "" # The 3-sentence summary from 04c

class ChapterMetadata(BaseModel):
    """Detailed metadata for a single chapter (the 'Chapter Map')."""
    chapter_number: int
    title: str = ""
    summary: str = ""  # Skeleton part
    # Detailed part (Architect Phase)
    pov: str = ""
    tense: str = ""
    key_revelation: str = ""
    plot_thread_a: str = ""
    plot_thread_b: str = ""
    scene_notes: str = ""  # Beats
    
    # Phase 4 Data
    draft: ChapterDraft = Field(default_factory=ChapterDraft)

class ProjectState(BaseModel):
    """Root model representing the entire state of a book project."""
    world: WorldSpecs = Field(default_factory=WorldSpecs)
    style: StyleSpecs = Field(default_factory=StyleSpecs)
    plot: PlotSpecs = Field(default_factory=PlotSpecs)
    characters: List[CharacterProfile] = Field(default_factory=list)
    chapters: List[ChapterMetadata] = Field(default_factory=list)
    
    # Global Config & Estimates
    target_word_count: int = 50000
    chapter_count: int = 20
    min_main_chars: int = 1
    max_main_chars: int = 15
    
    # Persistent UI/Workflow State (Handover)
    current_tab: str = "Phase 1: Configuration"
    workshop_suggestions: str = "" # Storage for 01a/01b results in Phase 1
    
    # In-flight Drafts (Transient data to be persisted)
    temp_skel_draft: Optional[List[Dict[str, Any]]] = None
    temp_skel_critic: str = ""
    temp_skel_prose: str = ""  # The raw AI prose before formatting
    
    active_chapter_idx: Optional[int] = None
    active_chapter_draft: Optional[Dict[str, Any]] = None
    active_chapter_critic: str = ""
    
    last_updated: datetime = Field(default_factory=datetime.now)

    def log_entry(self):
        """Return a dictionary representation of the state for logging and persistence."""
        return {
            "book_title": self.plot.book_title,
            "date": self.last_updated.strftime("%Y-%m-%d"),
            "time": self.last_updated.strftime("%H:%M:%S"),
            "data": self.model_dump(mode='json')
        }
