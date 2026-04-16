import pytest
from src.core.agents import BookBotAgents

def test_estimate_tokens():
    """Verify that token estimation follows the characters/4 heuristic."""
    agents = BookBotAgents(None)
    assert agents.estimate_tokens("ABCD") == 1
    assert agents.estimate_tokens("12345678") == 2

def test_clean_json_valid():
    """Verify that _clean_json correctly parses valid JSON blocks."""
    agents = BookBotAgents(None)
    raw = 'Here is the JSON: {"key": "value"}'
    cleaned = agents._clean_json(raw)
    assert cleaned == {"key": "value"}

def test_clean_json_with_think_tags():
    """Verify that _clean_json strips <think> tags."""
    agents = BookBotAgents(None)
    raw = '<think>I should use a dict.</think>{"key": "value"}'
    cleaned = agents._clean_json(raw)
    assert cleaned == {"key": "value"}

def test_clean_json_failed_returns_error():
    """Verify that _clean_json returns an error dict on invalid input."""
    agents = BookBotAgents(None)
    raw = "Not JSON at all"
    cleaned = agents._clean_json(raw)
    assert "error" in cleaned
    assert "No JSON block found" in cleaned["error"]
