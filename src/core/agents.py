import json
import re
from typing import List, Optional
from .state import ProjectState, ChapterMetadata
from .llm_client import OllamaClient

class BookBotAgents:
    """Provides a suite of specialized agents for narrative plotting and critique."""

    def __init__(self, client: OllamaClient):
        """Initialize with an LLM client."""
        self.client = client

    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a string using a character-based heuristic."""
        return len(text) // 4

    def get_context_summary(self, chapters: List[ChapterMetadata], count: int = 5) -> str:
        """Return a formatted summary of the most recent chapters for context."""
        recent = chapters[-count:] if chapters else []
        summary = ""
        for c in recent:
            summary += f"Chapter {c.chapter_number} ({c.title}): {c.key_revelation}. Threads: {c.plot_thread_a}, {c.plot_thread_b}\n"
        return summary

    def run_plotter_turn(self, state: ProjectState, chap_num: int, context_summary: str, critique: Optional[str] = None, previous_draft: Optional[str] = None):
        """Execute a plotter turn to generate or refine a detailed chapter outline."""
        
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
        """Execute a skeleton plotter turn to generate or refine the project-wide outline."""
        system_prompt = (
            "You are '01a_skeleton_plotter', an expert story architect. Your task is to design the high-level skeleton "
            f"of a {count}-chapter book. You MUST respond in valid JSON format only."
        )

        user_content = (
            "### PROJECT SPECIFICATIONS\n"
            f"- Title: {state.plot.book_title}\n"
            f"- World: {state.world.setting}\n"
            f"- Goals: {state.plot.goals}\n"
            f"- Conflicts: {state.plot.conflicts}\n"
            f"- Philosophy: {state.plot.philosophy}\n\n"
        )

        if state.chapters and not previous_draft:
             user_content += "### EXISTING CHAPTER WORK (KEEP THESE IN YOUR NEW SKELETON)\n"
             user_content += "\n".join([f"Ch {c.chapter_number}: {c.title} - {c.summary}" for c in state.chapters if c.summary]) + "\n\n"

        if critique and previous_draft:
            user_content += "### PREVIOUS SKELETON DRAFT\n"
            user_content += f"```json\n{previous_draft}\n```\n\n"
            user_content += "### CRITIQUE FROM 01b_skeleton_critic\n"
            user_content += f"{critique}\n\n"
            user_content += "**TASK:** Refine the skeleton above by addressing ALL points in the critique. Ensure story consistency is maintained.\n"
        else:
            user_content += f"**TASK:** Generate a fresh {count}-chapter skeleton. Each chapter MUST have a title and a SINGLE PARAGRAPH of high-level description.\n"

        user_content += (
            "\n### REQUIRED JSON FORMAT\n"
            "Return ONLY a valid JSON object. Do not include any conversational preamble. "
            "Your response must start with '{'.\n"
            "```json\n"
            "{\n"
            "  \"chapters\": [\n"
            "    {\"chapter_number\": 1, \"title\": \"Title\", \"summary\": \"Description...\"},\n"
            "    ...\n"
            "  ]\n"
            "}\n"
            "```"
        )

        response = self.client.prompt(system_prompt, user_content)
        return self._clean_json(response)



    def run_skeleton_formatter_turn(self, raw_outline: str, target_count: int):
        """Convert creative prose narrative into a strict JSON chapter structure."""
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
        """Evaluate the project skeleton for structural integrity and pacing."""
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



    def extract_recommendations(self, text: str) -> List[str]:
        """Parse bulleted recommendations from an agent's critique text."""
        # Find the section starting with 'Recommendations'
        match = re.search(r'(?:Recommendations|Advice for the Plotter).*?\n(.*?)(?:\n\n|\Z|###|---)', text, re.DOTALL | re.IGNORECASE)
        if not match:
            return []
        
        section_content = match.group(1)
        # Extract lines starting with bullet points (- or *)
        recommendations = re.findall(r'^[ \t]*[-*][ \t]*(.+)$', section_content, re.MULTILINE)
        return [r.strip() for r in recommendations if r.strip()]

    def analyze_impact(self, state: ProjectState, changed_index: int, new_content: str):
        """Identify potential ripple effects and contradictions caused by a chapter change."""
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
        """Execute a critic turn to evaluate a detailed chapter draft."""
        
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
                "[SUMMARY]: General status and if it's ready.\n"
                "[STRENGTHS]: What works well.\n"
                "[AREAS FOR TIGHTENING]: What could be better."
            )
        else:
            user_content += "Identify flaws, pacing issues, or missed opportunities. Provide specific advice for the plotter to improve this draft."


        return self.client.prompt(system_prompt, user_content)

    def _clean_json(self, text: str):
        """Extract and parse a JSON block from potentially noisy agent output."""
        # 1. Remove reasoning blocks like <think>...</think>
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # 2. Extract content between first and last curly brace
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                # If direct load fails, try a aggressive filter for code blocks
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except: pass
                
                print(f"DEBUG: Failed to parse JSON. Error: {e}")
                print(f"DEBUG: Raw Text Snippet: {text[:200]}...")
                return {"error": f"JSON Parse Error: {str(e)}", "raw": text}

        print("DEBUG: No JSON braces found in response.")
        print(f"DEBUG: Raw Text: {text}")
        return {"error": "JSON Parse Error: No JSON block found in response.", "raw": text}
