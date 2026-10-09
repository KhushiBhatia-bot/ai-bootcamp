
import re
from time import perf_counter

from backend.app.llm.ollama import generate_answer
from backend.app.llm.prompts import build_policy_prompt
from backend.app.rag.retriever import search_policy


VALID_STATUSES = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "NEEDS_REVIEW",
}


def ask_policy(question: str) -> dict:
    """
    Answer a policy question using retrieved policy evidence.

    Returns the answer, source references, and timing metrics.
    """
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    total_start = perf_counter()

    retrieval_start = perf_counter()
    chunks = search_policy(question, top_k=5)
    retrieval_ms = round(
        (perf_counter() - retrieval_start) * 1000, 2
    )

    if not chunks:
        return {
            "question": question,
            "answer": (
                "I could not find sufficiently relevant policy "
                "evidence. Please review the applicable policy manually."
            ),
            "sources": [],
            "retrieved_chunks": 0,
            "retrieval_ms": retrieval_ms,
            "generation_ms": 0.0,
            "total_ms": round(
                (perf_counter() - total_start) * 1000, 2
            ),
            "search_mode": "vector",
        }

    prompt = build_policy_prompt(
        question=question,
        chunks=chunks,
    )

    generation_start = perf_counter()
    answer = generate_answer(prompt)
    generation_ms = round(
        (perf_counter() - generation_start) * 1000, 2
    )

    sources = [
        {
            "policy": chunk.get("policy_name") or "Unknown",
            "page": chunk.get("page"),
            "text": chunk.get("text", "")[:300],
        }
        for chunk in chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(chunks),
        "retrieval_ms": retrieval_ms,
        "generation_ms": generation_ms,
        "total_ms": round(
            (perf_counter() - total_start) * 1000, 2
        ),
        "search_mode": "vector",
    }


def evaluate_policy(scenario: str) -> dict:
    """
    Evaluate a scenario against retrieved policy evidence.

    If evidence is unavailable or the model returns an invalid
    status, the result defaults to NEEDS_REVIEW.
    """
    scenario = scenario.strip()

    if not scenario:
        raise ValueError("Scenario cannot be empty.")

    total_start = perf_counter()

    retrieval_start = perf_counter()
    chunks = search_policy(scenario, top_k=5)
    retrieval_ms = round(
        (perf_counter() - retrieval_start) * 1000, 2
    )

    # Fail safely when there is no sufficiently relevant evidence.
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
            "retrieval_ms": retrieval_ms,
            "generation_ms": 0.0,
            "total_ms": round(
                (perf_counter() - total_start) * 1000, 2
            ),
            "search_mode": "vector",
        }

    policy_evidence = "\n\n".join(
        (
            f"Policy: {chunk.get('policy_name') or 'Unknown'}\n"
            f"Page: {chunk.get('page') or 'Unknown'}\n"
            f"Text: {chunk.get('text', '')}"
        )
        for chunk in chunks
    )

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
{policy_evidence}
"""

    generation_start = perf_counter()
    answer = generate_answer(prompt)
    generation_ms = round(
        (perf_counter() - generation_start) * 1000, 2
    )

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

    # Do not accept statuses outside the allowed set.
    status = (
        status_match.group(1).upper()
        if status_match
        else "NEEDS_REVIEW"
    )

    if status not in VALID_STATUSES:
        status = "NEEDS_REVIEW"

    reason = (
        reason_match.group(1).strip()
        if reason_match
        else (
            "The model response could not be validated. "
            "Manual review is required."
        )
    )

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
        "retrieval_ms": retrieval_ms,
        "generation_ms": generation_ms,
        "total_ms": round(
            (perf_counter() - total_start) * 1000, 2
        ),
        "search_mode": "vector",
    }

