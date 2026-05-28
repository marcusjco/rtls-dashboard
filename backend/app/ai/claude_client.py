"""
Claude Sonnet 4.6 client with tool use and streaming.
"""
import json
from typing import Generator
import anthropic

from app.config import get_settings
from app.ai.tools import TOOL_DEFINITIONS, handle_tool
from app.ai.prompts import build_system_prompt
from app.ai import rag as rag_module

settings = get_settings()
_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def chat_stream(
    message: str,
    history: list[dict],
    page_context: str = None,
    db=None,
) -> Generator[str, None, None]:
    """
    Stream a chat response from Claude with tool use.
    Yields Server-Sent Event strings: "data: {json}\n\n"
    """
    client = get_client()

    # RAG context retrieval
    rag_context = rag_module.retrieve(message) if message else ""

    system_prompt = build_system_prompt(
        page_context=page_context,
        rag_context=rag_context if rag_context else None,
    )

    # Build messages list
    messages = []
    for h in history[-20:]:  # keep last 20 turns
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    # Agentic tool-use loop
    max_tool_rounds = 5
    for _round in range(max_tool_rounds):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        # Collect text content and tool uses
        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # Stream any text content immediately
        if text_parts:
            combined = "".join(text_parts)
            yield f"data: {json.dumps({'type': 'text', 'content': combined})}\n\n"

        # If no tool calls or stop reason is end_turn, we're done
        if not tool_uses or response.stop_reason == "end_turn":
            break

        # Execute all tool calls
        tool_results = []
        for tool_use in tool_uses:
            # Notify frontend which tool is being called
            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_use.name, 'input': tool_use.input})}\n\n"

            result = handle_tool(tool_use.name, tool_use.input, db)

            # Notify frontend of result
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_use.name, 'result': result})}\n\n"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        # Add assistant response + tool results to messages for next round
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def generate_report(
    report_type: str,
    report_name: str,
    date_from,
    date_to,
    db,
) -> str:
    """Generate a report using Claude. Returns markdown string."""
    client = get_client()

    # Build a focused prompt for report generation
    prompt = f"""Generate a detailed operational report for Meridian Industrial's RTLS facility.

**Report Type:** {report_type}
**Report Name:** {report_name}
**Period:** {date_from.strftime('%B %d, %Y')} to {date_to.strftime('%B %d, %Y')}

Use your tools to gather data for this report. Then write a comprehensive report in markdown format with:
1. Executive Summary (2-3 sentences)
2. Key Metrics (use specific numbers from the data)
3. Detailed Findings (zone-by-zone or entity-by-entity as appropriate)
4. Issues & Alerts (any notable problems)
5. Recommendations (3-5 actionable items)

Be specific and data-driven. Use the actual data from the database."""

    messages = [{"role": "user", "content": prompt}]
    system = build_system_prompt(page_context="reports")

    full_text = []
    max_tool_rounds = 8

    for _round in range(max_tool_rounds):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=system,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                full_text.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        if not tool_uses or response.stop_reason == "end_turn":
            break

        tool_results = []
        for tool_use in tool_uses:
            result = handle_tool(tool_use.name, tool_use.input, db)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "\n".join(full_text)
