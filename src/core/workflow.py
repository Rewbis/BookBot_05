import json
from datetime import datetime
from typing import Callable, Optional

class NarrativeWorkflow:
    """Orchestrate multi-agent workflows for book planning."""

    def __init__(self, agents, exporter):
        """Initialize the workflow with required agents and exporter."""
        self.agents = agents
        self.exporter = exporter

    def run_skeleton_generation(self, state, target_count: int, status_callback: Callable[[str], None]):
        """Execute the automated skeleton generation workflow."""
        # Step 1: Initial Plot
        status_callback("🤖 **01a_skeleton_plotter** drafting skeleton...")
        skel_json = self.agents.run_skeleton_plotter_turn(state, target_count)
        if "error" in skel_json:
            return {"error": skel_json["error"], "raw": skel_json.get("raw", "")}
        
        skel_text = json.dumps(skel_json, indent=2)

        # Step 2: Critique
        status_callback("🧐 **01b_skeleton_critic** reviewing structure...")
        critique = self.agents.run_skeleton_critic_turn(state, skel_text)

        # Step 3: Refine
        status_callback("🛠️ **01a_skeleton_plotter** refining skeleton...")
        refined_json = self.agents.run_skeleton_plotter_turn(state, target_count, critique, skel_text)
        if "error" in refined_json:
            return {"error": refined_json["error"], "raw": refined_json.get("raw", "")}
        
        raw_refined = refined_json.get("raw", json.dumps(refined_json))

        # Step 4: Extract/Format
        status_callback("🔄 **01c_skeleton_formatter** extracting structured JSON...")
        formatted_json = self.agents.run_skeleton_formatter_turn(raw_refined, target_count)
        if "error" in formatted_json:
            return {"error": formatted_json["error"], "raw": raw_refined}
        
        formatted_text = json.dumps(formatted_json, indent=2)

        # Step 5: Final QA
        status_callback("⚖️ **01b_skeleton_critic** final JSON assessment...")
        final_qa = self.agents.run_skeleton_critic_turn(state, formatted_text, is_final=True)

        # Persistence
        j_path, _ = self.exporter.save_skeleton_draft(
            formatted_json.get("chapters", []),
            f"FINAL JSON:\n{formatted_text}\n\nFINAL QA:\n{final_qa}\n\nREFINED PROSE:\n{raw_refined}\n\nINITIAL CRITIQUE:\n{critique}"
        )

        return {
            "chapters": formatted_json.get("chapters", []),
            "final_qa": final_qa,
            "initial_critique": critique,
            "refined_prose": raw_refined,
            "save_path": j_path
        }

    def run_skeleton_refinement(self, state, target_count: int, combined_critique: str, current_prose: str, status_callback: Callable[[str], None]):
        """Execute a targeted refinement turn for an existing skeleton."""
        # 1. Refine
        status_callback("🛠️ **01a_skeleton_plotter** applying adjustments...")
        new_refined_json = self.agents.run_skeleton_plotter_turn(state, target_count, combined_critique, current_prose)
        if "error" in new_refined_json:
            return {"error": new_refined_json["error"], "raw": new_refined_json.get("raw", "")}
        
        new_raw_refined = new_refined_json.get("raw", json.dumps(new_refined_json))

        # 2. Format
        status_callback("🔄 **01c_skeleton_formatter** re-extracting JSON...")
        new_formatted_json = self.agents.run_skeleton_formatter_turn(new_raw_refined, target_count)
        if "error" in new_formatted_json:
            return {"error": new_formatted_json["error"], "raw": new_raw_refined}
        
        new_formatted_text = json.dumps(new_formatted_json, indent=2)

        # 3. Final QA
        status_callback("⚖️ **01b_skeleton_critic** final assessment of new draft...")
        new_final_qa = self.agents.run_skeleton_critic_turn(state, new_formatted_text, is_final=True)

        # Persistence
        j_path, _ = self.exporter.save_skeleton_draft(
            new_formatted_json.get("chapters", []),
            f"MANUAL REFINEMENT JSON:\n{new_formatted_text}\n\nFINAL QA:\n{new_final_qa}\n\nSELECTED CRITIQUE:\n{combined_critique}\n\nBASE PROSE:\n{current_prose}"
        )

        return {
            "chapters": new_formatted_json.get("chapters", []),
            "final_qa": new_final_qa,
            "refined_prose": new_raw_refined,
            "save_path": j_path
        }

    def run_chapter_detailing(self, state, chap_num: int, context_summary: str, status_callback: Callable[[str], None]):
        """Execute the Chapter Detail Architect workflow."""
        # 1. Initial Draft
        status_callback("🤖 **02a_plotter** drafting detailed outline...")
        draft_json = self.agents.run_plotter_turn(state, chap_num, context_summary)
        if "error" in draft_json:
            return {"error": draft_json["error"]}
        
        draft_text = json.dumps(draft_json, indent=2)

        # 2. Critique
        status_callback("🧐 **02b_critic** evaluating draft...")
        critique = self.agents.run_critic_turn(state, chap_num, context_summary, draft_text)

        # 3. Refine
        status_callback("🛠️ **02a_plotter** self-correcting based on feedback...")
        refined_json = self.agents.run_plotter_turn(state, chap_num, context_summary, critique, draft_text)
        if "error" in refined_json:
            return {"error": refined_json["error"]}
        
        refined_text = json.dumps(refined_json, indent=2)

        # 4. Final Assessment
        status_callback("⚖️ **02b_critic** providing final QA...")
        final_qa = self.agents.run_critic_turn(state, chap_num, context_summary, refined_text, is_final=True)

        return {
            "draft_json": refined_json,
            "final_qa": final_qa
        }
