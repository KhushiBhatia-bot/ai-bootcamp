
from backend.app.llm.ollama import generate_answer
from backend.app.llm.prompts import build_policy_prompt
from backend.app.rag.retriever import search_policy


VALID_STATUSES = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "NEEDS_REVIEW",
}


def ask_policy(question: str) -> dict:
    """Answer a question using retrieved policy passages."""

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    chunks = search_policy(question, top_k=5)

    prompt = build_policy_prompt(
        question=question,
        chunks=chunks,
    )

    answer = generate_answer(prompt)

    sources = [
        {
            "policy": chunk.get("policy_name"),
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
    }


def evaluate_policy(scenario: str) -> dict:
    """
    Evaluate a scenario against retrieved policy evidence.

    The LLM produces a structured decision, but its output is
    treated as a recommendation requiring evidence-based review.
    """

    scenario = scenario.strip()

    if not scenario:
        raise ValueError("Scenario cannot be empty.")

    chunks = search_policy(scenario, top_k=5)

    if not chunks:
        return {
            "scenario": scenario,
            "status": "NEEDS_REVIEW",
            "reason": "No relevant policy evidence was retrieved.",
            "evidence": [],
            "retrieved_chunks": 0,
        }

    evidence_text = "\n\n".join(
        (
            f"Policy: {chunk.get('policy_name')}\n"
            f"Page: {chunk.get('page')}\n"
            f"Text: {chunk.get('text', '')}"
        )
        for chunk in chunks
    )

    prompt = f"""
You are PolicyGuard AI, a policy compliance assessment assistant.

Assess the scenario using ONLY the policy evidence supplied below.

SCENARIO:
{scenario}

POLICY EVIDENCE:
{evidence_text}

Return exactly these four fields, each on its own line:
STATUS: COMPLIANT, NON_COMPLIANT, or NEEDS_REVIEW
REASON: A concise explanation based on the evidence
POLICY: The policy name that supports the assessment
PAGE: The page number, or UNKNOWN if unavailable

Rules:
- COMPLIANT means the evidence supports compliance.
- NON_COMPLIANT means the evidence directly supports a violation.
- NEEDS_REVIEW means evidence is missing, ambiguous, or insufficient.
- Do not invent policy requirements or citations.
- If the scenario lacks necessary details, choose NEEDS_REVIEW.
- Do not treat a missing policy statement as proof of compliance.
- Keep the reason concise.
"""

    answer = generate_answer(prompt)

    # Parse the model's simple structured response.
    fields = {}

    for line in answer.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip().upper()] = value.strip()

    status = fields.get("STATUS", "").upper()

    if status not in VALID_STATUSES:
        status = "NEEDS_REVIEW"

    reason = fields.get(
        "REASON",
        "The model did not provide a clear assessment. Manual review is needed.",
    )

    # Return retrieved evidence as well as the model's claimed citation.
    sources = [
        {
            "policy": chunk.get("policy_name"),
            "page": chunk.get("page"),
            "text": chunk.get("text", "")[:300],
        }
        for chunk in chunks
    ]

    return {
        "scenario": scenario,
        "status": status,
        "reason": reason,
        "claimed_policy": fields.get("POLICY", "UNKNOWN"),
        "claimed_page": fields.get("PAGE", "UNKNOWN"),
        "evidence": sources,
        "retrieved_chunks": len(chunks),
    }