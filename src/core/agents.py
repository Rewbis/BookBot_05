import json
import re
import os
from datetime import datetime
from typing import List, Optional
from .state import ProjectState, ChapterMetadata
from .llm_client import OllamaClient

class BookBotAgents:
    """Provides a suite of specialized agents for narrative plotting and critique."""

    def __init__(self, client: OllamaClient):
        """
        Initialize with an LLM client.

        Args:
            client (OllamaClient): The client used to communicate with the Ollama server.
        """
        self.client = client

    def run_brainstormer_turn(self, state: ProjectState) -> Dict[str, Any]:
        """
        Execute a brainstorming turn to expand on Phase 1 project specs.

        Args:
            state (ProjectState): The current project state.

        Returns:
            Dict[str, Any]: A dictionary containing the brainstormed suggestions and token usage.
        """
        system_prompt = (
            "You are '01a_brainstormer', a creative consultant for novelists. Your task is to take a set of "
            "preliminary story notes and expand them into rich, actionable ideas for characters, world-building, "
            "and plot seeds. BE CREATIVE and push for unique twists."
        )

        user_content = (
            f"### CURRENT SPECS\nTitle: {state.plot.book_title}\nGenre: {state.plot.genre}\n"
            f"Philosophy/Theme: {state.plot.philosophy}\n"
            f"Setting: {state.world.setting}\nHistory: {state.world.history}\n"
            f"Plot Goals: {state.plot.goals}\nConflicts: {state.plot.conflicts}\n\n"
            f"### CONSTRAINTS\n"
            f"- Main Characters: Aim for between {state.min_main_chars} and {state.max_main_chars} main characters.\n"
            "- Secondary Characters: Suggest as many as are sensible to flesh out the world.\n\n"
            "### TASK\nProvide a detailed expansion covering:\n"
            "1. Deepened World Building (Geography, History, Rules).\n"
            "2. Character Roster (Names, Archetypes, Secret Motivations).\n"
            "3. Secondary Characters & Factions.\n"
            "4. Additional Plot Seeds & Subplot ideas."
        )

        response = self.client.prompt(system_prompt, user_content)
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        return {"suggestion": response, "_tokens": total_tokens}

    def run_continuity_expert_turn(self, state: ProjectState) -> Dict[str, Any]:
        """
        Analyze Phase 1 specs for contradictions and logic gaps.

        Args:
            state (ProjectState): The current project state.

        Returns:
            Dict[str, Any]: A dictionary containing the continuity audit results.
        """
        system_prompt = (
            "You are '01b_continuity_expert', a logic specialist and story editor. Your task is to audit "
            "a project's high-level configuration and identify ANY contradictions, logic gaps, or inconsistencies."
        )

        user_content = (
            f"### PROJECT SPECS\nTitle: {state.plot.book_title}\nGenre: {state.plot.genre}\n"
            f"Philosophy: {state.plot.philosophy}\n"
            f"Setting: {state.world.setting}\nRules: {state.world.rules}\n"
            f"Goals: {state.plot.goals}\nConflicts: {state.plot.conflicts}\n"
            f"Twists: {state.plot.twists}\n"
            f"Characters: " + ", ".join([f"{c.name} ({c.archetype})" for c in state.characters]) + "\n\n"
            "### TASK\nPerform a comprehensive audit. Look for:\n"
            "1. Rules Contradictions (e.g., world rules vs. character abilities).\n"
            "2. Motivation Issues (e.g., character motivation vs. plot stakes).\n"
            "3. Pacing Concerns (e.g., too many twists for the target word count).\n"
            "4. Missing Elements (e.g., a setting mentioned in plot but not in world building)."
        )

        response = self.client.prompt(system_prompt, user_content)
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        return {"audit": response, "_tokens": total_tokens}

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate tokens using a hybrid heuristic.
        - 1 token per 3.8 characters (conservative for English).
        - Add overhead for prompt structures.
        """
        if not text:
            return 0
        return int(len(text) / 3.8) + 10

    def get_context_summary(self, chapters: List[ChapterMetadata], count: int = 5) -> str:
        """Return a formatted summary of the most recent chapters for context."""
        recent = chapters[-count:] if chapters else []
        summary = ""
        for c in recent:
            summary += f"Chapter {c.chapter_number} ({c.title}): {c.key_revelation}. Threads: {c.plot_thread_a}, {c.plot_thread_b}\n"
        return summary

    def run_architect_turn(self, state: ProjectState, chap_num: int, context_summary: str, critique: Optional[str] = None, previous_draft: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an architect turn to generate or refine a detailed chapter outline (Phase 3).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Target chapter number.
            context_summary (str): Summary of previous chapters.
            critique (Optional[str]): Feedback from 03b_architect_critic.
            previous_draft (Optional[str]): The draft before refinement.

        Returns:
            Dict[str, Any]: The detailed architect map as JSON.
        """
        system_prompt = (
            "You are '03a_architect', an expert story architect. Your goal is to design a single chapter outline "
            "that fits perfectly into the existing story structure. You MUST respond in valid JSON format only. "
            "Do NOT include conversational preamble, explanations, or any text outside the JSON block."
        )

        # Context Truncation (Safety)
        style_sample = state.style.example_paragraphs[:1500]
        context_truncated = context_summary[-2000:] if context_summary else ""

        user_content = (
            f"PROJECT SPECS:\nTitle: {state.plot.book_title}\nGenre: {state.plot.genre}\nWorld: {state.world.setting}\n"
            f"Goals: {state.plot.goals}\nConflicts: {state.plot.conflicts}\n"
            f"Tone/Voice: {state.style.tone}, {state.style.voice}\n"
            f"Global Tense: {state.style.tense}\n\n"
            f"STYLE EXAMPLES:\n{style_sample}\n\n"
            f"BOOK SKELETON SUMMARY FOR THIS CHAPTER:\n{state.chapters[chap_num-1].summary if len(state.chapters) >= chap_num else 'N/A'}\n\n"
            f"CONTEXT (Previous Chapters):\n{context_truncated}\n\n"
            f"TASK: Generate the detailed outline for Chapter {chap_num}.\n"
            "\n\n### MANDATORY JSON STRUCTURE REQUIRED\n"
            "Respond ONLY with valid JSON inside a code block. Do not include any text before or after the JSON block.\n"
            "```json\n"
            "{\n"
            "  \"title\": \"Chapter Title\",\n"
            "  \"pov\": \"POV Character\",\n"
            "  \"tense\": \"Past or Present\",\n"
            "  \"plot_thread_a\": \"Sequence/Primary Plot\",\n"
            "  \"plot_thread_b\": \"Subplot/Setup\",\n"
            "  \"key_revelation\": \"The big twist or discovery\",\n"
            "  \"scene_notes\": \"Detailed beat-by-beat notes\"\n"
            "}"
        )

        response = self.client.prompt(system_prompt, user_content)
        result = self._clean_json(response)
        
        # Calculate tokens
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        
        if isinstance(result, dict):
            result["_tokens"] = total_tokens
            
        return result

    def run_skeleton_planner_turn(self, state: ProjectState, count: int, critique: Optional[str] = None, previous_draft: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a skeleton planner turn to generate or refine the project-wide outline (Phase 2).

        Args:
            state (ProjectState): The project state.
            count (int): Total chapters to plan.
            critique (Optional[str]): Feedback from 02b_skeleton_critic.
            previous_draft (Optional[str]): The draft before refinement.

        Returns:
            Dict[str, Any]: The structured skeleton as JSON.
        """
        system_prompt = (
            "You are '02a_skeleton_plotter', an expert story architect. Your task is to design the high-level skeleton "
            f"of a {count}-chapter book. You MUST respond in valid JSON format only. "
            "Do NOT include conversational preamble, explanations, or any text outside the JSON block."
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
            user_content += "### CRITIQUE FROM 02b_skeleton_critic\n"
            user_content += f"{critique}\n\n"
            user_content += "**TASK:** Refine the skeleton above by addressing ALL points in the critique. Ensure story consistency is maintained.\n"
        else:
            user_content += f"**TASK:** Generate a fresh {count}-chapter skeleton. Each chapter MUST have a title and a SINGLE PARAGRAPH of high-level description.\n"

        user_content += (
            "\n### REQUIRED JSON FORMAT\n"
            "Return ONLY a valid JSON object inside a Markdown code block. Do not include any conversational preamble.\n"
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
        result = self._clean_json(response)
        
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        if isinstance(result, dict):
            result["_tokens"] = total_tokens
            
        return result



    def run_skeleton_formatter_turn(self, raw_outline: str, target_count: int) -> Dict[str, Any]:
        """
        Convert creative prose narrative into a strict JSON chapter structure (Phase 2).

        Args:
            raw_outline (str): The prose outline to format.
            target_count (int): The number of chapters to extract.

        Returns:
            Dict[str, Any]: A structured JSON list of chapters with token counts.
        """
        system_prompt = (
            "You are '02c_skeleton_formatter', a data extraction specialist. Your task is to take a creative book "
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
        result = self._clean_json(response)
        
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        if isinstance(result, dict):
            result["_tokens"] = total_tokens
            
        return result

    def run_skeleton_critic_turn(self, state: ProjectState, content: str, is_final: bool = False) -> str:
        """
        Evaluate the project skeleton for structural integrity and pacing (Phase 2).

        Args:
            state (ProjectState): The current project state.
            content (str): The skeleton content (prose or JSON) to review.
            is_final (bool): Whether this is the final assessment of the formatted JSON.

        Returns:
            str: The critic's text feedback and recommendations.
        """
        role_desc = "literature expert and antagonistic critic" if not is_final else "literature expert providing final QA on the structured skeleton"
        system_prompt = f"You are '02b_skeleton_critic', a {role_desc}. Evaluate the book skeleton for pacing, twists, and structural integrity."
        
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

    def run_architect_impact_analysis_turn(self, state: ProjectState, changed_index: int, new_content: str) -> str:
        """
        Identify potential ripple effects and contradictions caused by a chapter change (Phase 3).

        Args:
            state (ProjectState): The project state.
            changed_index (int): Index of the changed chapter in the chapter list.
            new_content (str): The updated summary/beats for the chapter.

        Returns:
            str: Analysis of ripple effects and suggestions for other chapters.
        """
        system_prompt = (
            "You are '03b_architect_critic' performing an Impact Analysis. When a chapter changes, you must identify "
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

    def run_narrative_engine_turn(self, state: ProjectState, chap_num: int, context_memos: List[str], previous_bridge: str, critique: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a narrative engine turn to generate full chapter prose (Phase 4).

        Args:
            state (ProjectState): The current project state.
            chap_num (int): Target chapter number.
            context_memos (List[str]): Continuity memos from previous chapters.
            previous_bridge (str): The last 1,000 words of the previous chapter.
            critique (Optional[str]): Feedback from 04b_narrative_critic for refinement.

        Returns:
            Dict[str, Any]: A dictionary containing the generated 'prose' and token counts.
        """
        system_prompt = (
            "You are '04a_narrative_engine', a world-class novelist. Your task is to write high-quality, immersive "
            "prose based on the provided chapter map. Focus on sensory details, authentic dialogue, and pacing. "
            "You MUST maintain strict continuity with previous chapters."
        )

        # Context construction
        memo_text = "\n".join([f"- {m}" for m in context_memos]) if context_memos else "No previous chapter memos."
        
        user_content = (
            f"### PROJECT SPECS\nTitle: {state.plot.book_title}\nGenre: {state.plot.genre}\n"
            f"Style: {state.style.tone}, {state.style.voice}\n"
            f"Vocabulary: {state.style.vocabulary}\n"
            f"Global Tense: {state.style.tense}\n\n"
            f"### STYLE EXAMPLES\n{state.style.example_paragraphs[:1000]}\n\n"
            f"### CONTINUITY MEMOS (Previous Events)\n{memo_text}\n\n"
            f"### PROSE BRIDGE (End of Previous Chapter)\n...{previous_bridge[-1000:] if previous_bridge else 'First Chapter'}\n\n"
            f"### CHAPTER MAP: CHAPTER {chap_num}\n"
            f"POV: {state.chapters[chap_num-1].pov}\n"
            f"Revelation: {state.chapters[chap_num-1].key_revelation}\n"
            f"Beats: {state.chapters[chap_num-1].scene_notes}\n\n"
        )

        if critique:
            user_content += f"### CRITIQUE FROM 04b_narrative_critic\n{critique}\n\n**TASK:** Rewrite/Refine the chapter following these guidelines."
        else:
            user_content += f"**TASK:** Write a full, immersive draft for Chapter {chap_num}."

        response = self.client.prompt(system_prompt, user_content)
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        return {"prose": response, "_tokens": total_tokens}

    def run_narrative_critic_turn(self, state: ProjectState, chap_num: int, prose: str) -> Dict[str, Any]:
        """
        Evaluate chapter prose for pacing, word count, and continuity (Phase 4).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Chapter number being reviewed.
            prose (str): The generated prose to audit.

        Returns:
            Dict[str, Any]: A structured JSON critique including word counts and suggestions.
        """
        system_prompt = (
            "You are '04b_narrative_critic', a sharp-eyed editor. Your task is to review chapter prose for word count, "
            "pacing, and continuity. You MUST respond in valid JSON format only."
        )

        user_content = (
            f"### CHAPTER {chap_num} PROSE\n{prose}\n\n"
            "### TASK\nEvaluate this chapter. Identify where the pacing slows down too much or where details contradict "
            "the project goals. Provide specific advice for 04a to improve the draft.\n\n"
            "### MANDATORY JSON FORMAT\n"
            "{\n"
            "  \"word_count\": 1200,\n"
            "  \"pacing_score\": 7,\n"
            "  \"suggestions\": [\"scene 2 is too fast\", \"...\"],\n"
            "  \"continuity_warnings\": [\"Character X mentioned a sword they lost earlier\", \"...\"],\n"
            "  \"editorial_notes\": \"Overall thoughts...\"\n"
            "}"
        )

        response = self.client.prompt(system_prompt, user_content)
        result = self._clean_json(response)
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        if isinstance(result, dict):
            result["_tokens"] = total_tokens
        return result

    def run_context_manager_turn(self, state: ProjectState, chap_num: int, prose: str) -> Dict[str, Any]:
        """
        Summarize a chapter into a 3-sentence continuity memo (Phase 4).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Chapter number.
            prose (str): The full prose of the chapter.

        Returns:
            Dict[str, Any]: A dictionary containing the 'memo' and token usage.
        """
        system_prompt = (
            "You are '04c_context_manager', a continuity specialist. Your task is to summarize the core events "
            "of a chapter into EXACTLY 3 sentences that will be used keep the AI coherent in future chapters."
        )

        user_content = (
            f"### CHAPTER {chap_num} PROSE\n{prose[:4000]}...\n\n"
            "### TASK\nSummarize the key plot changes, character state shifts (injuries, items gained/lost), and revelations "
            "from this chapter into exactly 3 clear bullets or sentences."
        )

        response = self.client.prompt(system_prompt, user_content)
        total_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_content)
        return {"memo": response, "_tokens": total_tokens}

    def run_architect_critic_turn(self, state: ProjectState, chap_num: int, context_summary: str, draft: str, is_final: bool = False) -> str:
        """
        Execute a critic turn to evaluate a detailed chapter draft (Phase 3).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Target chapter number.
            context_summary (str): Summary of previous chapters.
            draft (str): The detailed map draft to review.
            is_final (bool): Whether this is the final assessment pass.

        Returns:
            str: The critic's feedback text.
        """
        role_desc = "literature expert and antagonistic critic" if not is_final else "literature expert providing final thoughts for the user"
        system_prompt = (
            f"You are '03b_architect_critic', a {role_desc}. Your goal is to evaluate the plotter's draft for Chapter {chap_num} "
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
        if not text:
            return {"error": "Empty response from LLM"}

        # 0. Check for low-level connection errors signaled by the client
        if text == "SIGNAL_OFFLINE_OLLAMA":
            return {"error": "OLLAMA_OFFLINE: Could not connect to Ollama. Please ensure the server is running on localhost:11434."}
        if text.startswith("SIGNAL_ERROR_LLM:"):
            return {"error": f"LLM_CLIENT_ERROR: {text.split(':', 1)[1].strip()}"}

        # 1. Aggressive Noise Removal (Strip Thinking Blocks)
        # Remove balanced tags
        text = re.sub(r'<(think|thought|reasoning|thinking)>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Handle unpaired tags (common prefix/suffix thinking)
        if "</think>" in text: text = text.split("</think>", 1)[1]
        if "</thought>" in text: text = text.split("</thought>", 1)[1]
        if "</reasoning>" in text: text = text.split("</reasoning>", 1)[1]
        
        # 2. Try to find JSON in Markdown blocks first (most reliable)
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            candidate = match.group(1)
            parsed = self._try_parse(candidate)
            if parsed: return parsed

        # 3. Smart Search for JSON-like structures (Reverse order to find final payload)
        potential_starts = [m.start() for m in re.finditer(r'\{', text)]
        for start in reversed(potential_starts):
            # Check if this brace is likely the start of a property or empty object
            if re.match(r'\{\s*(?:"|\})', text[start:]):
                end = text.rfind('}')
                if end > start:
                    candidate = text[start:end+1]
                    parsed = self._try_parse(candidate)
                    if parsed: return parsed

        # 4. Final Hail Mary: Literal Brace Extraction (Old Method)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end > start:
            candidate = text[start:end+1]
            parsed = self._try_parse(candidate)
            if parsed: return parsed

        self._log_debug_output(text, "No valid JSON structure found.")
        return {"error": "JSON Parse Error: No valid JSON block found in response.", "raw": text}

    def _try_parse(self, json_str: str):
        """Helper to try parsing and repairing a candidate JSON string."""
        try:
            # Stage 1: Normalize smart quotes
            json_str = json_str.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
            
            # Stage 2: Fix trailing commas in objects and arrays
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            
            # Stage 3: Initial Parse
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Stage 4: Targeted Repair (Single to Double Quotes for Keys)
                repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', json_str)
                # Simple boolean/null repairs
                repaired = repaired.replace('True', 'true').replace('False', 'false').replace('None', 'null')
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    return None
        except Exception:
            return None

    def _log_debug_output(self, text: str, error_msg: str):
        """Log suspicious AI output to a debug file for investigation."""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "debug_llm_output.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- DEBUG LOG: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f.write(f"ERROR: {error_msg}\n")
                f.write("RAW TEXT:\n")
                f.write(text)
                f.write("\n" + "="*40 + "\n")
        except Exception as e:
            print(f"Failed to write debug log: {e}")
