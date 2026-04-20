import pytest
import json
from src.core.workflow import NarrativeWorkflow

def test_run_skeleton_generation_success(mocker, sample_state):
    """Verify that skeleton generation correctly orchestrates multiple agent turns."""
    mock_agents = mocker.Mock()
    mock_exporter = mocker.Mock()
    
    # Mock plotter success
    mock_agents.run_skeleton_planner_turn.return_value = {"chapters": []}
    # Mock critic
    mock_agents.run_skeleton_critic_turn.return_value = "Critique"
    # Mock formatter
    mock_agents.run_skeleton_formatter_turn.return_value = {"chapters": [{"chapter_number": 1, "title": "Test"}]}
    # Mock exporter
    mock_exporter.save_skeleton_draft.return_value = ("path/to/json", "path/to/txt")
    
    workflow = NarrativeWorkflow(mock_agents, mock_exporter)
    status_calls = []
    
    result = workflow.run_skeleton_generation(sample_state, 1, status_calls.append)
    
    assert "error" not in result
    assert result["chapters"][0]["title"] == "Test"
    assert len(status_calls) >= 5  # Should have status updates for each step
    assert mock_agents.run_skeleton_planner_turn.call_count == 2 # Initial + Refinement

def test_run_chapter_detailing_success(mocker, sample_state):
    """Verify that chapter detailing correctly orchestrates plotting and critique."""
    mock_agents = mocker.Mock()
    mock_exporter = mocker.Mock()
    
    mock_agents.run_architect_turn.return_value = {"title": "Refined"}
    mock_agents.run_architect_critic_turn.return_value = "Final Critic Thoughts"
    
    workflow = NarrativeWorkflow(mock_agents, mock_exporter)
    status_calls = []
    
    result = workflow.run_chapter_detailing(sample_state, 1, "Context Summary", status_calls.append)
    
    assert "error" not in result
    assert result["draft_json"]["title"] == "Refined"
    assert result["final_qa"] == "Final Critic Thoughts"
    assert mock_agents.run_architect_turn.call_count == 2 # Initial + Refined
