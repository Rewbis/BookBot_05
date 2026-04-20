import json
from datetime import datetime
from typing import Callable, Optional, Dict, Any

class NarrativeWorkflow:
    """Orchestrate multi-agent workflows for book planning."""

    def __init__(self, agents: Any, exporter: Any):
        """
        Initialize the workflow with required agents and exporter.

        Args:
            agents (BookBotAgents): The suite of available agents.
            exporter (Exporter): The data exporter for persistence.
        """
        self.agents = agents
        self.exporter = exporter

    def run_skeleton_generation(self, state: Any, target_count: int, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Execute the automated skeleton generation workflow (Phase 2).
        Orchestrates 02a (Plotter) -> 02b (Critic) -> 02a (Refiner) -> 02c (Formatter) -> 02b (QA).

        Args:
            state (ProjectState): The project state.
            target_count (int): Number of chapters to generate.
            status_callback (Callable): Callback for UI status updates.

        Returns:
            Dict[str, Any]: Resulting chapters and orchestration metadata.
        """
        total_tokens = 0
        
        # Step 1: Initial Plot
        status_callback("🤖 **02a_skeleton_plotter** drafting skeleton...")
        skel_result = self.agents.run_skeleton_planner_turn(state, target_count)
        if "error" in skel_result:
            return {"error": skel_result["error"], "raw": skel_result.get("raw", "")}
        
        total_tokens += skel_result.get("_tokens", 0)
        skel_text = json.dumps(skel_result, indent=2)

        # Step 2: Critique
        status_callback("🧐 **02b_skeleton_critic** reviewing structure...")
        critique = self.agents.run_skeleton_critic_turn(state, skel_text)

        # Step 3: Refine
        status_callback("🛠️ **02a_skeleton_plotter** refining skeleton...")
        refined_result = self.agents.run_skeleton_planner_turn(state, target_count, critique, skel_text)
        if "error" in refined_result:
            return {"error": refined_result["error"], "raw": refined_result.get("raw", "")}
        
        total_tokens += refined_result.get("_tokens", 0)
        raw_refined = refined_result.get("raw", json.dumps(refined_result))

        # Step 4: Extract/Format
        status_callback("🔄 **02c_skeleton_formatter** extracting structured JSON...")
        formatted_result = self.agents.run_skeleton_formatter_turn(raw_refined, target_count)
        if "error" in formatted_result:
            return {"error": formatted_result["error"], "raw": raw_refined}
        
        total_tokens += formatted_result.get("_tokens", 0)
        formatted_text = json.dumps(formatted_result, indent=2)

        # Step 5: Final QA
        status_callback("⚖️ **02b_skeleton_critic** final JSON assessment...")
        final_qa = self.agents.run_skeleton_critic_turn(state, formatted_text, is_final=True)

        # Persistence
        j_path, _ = self.exporter.save_skeleton_draft(
            formatted_result.get("chapters", []),
            f"FINAL JSON:\n{formatted_text}\n\nFINAL QA:\n{final_qa}\n\nREFINED PROSE:\n{raw_refined}\n\nINITIAL CRITIQUE:\n{critique}"
        )

        return {
            "chapters": formatted_result.get("chapters", []),
            "final_qa": final_qa,
            "initial_critique": critique,
            "refined_prose": raw_refined,
            "save_path": j_path,
            "total_tokens": total_tokens
        }

    def run_skeleton_refinement(self, state: Any, target_count: int, combined_critique: str, current_prose: str, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Execute a targeted refinement turn for an existing skeleton (Phase 2).
        Allows for manual intervention and specific adjustments.

        Args:
            state (ProjectState): The project state.
            target_count (int): Number of chapters.
            combined_critique (str): Merged feedback for refinement.
            current_prose (str): The existing prose draft to refine.
            status_callback (Callable): Status update callback.

        Returns:
            Dict[str, Any]: Updated chapters and metadata.
        """
        total_tokens = 0
        
        # 1. Refine
        status_callback("🛠️ **02a_skeleton_plotter** applying adjustments...")
        new_refined_result = self.agents.run_skeleton_planner_turn(state, target_count, combined_critique, current_prose)
        if "error" in new_refined_result:
            return {"error": new_refined_result["error"], "raw": new_refined_result.get("raw", "")}
        
        total_tokens += new_refined_result.get("_tokens", 0)
        new_raw_refined = new_refined_result.get("raw", json.dumps(new_refined_result))

        # 2. Format
        status_callback("🔄 **01c_skeleton_formatter** re-extracting JSON...")
        new_formatted_result = self.agents.run_skeleton_formatter_turn(new_raw_refined, target_count)
        if "error" in new_formatted_result:
            return {"error": new_formatted_result["error"], "raw": new_raw_refined}
        
        total_tokens += new_formatted_result.get("_tokens", 0)
        new_formatted_text = json.dumps(new_formatted_result, indent=2)

        # 3. Final QA
        status_callback("⚖️ **02b_skeleton_critic** final assessment of new draft...")
        new_final_qa = self.agents.run_skeleton_critic_turn(state, new_formatted_text, is_final=True)

        # Persistence
        j_path, _ = self.exporter.save_skeleton_draft(
            new_formatted_result.get("chapters", []),
            f"MANUAL REFINEMENT JSON:\n{new_formatted_text}\n\nFINAL QA:\n{new_final_qa}\n\nSELECTED CRITIQUE:\n{combined_critique}\n\nBASE PROSE:\n{current_prose}"
        )

        return {
            "chapters": new_formatted_result.get("chapters", []),
            "final_qa": new_final_qa,
            "refined_prose": new_raw_refined,
            "save_path": j_path,
            "total_tokens": total_tokens
        }

    def run_chapter_detailing(self, state: Any, chap_num: int, context_summary: str, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Execute the Chapter Detail Architect workflow (Phase 3).
        Orchestrates 03a (Architect) -> 03b (Critic) -> 03a (Refiner) -> 03b (QA).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Target chapter number.
            context_summary (str): Context from previous chapters.
            status_callback (Callable): Status update callback.

        Returns:
            Dict[str, Any]: Detailed chapter map and quality assessment.
        """
        total_tokens = 0
        
        # 1. Initial Draft
        status_callback("🤖 **03a_architect** drafting detailed outline...")
        draft_result = self.agents.run_architect_turn(state, chap_num, context_summary)
        if "error" in draft_result:
            return {"error": draft_result["error"]}
        
        total_tokens += draft_result.get("_tokens", 0)
        draft_text = json.dumps(draft_result, indent=2)

        # 2. Critique
        status_callback("🧐 **03b_architect_critic** evaluating draft...")
        critique = self.agents.run_architect_critic_turn(state, chap_num, context_summary, draft_text)

        # 3. Refine
        status_callback("🛠️ **03a_architect** self-correcting based on feedback...")
        refined_result = self.agents.run_architect_turn(state, chap_num, context_summary, critique, draft_text)
        if "error" in refined_result:
            return {"error": refined_result["error"]}
        
        total_tokens += refined_result.get("_tokens", 0)
        refined_text = json.dumps(refined_result, indent=2)

        # 4. Final Assessment
        status_callback("⚖️ **03b_architect_critic** providing final QA...")
        final_qa = self.agents.run_architect_critic_turn(state, chap_num, context_summary, refined_text, is_final=True)

        return {
            "draft_json": refined_result,
            "final_qa": final_qa,
            "total_tokens": total_tokens
        }

    def run_bulk_detailing(self, state: Any, start_ch: int, end_ch: int, status_callback: Callable[[str], None], 
                           progress_callback: Optional[Callable[[float, str], None]] = None,
                           stop_check: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """
        Run the detailing workflow for a range of chapters sequentially (Phase 3 Bulk).

        Args:
            state (ProjectState): The project state.
            start_ch (int): Start chapter index.
            end_ch (int): End chapter index.
            status_callback (Callable): UI status callback.
            progress_callback (Optional[Callable]): UI progress bar callback.
            stop_check (Optional[Callable]): Callback to check for user interruption.

        Returns:
            Dict[str, Any]: Success status and telemetry.
        """
        from src.ui.planning_view import clean_narrative_text
        
        total_tokens = 0
        success_count = 0
        
        total_range = (end_ch - start_ch) + 1
        
        for i, ch_num in enumerate(range(start_ch, end_ch + 1)):
            if ch_num > len(state.chapters):
                break
                
            progress_msg = f"Architecting Ch {ch_num} ({i+1}/{total_range})"
            status_callback(f"🌊 **Bulk Mode**: {progress_msg}...")
            if progress_callback:
                progress_callback((i) / total_range, progress_msg)
            
            # Use most recent chapters for context
            context = self.agents.get_context_summary(state.chapters[:ch_num-1], count=5)
            
            result = self.run_chapter_detailing(state, ch_num, context, status_callback)
            
            if "error" in result:
                if progress_callback:
                    progress_callback(1.0, f"Error at Ch {ch_num}")
                return {"error": f"Failed at Ch {ch_num}: {result['error']}", "success_count": success_count}
            
            total_tokens += result.get("total_tokens", 0)
            
            # Apply to registry immediately
            chap = state.chapters[ch_num-1]
            d = result["draft_json"]
            
            # Clean and map
            chap.title = clean_narrative_text(d.get("title", chap.title))
            chap.pov = clean_narrative_text(d.get("pov", ""))
            chap.tense = clean_narrative_text(d.get("tense", "Past"))
            chap.key_revelation = clean_narrative_text(d.get("key_revelation", ""))
            chap.plot_thread_a = clean_narrative_text(d.get("plot_thread_a", ""))
            chap.plot_thread_b = clean_narrative_text(d.get("plot_thread_b", ""))
            chap.scene_notes = clean_narrative_text(d.get("scene_notes", ""))
            
            success_count += 1

            if progress_callback:
                progress_callback((i + 1) / total_range, f"Completed Ch {ch_num}")
            
            # Checkpoint save every 3 chapters
            if success_count % 3 == 0:
                self.exporter.save_log(state, checkpoint_name=f"bulk_ch{ch_num}")

            # Check for user cancellation
            if stop_check and stop_check():
                status_callback("🛑 **Bulk Mode**: Generation interrupted by user.")
                return {"success": True, "interrupted": True, "success_count": success_count, "total_tokens": total_tokens}
                
        return {"success": True, "interrupted": False, "success_count": success_count, "total_tokens": total_tokens}

    def run_prose_drafting(self, state: Any, chap_num: int, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Execute the Phase 4 Narrative Engine drafting/refinement workflow.
        Orchestrates 04a (Engine) -> 04b (Critic) -> 04a (Refiner).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Target chapter number.
            status_callback (Callable): Status update callback.

        Returns:
            Dict[str, Any]: Generated prose versions (v1, v2) and telemetry.
        """
        total_tokens = 0
        
        # 1. Gather Context
        status_callback("📚 Gathering continuity context...")
        memos = [c.draft.continuity_memo for c in state.chapters[:chap_num-1] if c.draft.continuity_memo]
        
        bridge = ""
        if chap_num > 1:
            prev_chap = state.chapters[chap_num-2]
            bridge = prev_chap.draft.final_prose if prev_chap.draft.final_prose else prev_chap.draft.v2_refined
        
        # 2. First Draft (04a)
        status_callback("✍️ **04a_narrative_engine** drafting full chapter prose...")
        v1_result = self.agents.run_narrative_engine_turn(state, chap_num, memos, bridge)
        v1_prose = v1_result.get("prose", "")
        total_tokens += v1_result.get("_tokens", 0)

        # 3. Editorial Review (04b)
        status_callback("🧐 **04b_narrative_critic** auditing prose and pacing...")
        critique_result = self.agents.run_narrative_critic_turn(state, chap_num, v1_prose)
        total_tokens += critique_result.get("_tokens", 0)
        
        # Format critique sections for 04a
        critique_text = f"Word Count: {critique_result.get('word_count')}\n"
        critique_text += f"Suggestions: {', '.join(critique_result.get('suggestions', []))}\n"
        critique_text += f"Continuity Warnings: {', '.join(critique_result.get('continuity_warnings', []))}"

        # 4. Refinement (04a)
        status_callback("🛠️ **04a_narrative_engine** self-correcting and polishing...")
        v2_result = self.agents.run_narrative_engine_turn(state, chap_num, memos, bridge, critique=critique_text)
        v2_prose = v2_result.get("prose", "")
        total_tokens += v2_result.get("_tokens", 0)

        return {
            "v1_raw": v1_prose,
            "critic_notes": critique_text,
            "v2_refined": v2_prose,
            "total_tokens": total_tokens
        }

    def run_prose_cleanup(self, state: Any, chap_num: int, final_prose: str, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Generate a 3-sentence continuity memo for an approved chapter (Phase 4 Cleanup).

        Args:
            state (ProjectState): The project state.
            chap_num (int): Chapter index.
            final_prose (str): The approved final prose for the chapter.
            status_callback (Callable): Status update callback.

        Returns:
            Dict[str, Any]: The continuity memo and token usage.
        """
        status_callback("📒 **04c_context_manager** archiving continuity memo...")
        result = self.agents.run_context_manager_turn(state, chap_num, final_prose)
        return {
            "memo": result.get("memo", ""),
            "total_tokens": result.get("_tokens", 0)
        }

    def run_brainstorm_ideation(self, state: Any, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Run the 01a_brainstormer agent to expand project specs (Phase 1).

        Args:
            state (ProjectState): The current project setup.
            status_callback (Callable): Status update callback.

        Returns:
            Dict[str, Any]: Brainstormed suggestions.
        """
        status_callback("🧠 **01a_brainstormer** exploring new ideas...")
        result = self.agents.run_brainstormer_turn(state)
        return result

    def run_continuity_audit(self, state: Any, status_callback: Callable[[str], None]) -> Dict[str, Any]:
        """
        Run the 01b_continuity_expert agent to audit project logic (Phase 1).

        Args:
            state (ProjectState): The current project setup.
            status_callback (Callable): Status update callback.

        Returns:
            Dict[str, Any]: Audit findings and contradiction reports.
        """
        status_callback("⚖️ **01b_continuity_expert** auditing for contradictions...")
        result = self.agents.run_continuity_expert_turn(state)
        return result
    def run_bulk_prose_generation(self, state: Any, start_ch: int, end_ch: int, status_callback: Callable[[str], None],
                                 progress_callback: Optional[Callable[[float, str], None]] = None,
                                 stop_check: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """
        Run the prose drafting workflow for a range of chapters sequentially (Phase 4 Bulk).
        
        Args:
            state (ProjectState): The project state.
            start_ch (int): Start chapter index.
            end_ch (int): End chapter index.
            status_callback (Callable): UI status callback.
            progress_callback (Optional[Callable]): UI progress bar callback.
            stop_check (Optional[Callable]): Callback to check for user interruption.

        Returns:
            Dict[str, Any]: Success status and telemetry.
        """
        total_tokens = 0
        success_count = 0
        total_range = (end_ch - start_ch) + 1
        
        for i, ch_num in enumerate(range(start_ch, end_ch + 1)):
            if ch_num > len(state.chapters):
                break
                
            progress_msg = f"Drafting Ch {ch_num} ({i+1}/{total_range})"
            status_callback(f"✍️ **Bulk Mode**: {progress_msg}...")
            if progress_callback:
                progress_callback((i) / total_range, progress_msg)
            
            # Step 1: Draft
            result = self.run_prose_drafting(state, ch_num, status_callback)
            if "error" in result:
                if progress_callback:
                    progress_callback(1.0, f"Error at Ch {ch_num}")
                return {"error": f"Failed at Ch {ch_num}: {result['error']}", "success_count": success_count}
            
            total_tokens += result.get("total_tokens", 0)
            
            # Step 2: Apply to registry
            chap = state.chapters[ch_num-1]
            chap.draft.v1_raw = result["v1_raw"]
            chap.draft.critic_notes = result["critic_notes"]
            chap.draft.v2_refined = result["v2_refined"]
            chap.draft.final_prose = result["v2_refined"]
            
            # Step 3: Cleanup (Memo)
            cleanup_result = self.run_prose_cleanup(state, ch_num, chap.draft.final_prose, status_callback)
            chap.draft.continuity_memo = cleanup_result["memo"]
            total_tokens += cleanup_result.get("total_tokens", 0)
            
            # Step 4: Auto-Approve for continuity chain
            chap.draft.user_approved = True
            
            success_count += 1
            if progress_callback:
                progress_callback((i + 1) / total_range, f"Completed Ch {ch_num}")
            
            # Checkpoint save after EVERY chapter in Phase 4 (Long turns)
            self.exporter.save_log(state, checkpoint_name=f"bulk_prose_ch{ch_num}")

            # Check for user cancellation
            if stop_check and stop_check():
                status_callback("🛑 **Bulk Mode**: Drafting interrupted by user.")
                return {"success": True, "interrupted": True, "success_count": success_count, "total_tokens": total_tokens}
                
        return {"success": True, "interrupted": False, "success_count": success_count, "total_tokens": total_tokens}
