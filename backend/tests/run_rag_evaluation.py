
import json

from backend.app.rag.evaluation import evaluate_retrieval


def main():
    report = evaluate_retrieval(top_k=5)

    print("\n=== PolicyGuard AI: RAG Evaluation ===")
    print(f"Test queries: {report['total_queries']}")
    print(f"Hit Rate@{report['top_k']}: {report['hit_rate']:.1%}")
    print(
        f"Precision@{report['top_k']}: "
        f"{report['precision_at_k']:.1%}"
    )
    print(f"Queries with hits: {report['queries_with_hits']}")
    print("\nIndividual results:")

    for result in report["results"]:
        status = "PASS" if result["hit"] else "MISS"

        print(f"\n[{status}] {result['id']}")
        print(f"Query: {result['query']}")
        print(
            f"Relevant chunks: {result['relevant_count']} / "
            f"{result['retrieved_count']} retrieved"
        )
        print(f"Distances: {result['distances']}")

    with open(
        "rag_evaluation_report.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(report, file, indent=2)

    print("\nReport saved to rag_evaluation_report.json")


if __name__ == "__main__":
    main()
