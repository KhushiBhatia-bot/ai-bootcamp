import re

from backend.app.llm.ollama import generate_answer
from backend.app.llm.prompts import build_policy_prompt
from backend.app.rag.retriever import search_policy


VALID_STATUSES = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "NEEDS_REVIEW",
}


def evaluate_policy(scenario: str) -> dict:
    scenario = scenario.strip()

    if not scenario:
        raise ValueError("Scenario cannot be empty.")

    chunks = search_policy(scenario, top_k=5)

    # Do not make a decision without relevant policy evidence.
    if not chunks:
        return {
            "scenario": scenario,
            "status": "NEEDS_REVIEW",
            "reason": (
                "No sufficiently relevant policy evidence was found. "
                "Review the applicable policy manually."
            ),
            "claimed_policy": "",
            "claimed_page": "",
            "evidence": [],
            "retrieved_chunks": 0,
        }

    prompt = f"""
You are a policy compliance evaluation assistant.

Evaluate the scenario ONLY against the supplied policy evidence.
Do not invent policy rules, section numbers, or page numbers.
If the evidence is insufficient or ambiguous, choose NEEDS_REVIEW.

Return exactly these fields:
STATUS: COMPLIANT, NON_COMPLIANT, or NEEDS_REVIEW
REASON: A brief explanation grounded in the evidence
POLICY: The policy name supported by the evidence, or Unknown
PAGE: The page number supported by the evidence, or Unknown

Scenario:
{scenario}

Policy evidence:
{chr(10).join(
    f"Policy: {chunk.get('policy_name') or 'Unknown'} | "
    f"Page: {chunk.get('page') or 'Unknown'} | "
    f"Text: {chunk.get('text', '')}"
    for chunk in chunks
)}
"""

    answer = generate_answer(prompt)

    status_match = re.search(
        r"^\s*STATUS:\s*(COMPLIANT|NON_COMPLIANT|NEEDS_REVIEW)\b",
        answer,
        re.IGNORECASE | re.MULTILINE,
    )

    reason_match = re.search(
        r"^\s*REASON:\s*(.*)$",
        answer,
        re.IGNORECASE | re.MULTILINE,
    )

    policy_match = re.search(
        r"^\s*POLICY:\s*(.*)$",
        answer,
        re.IGNORECASE | re.MULTILINE,
    )

    page_match = re.search(
        r"^\s*PAGE:\s*(.*)$",
        answer,
        re.IGNORECASE | re.MULTILINE,
    )

    status = (
        status_match.group(1).upper()
        if status_match
        else "NEEDS_REVIEW"
    )

    reason = (
        reason_match.group(1).strip()
        if reason_match
        else "The model response could not be validated. Manual review is required."
    )

    # Include retrieved evidence so users can inspect the basis
    # for the assessment instead of relying only on the model's answer.
    evidence = [
        {
            "policy": chunk.get("policy_name") or "Unknown",
            "page": chunk.get("page"),
            "text": chunk.get("text", "")[:500],
            "distance": chunk.get("distance"),
        }
        for chunk in chunks
    ]

    return {
        "scenario": scenario,
        "status": status,
        "reason": reason,
        "claimed_policy": (
            policy_match.group(1).strip()
            if policy_match
            else ""
        ),
        "claimed_page": (
            page_match.group(1).strip()
            if page_match
            else ""
        ),
        "evidence": evidence,
        "retrieved_chunks": len(chunks),
    }
