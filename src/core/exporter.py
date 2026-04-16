import os
import json
from datetime import datetime
from .state import ProjectState

class Exporter:
    def __init__(self, base_dir="e:\\Coding\\BookBot_05"):
        self.exports_dir = os.path.join(base_dir, "exports")
        self.logs_dir = os.path.join(base_dir, "logs")
        self.skeleton_dir = os.path.join(base_dir, "skeleton_output")
        os.makedirs(self.exports_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.skeleton_dir, exist_ok=True)

    def save_log(self, state: ProjectState):
        entry = state.log_entry()
        filename = f"log_{entry['book_title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.logs_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(entry, f, indent=4)
        return filepath

    def list_logs(self):
        """Returns a list of log filenames."""
        return sorted([f for f in os.listdir(self.logs_dir) if f.endswith('.json')], reverse=True)

    def load_log(self, filename):
        """Reads a log file and returns the data dictionary."""
        filepath = os.path.join(self.logs_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_skeleton_draft(self, data: list, raw_text: str, filename: str = None):
        """Saves both the parsed JSON and the raw AI text for debugging/persistence."""
        if not filename:
            filename = f"skeleton_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save parsed JSON
        json_path = os.path.join(self.skeleton_dir, f"{filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        # Save raw text for debugging
        txt_path = os.path.join(self.skeleton_dir, f"{filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(raw_text)
            
        return json_path, txt_path

    def list_skeletons(self):
        """Lists available skeleton JSON files."""
        return sorted([f for f in os.listdir(self.skeleton_dir) if f.endswith('.json')], reverse=True)

    def load_skeleton(self, filename: str):
        """Loads a skeleton JSON file."""
        filepath = os.path.join(self.skeleton_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def export_txt_files(self, state: ProjectState):
        """Exports the state as a series of readable .txt files."""
        # World info
        world_path = os.path.join(self.exports_dir, f"{state.plot.book_title}_world_info.txt")
        with open(world_path, 'w', encoding='utf-8') as f:
            f.write(f"WORLD INFO: {state.plot.book_title}\n")
            f.write("="*40 + "\n")
            f.write(f"[SETTING]: {state.world.setting}\n")
            f.write(f"[HISTORY]: {state.world.history}\n")
            f.write(f"[RULES]: {state.world.rules}\n")
            f.write(f"[OTHER]: {state.world.other}\n")

        # Style guide
        style_path = os.path.join(self.exports_dir, f"{state.plot.book_title}_style_guide.txt")
        with open(style_path, 'w', encoding='utf-8') as f:
            f.write(f"STYLE GUIDE: {state.plot.book_title}\n")
            f.write("="*40 + "\n")
            f.write(f"[TONE]: {state.style.tone}\n")
            f.write(f"[VOICE]: {state.style.voice}\n")
            f.write(f"[VOCABULARY]: {state.style.vocabulary}\n")
            f.write(f"[GLOBAL_POV]: {state.style.pov_global}\n")
            f.write(f"[TENSE]: {state.style.tense}\n")

        # Chapter Metadata
        meta_path = os.path.join(self.exports_dir, f"{state.plot.book_title}_chapter_metadata.txt")
        with open(meta_path, 'w', encoding='utf-8') as f:
            f.write(f"CHAPTER METADATA: {state.plot.book_title}\n")
            f.write("="*40 + "\n")
            for chap in state.chapters:
                f.write(f"\n--- CHAPTER {chap.chapter_number}: {chap.title} ---\n")
                f.write(f"[POV]: {chap.pov}\n")
                f.write(f"[PLOT_THREAD_A]: {chap.plot_thread_a}\n")
                f.write(f"[PLOT_THREAD_B]: {chap.plot_thread_b}\n")
                f.write(f"[KEY_REVELATION]: {chap.key_revelation}\n")
                f.write(f"[SCENE_NOTES]:\n{chap.scene_notes}\n")

        return [world_path, style_path, meta_path]

    def format_skeleton_as_text(self, data: list) -> str:
        """Converts a skeleton list into a human-readable string."""
        lines = ["BOOK SKELETON EXPORT", "="*40, ""]
        for chap in data:
            num = chap.get('chapter_number', '?')
            title = chap.get('title', 'Untitled')
            summary = chap.get('summary', 'No summary provided.')
            lines.append(f"Chapter {num}: {title}")
            lines.append(f"{summary}")
            lines.append("")
        return "\n".join(lines)

