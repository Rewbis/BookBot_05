import os
import json
import pytest
from src.core.exporter import Exporter
from src.core.state import ProjectState

def test_exporter_path_initialization(tmp_path):
    """Verify that Exporter correctly initializes directories."""
    exporter = Exporter(base_dir=str(tmp_path))
    assert os.path.exists(exporter.exports_dir)
    assert os.path.exists(exporter.logs_dir)
    assert os.path.exists(exporter.skeleton_dir)

def test_save_and_load_log(tmp_path, sample_state):
    """Verify that saving and loading a log preserves state data."""
    exporter = Exporter(base_dir=str(tmp_path))
    path = exporter.save_log(sample_state, "test_checkpoint")
    
    filename = os.path.basename(path)
    loaded_data = exporter.load_log(filename)
    
    assert loaded_data["book_title"] == "Test Book"
    assert "data" in loaded_data
    assert loaded_data["data"]["plot"]["book_title"] == "Test Book"

def test_save_skeleton_draft(tmp_path):
    """Verify that skeleton drafts are saved in both JSON and TXT formats."""
    exporter = Exporter(base_dir=str(tmp_path))
    sample_data = [{"chapter_number": 1, "title": "Test"}]
    raw_text = "Raw AI response"
    
    json_p, txt_p = exporter.save_skeleton_draft(sample_data, raw_text, "test_skel")
    
    assert os.path.exists(json_p)
    assert os.path.exists(txt_p)
    
    with open(json_p, 'r') as f:
        data = json.load(f)
        assert data[0]["title"] == "Test"
    
    with open(txt_p, 'r') as f:
        assert f.read() == raw_text
