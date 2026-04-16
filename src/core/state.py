from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class WorldSpecs(BaseModel):
    """Container for high-level world-building specifications."""
    setting: str = ""
    history: str = ""
    rules: str = ""
    other: str = ""

class StyleSpecs(BaseModel):
    """Container for narrative style, tone, and voice constraints."""
    tone: str = ""
    voice: str = ""
    vocabulary: str = ""
    pov_global: str = "Third Person Limited"
    tense: str = "Past"

class PlotSpecs(BaseModel):
    """Container for the core plot premise, goals, and conflicts."""
    book_title: str = "Untitled Project"
    goals: str = ""
    conflicts: str = ""
    stakes: str = ""
    twists: str = ""
    philosophy: str = ""

class ChapterMetadata(BaseModel):
    """Detailed metadata for a single chapter, including POV and scene notes."""
    chapter_number: int
    title: str = ""
    summary: str = ""
    pov: str = ""
    plot_thread_a: str = ""
    plot_thread_b: str = ""
    key_revelation: str = ""
    scene_notes: str = ""

class ProjectState(BaseModel):
    """Root model representing the entire state of a book project."""
    world: WorldSpecs = Field(default_factory=WorldSpecs)
    style: StyleSpecs = Field(default_factory=StyleSpecs)
    plot: PlotSpecs = Field(default_factory=PlotSpecs)
    chapters: List[ChapterMetadata] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    def log_entry(self):
        """Return a dictionary representation of the state for logging and persistence."""
        return {
            "book_title": self.plot.book_title,
            "date": self.last_updated.strftime("%Y-%m-%d"),
            "time": self.last_updated.strftime("%H:%M:%S"),
            "data": self.model_dump(mode='json')
        }
