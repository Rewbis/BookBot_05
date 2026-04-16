import pytest
from src.core.state import ProjectState, WorldSpecs, PlotSpecs, StyleSpecs, ChapterMetadata

@pytest.fixture
def sample_state():
    """Return a ProjectState with sample data."""
    state = ProjectState()
    state.plot.book_title = "Test Book"
    state.world.setting = "Test World"
    state.chapters = [
        ChapterMetadata(chapter_number=1, title="Ch 1", summary="Summary 1"),
        ChapterMetadata(chapter_number=2, title="Ch 2", summary="Summary 2")
    ]
    return state

@pytest.fixture
def mock_agents(mocker):
    """Return a mock for BookBotAgents."""
    return mocker.Mock()

@pytest.fixture
def mock_exporter(mocker):
    """Return a mock for Exporter."""
    return mocker.Mock()
