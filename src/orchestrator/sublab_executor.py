"""SubLab Executor — runs dynamically composed agent teams.

Creates agents from a :class:`SubLabPlan`, executes them in the
specified group order (parallel within groups, sequential across groups),
and wraps results in :class:`DivisionReport` objects so the downstream
pipeline (review, synthesis) works unchanged.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from src.agents.base_agent import BaseAgent
from src.agents.dynamic_factory import create_dynamic_agent
from src.orchestrator.stream_events import PipelineEventEmitter
from src.utils.types import (
    AgentResult,
    ConfidenceAssessment,
    ConfidenceLevel,
    DivisionReport,
    SubLabPlan,
    Task,
)

logger = logging.getLogger("lumi.orchestrator.sublab_executor")


class SubLabExecutor:
    """Executes a dynamic SubLab plan."""

    async def execute(
        self,
        sublab_plan: SubLabPlan,
        task_description: str,
        emitter: PipelineEventEmitter | None = None,
    ) -> list[DivisionReport]:
        """Create dynamic agents and execute the SubLab plan."""
        emitter = emitter or PipelineEventEmitter()

        # 1. Create all agents
        agents: dict[str, BaseAgent] = {}
        for spec in sublab_plan.agents:
            agent = create_dynamic_agent(
                name=spec.name,
                role_description=spec.role,
                tool_names=spec.tools,
                domains=spec.domains,
                model=spec.model_tier,
            )
            agents[spec.name] = agent

        logger.info("[SubLabExecutor] Created %d dynamic agents", len(agents))
        for name, agent in agents.items():
            tool_count = len([t for t in agent.tools if t.get("name") != "execute_code"])
            logger.info("[SubLabExecutor]   '%s': %d tools, model=%s", name, tool_count, agent.model.value)

        # 2. Execute groups sequentially; agents within a group in parallel
        all_results: dict[str, AgentResult] = {}
        prior_context = ""

        for group_idx, group in enumerate(sublab_plan.execution_groups):
            group_label = f"Dynamic SubLab · Group {group_idx + 1}"
            logger.info("[SubLabExecutor] Executing group %d/%d: %s", group_idx + 1, len(sublab_plan.execution_groups), group)

            async def _run_agent(agent_name: str, agent: BaseAgent, task: Task, division: str) -> AgentResult:
                """Run a single agent with streaming events."""
                start = time.time()
                await emitter.trace_start(agent_name, division, f"Executing {agent_name}...")

                async def on_tool(tool_name, tool_input, result_str, dur_ms):
                    await emitter.tool_call(agent_name, tool_name, tool_input, result_str, dur_ms)

                try:
                    result = await agent.execute(task, on_tool_call=on_tool)
                    duration_ms = int((time.time() - start) * 1000)

                    # Compute confidence
                    conf_score = None
                    conf_level = None
                    if result.findings:
                        conf_score = sum(c.confidence.score for c in result.findings) / len(result.findings)
                        conf_level = "HIGH" if conf_score >= 0.7 else "MEDIUM" if conf_score >= 0.4 else "LOW"

                    summary = result.raw_data.get("final_response", "")[:300]
                    tools_list = [
                        {"tool_name": t, "tool_input": {}, "result": None, "duration_ms": None}
                        for t in result.tools_used
                    ]

                    await emitter.trace_complete(
                        agent_name, division, summary,
                        tools_called=tools_list,
                        confidence_score=conf_score,
                        confidence_level=conf_level,
                        duration_ms=duration_ms,
                    )
                    return result

                except Exception as exc:
                    duration_ms = int((time.time() - start) * 1000)
                    await emitter.trace_error(agent_name, division, str(exc), duration_ms)
                    raise

            coros = []
            group_agent_names = []
            for agent_name in group:
                agent = agents.get(agent_name)
                if agent is None:
                    logger.warning("[SubLabExecutor] Agent '%s' not found — skipping", agent_name)
                    continue

                task_text = task_description
                if prior_context:
                    task_text += f"\n\n--- Prior findings from earlier agents ---\n{prior_context}"

                task = Task(
                    task_id=f"sublab_{uuid.uuid4().hex[:8]}",
                    description=task_text,
                    agent=agent_name,
                )

                coros.append(_run_agent(agent_name, agent, task, group_label))
                group_agent_names.append(agent_name)

            # Run group in parallel
            batch = await asyncio.gather(*coros, return_exceptions=True)

            for agent_name, result in zip(group_agent_names, batch):
                if isinstance(result, Exception):
                    logger.error("[SubLabExecutor] Agent '%s' failed: %s", agent_name, result)
                    all_results[agent_name] = AgentResult(
                        agent_id=agent_name,
                        task_id="failed",
                        raw_data={"error": str(result)},
                    )
                else:
                    all_results[agent_name] = result

            # Build context from this group's results for the next group
            context_parts: list[str] = []
            for agent_name in group_agent_names:
                r = all_results.get(agent_name)
                if r is None:
                    continue
                findings_text = "\n".join(
                    f"  - {c.claim_text} (confidence: {c.confidence.level.value})"
                    for c in r.findings
                ) or "(no structured findings)"
                raw_excerpt = r.raw_data.get("final_response", "")[:500]
                context_parts.append(f"[{agent_name}]\nFindings:\n{findings_text}\n{raw_excerpt}")

            if context_parts:
                prior_context += "\n\n".join(context_parts) + "\n"
                # Cap prior_context to prevent unbounded token growth
                if len(prior_context) > 4000:
                    prior_context = prior_context[-4000:]

        # 3. Wrap each agent result in a DivisionReport
        reports: list[DivisionReport] = []
        for spec in sublab_plan.agents:
            result = all_results.get(spec.name)
            if result is None:
                continue

            if result.findings:
                avg_score = sum(c.confidence.score for c in result.findings) / len(result.findings)
                level = ConfidenceLevel.HIGH if avg_score >= 0.7 else ConfidenceLevel.MEDIUM if avg_score >= 0.4 else ConfidenceLevel.LOW if avg_score >= 0.15 else ConfidenceLevel.INSUFFICIENT
            else:
                avg_score = 0.0
                level = ConfidenceLevel.INSUFFICIENT

            reports.append(DivisionReport(
                division_id=f"sublab_{spec.name.lower().replace(' ', '_')}",
                division_name=f"SubLab: {spec.name}",
                lead_agent=spec.name,
                specialist_results=[result],
                synthesis=result.raw_data.get("final_response", "")[:2000],
                confidence=ConfidenceAssessment(level=level, score=avg_score),
            ))

        logger.info("[SubLabExecutor] Execution complete — %d reports produced", len(reports))
        return reports
