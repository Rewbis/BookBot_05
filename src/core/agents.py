import json
import re
from typing import List, Optional
from .state import ProjectState, ChapterMetadata
from .llm_client import OllamaClient

class BookBotAgents:
    def __init__(self, client: OllamaClient):
        self.client = client

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens: characters / 4."""
        return len(text) // 4

    def get_context_summary(self, chapters: List[ChapterMetadata], count: int = 5) -> str:
        """Summarizes the last 'count' chapters for context."""
        recent = chapters[-count:] if chapters else []
        summary = ""
        for c in recent:
            summary += f"Chapter {c.chapter_number} ({c.title}): {c.key_revelation}. Threads: {c.plot_thread_a}, {c.plot_thread_b}\n"
        return summary

    def run_plotter_turn(self, state: ProjectState, chap_num: int, context_summary: str, critique: Optional[str] = None, previous_draft: Optional[str] = None):
        """01a_plotter turn: Initial draft or refinement based on critique."""
        
        system_prompt = (
            "You are '02a_plotter', an expert story architect. Your goal is to design a single chapter outline "
            "that fits perfectly into the existing story structure. You MUST respond in valid JSON format only."
        )

        user_content = (
            f"PROJECT SPECS:\nTitle: {state.plot.book_title}\nWorld: {state.world.setting}\n"
            f"Goals: {state.plot.goals}\nConflicts: {state.plot.conflicts}\n"
            f"Tone/Voice: {state.style.tone}, {state.style.voice}\n\n"
            f"BOOK SKELETON SUMMARY FOR THIS CHAPTER:\n{state.chapters[chap_num-1].summary if len(state.chapters) >= chap_num else 'N/A'}\n\n"
            f"CONTEXT (Previous Chapters):\n{context_summary}\n\n"
            f"TASK: Generate the detailed outline for Chapter {chap_num}.\n"
        )

        if critique and previous_draft:
            user_content += (
                f"\nPREVIOUS DRAFT:\n{previous_draft}\n\n"
                f"CRITIQUE FROM 02b_critic:\n{critique}\n\n"
                "Refine the draft by addressing ALL points in the critique while maintaining story consistency."
            )
        else:
            user_content += "Create a fresh draft for this chapter."

        user_content += (
            "\n\nJSON STRUCTURE REQUIRED:\n"
            "{\n"
            "  \"title\": \"Chapter Title\",\n"
            "  \"pov\": \"POV Character\",\n"
            "  \"plot_thread_a\": \"Sequence/Primary Plot\",\n"
            "  \"plot_thread_b\": \"Subplot/Setup\",\n"
            "  \"key_revelation\": \"The big twist or discovery\",\n"
            "  \"scene_notes\": \"Detailed beat-by-beat notes\"\n"
            "}"
        )

        response = self.client.prompt(system_prompt, user_content)
        return self._clean_json(response)

    def run_skeleton_plotter_turn(self, state: ProjectState, count: int, critique: Optional[str] = None, previous_draft: Optional[str] = None):
        """Phase 1: Generates the book-wide skeleton."""
        system_prompt = (
            "You are '01a_skeleton_plotter', an expert story architect. Your task is to design the high-level skeleton "
            f"of a {count}-chapter book. You MUST respond in valid JSON format only."
        )

        user_content = (
            f"PROJECT SPECS:\nTitle: {state.plot.book_title}\nWorld: {state.world.setting}\n"
            f"Goals: {state.plot.goals}\nConflicts: {state.plot.conflicts}\n"
            f"Philosophy: {state.plot.philosophy}\n\n"
            f"EXISTING CHAPTER WORK (KEEP THESE IN YOUR NEW SKELETON):\n"
            + "\n".join([f"Ch {c.chapter_number}: {c.title} - {c.summary}" for c in state.chapters if c.summary]) + "\n\n"
            f"TASK: Generate a {count}-chapter skeleton. Each chapter MUST have a title and a SINGLE PARAGRAPH of high-level description. "
            "This paragraph should cover the major events, key people involved, and important locations."
        )

        if critique and previous_draft:
            user_content += f"\n\nPREVIOUS SKELETON:\n{previous_draft}\n\nCRITIQUE FROM 01b_skeleton_critic:\n{critique}\n\nRefine the skeleton based on this feedback."

        user_content += (
            "\n\nJSON STRUCTURE REQUIRED:\n"
            "{\n"
            "  \"chapters\": [\n"
            "    {\"chapter_number\": 1, \"title\": \"Chapter Title\", \"summary\": \"High-level paragraph description...\"},\n"
            "    ...\n"
            "  ]\n"
            "}"
        )

        response = self.client.prompt(system_prompt, user_content)
        return self._clean_json(response)

    def run_skeleton_formatter_turn(self, raw_outline: str, target_count: int):
        """Phase 1 Step 4: Converts creative prose to strict JSON."""
        system_prompt = (
            "You are '01c_skeleton_formatter', a data extraction specialist. Your task is to take a creative book "
            "outline (prose) and convert it into a strict JSON structure. Do NOT add new plot points."
        )
        
        user_content = (
            f"CREATIVE OUTLINE:\n{raw_outline}\n\n"
            f"TASK: Convert the creative outline above into exactly {target_count} chapters. "
            "You MUST output every single chapter requested. Do NOT skip chapters or summarize multiple chapters into one. "
            "Each chapter summary must be a single, detailed paragraph."
            "\n\nJSON STRUCTURE REQUIRED (ONE SINGLE BLOCK):\n"
            "{\n"
            "  \"chapters\": [\n"
            "    {\"chapter_number\": 1, \"title\": \"Title\", \"summary\": \"Single paragraph description...\"},\n"
            "    ...\n"
            "  ]\n"
            "}"
        )
        
        response = self.client.prompt(system_prompt, user_content)
        return self._clean_json(response)

    def run_skeleton_critic_turn(self, state: ProjectState, content: str, is_final: bool = False):
        """Phase 1: Evaluates the book-wide skeleton (prose in Step 2, JSON in Step 5)."""
        role_desc = "literature expert and antagonistic critic" if not is_final else "literature expert providing final QA on the structured skeleton"
        system_prompt = f"You are '01b_skeleton_critic', a {role_desc}. Evaluate the book skeleton for pacing, twists, and structural integrity."
        
        if is_final:
            user_content = (
                f"PROJECT SPECS:\nTitle: {state.plot.book_title}\nGoals: {state.plot.goals}\n\n"
                f"FINAL STRUCTURED SKELETON (JSON):\n{content}\n\n"
                "TASK: Provide a final assessment of this structured plan. You MUST include:\n"
                "1. Exactly 3 Bullet Points for 'Key Strengths'.\n"
                "2. Exactly 3 Bullet Points for 'Areas for Tightening'.\n"
                "3. Sections: [FINAL THOUGHTS], [INTERNAL LOGIC & THEMES], and [VERDICT]."
            )
        else:
            user_content = f"PROJECT SPECS:\nTitle: {state.plot.book_title}\nGoals: {state.plot.goals}\n\nSKELETON DRAFT:\n{content}"
            user_content += "\n\nIdentify structural flaws or boring stretches. Give advice to the plotter."

        return self.client.prompt(system_prompt, user_content)



    def analyze_impact(self, state: ProjectState, changed_index: int, new_content: str):
        """Phase 2: Detects ripple effects when a chapter is modified."""
        system_prompt = (
            "You are '02b_critic' performing an Impact Analysis. When a chapter changes, you must identify "
            "how it breaks or affects the rest of the book's skeleton."
        )

        skeleton_text = ""
        for i, c in enumerate(state.chapters):
            skeleton_text += f"Chapter {c.chapter_number}: {c.summary}\n"

        user_content = (
            "THE WHOLE BOOK SKELETON:\n" + skeleton_text + "\n"
            f"CHANGE DETECTED IN CHAPTER {changed_index + 1}:\n"
            f"New content/details: {new_content}\n\n"
            "TASK: Analyze if this change creates contradictions or missed opportunities in subsequent chapters. "
            "If it does, list which chapters are impacted and suggest how their skeleton summaries should be updated. "
            "If no impact, simply say 'No ripple effects detected.'"
        )

        return self.client.prompt(system_prompt, user_content)

    def run_critic_turn(self, state: ProjectState, chap_num: int, context_summary: str, draft: str, is_final: bool = False):
        """02b_critic turn: Evaluation of the plotter's output."""
        
        role_desc = "literature expert and antagonistic critic" if not is_final else "literature expert providing final thoughts for the user"
        system_prompt = (
            f"You are '02b_critic', a {role_desc}. Your goal is to evaluate the plotter's draft for Chapter {chap_num} "
            f"against the story's pacing, goals, and internal logic. Be sharp, direct, and insightful."
        )

        user_content = (
            f"PROJECT SPECS:\nTitle: {state.plot.book_title}\nGoals: {state.plot.goals}\n\n"
            f"CONTEXT (Previous Chapters):\n{context_summary}\n\n"
            f"DRAFT FOR CHAPTER {chap_num}:\n{draft}\n\n"
        )

        if is_final:
            user_content += (
                "Provide your final assessment of this refined chapter in exactly these sections:\n"
                "[FINAL THOUGHTS]: General summary.\n"
                "[STRENGTHS]: What works well.\n"
                "[AREAS FOR TIGHTENING]: What could be better.\n"
                "[INTERNAL LOGIC & THEMES]: Philosophical or logical consistency.\n"
                "[VERDICT]: Final recommendation (e.g., Approved, Needs minor polish, etc.)."
            )
        else:
            user_content += "Identify flaws, pacing issues, or missed opportunities. Provide specific advice for the plotter to improve this draft."

        return self.client.prompt(system_prompt, user_content)

    def _clean_json(self, text: str):
        """Attempts to extract JSON from a string that might contain reasoning tags or multiples."""
        # 1. Remove reasoning blocks like <think>...</think>
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # 2. Find the outermost braces to handle nested structures
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If direct load fails, try to fix common issues or fallback to regex
                pass

        try:
            # Fallback: greedy match for the largest block
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            
            # Final fallback: raw text
            return json.loads(text)
        except Exception as e:
            # Check if it's "too many chapters" or just garbage
            return {"error": f"JSON Parse Error: {str(e)}", "raw": text}
