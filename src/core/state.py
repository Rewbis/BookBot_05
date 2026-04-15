from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class WorldSpecs(BaseModel):
    setting: str = ""
    history: str = ""
    rules: str = ""
    other: str = ""

class StyleSpecs(BaseModel):
    tone: str = ""
    voice: str = ""
    vocabulary: str = ""
    pov_global: str = "Third Person Limited"
    tense: str = "Past"

class PlotSpecs(BaseModel):
    book_title: str = "Untitled Project"
    goals: str = ""
    conflicts: str = ""
    stakes: str = ""
    twists: str = ""
    philosophy: str = ""

class ChapterMetadata(BaseModel):
    chapter_number: int
    title: str = ""
    pov: str = ""
    plot_thread_a: str = ""
    plot_thread_b: str = ""
    key_revelation: str = ""
    scene_notes: str = ""

class ProjectState(BaseModel):
    world: WorldSpecs = Field(default_factory=WorldSpecs)
    style: StyleSpecs = Field(default_factory=StyleSpecs)
    plot: PlotSpecs = Field(default_factory=PlotSpecs)
    chapters: List[ChapterMetadata] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    def log_entry(self):
        return {
            "book_title": self.plot.book_title,
            "date": self.last_updated.strftime("%Y-%m-%d"),
            "time": self.last_updated.strftime("%H:%M:%S"),
            "data": self.model_dump(mode='json')
        }
