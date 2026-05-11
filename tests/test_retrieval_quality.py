import os

import pytest

from app.services.retrieval_service import RetrievalService
from evaluation.evaluator import RetrievalEvaluator


TEST_CASES = [
    {
        "query": (
            "How APIRouter works?"
        ),
        "expected_files": [
            "applications.py",
            "routing.py",
        ],
    },
    {
        "query": (
            "How dependency injection works?"
        ),
        "expected_files": [
            "dependencies",
            "params.py",
        ],
    },
    {
        "query": (
            "Explain FastAPI application structure"
        ),
        "expected_files": [
            "applications.py",
        ],
    },
]


def run_evaluation():
    for test_case in TEST_CASES:
        print("\n================================")
        print(
            f"QUERY: {test_case['query']}"
        )

        retrieval_service = RetrievalService()
        evaluator = RetrievalEvaluator()

        retrieval_results = (
            retrieval_service.search(
                query=test_case["query"],
                top_k=5,
            )
        )

        evaluation_result = (
            evaluator.evaluate(
                query=test_case["query"],
                retrieval_results=retrieval_results,
                expected_files=test_case[
                    "expected_files"
                ],
            )
        )

        print("\nPRECISION:")
        print(
            evaluation_result[
                "precision"
            ]
        )

        print("\nRECALL:")
        print(
            evaluation_result[
                "recall"
            ]
        )

        print("\nMATCHED FILES:")
        print(
            evaluation_result[
                "matched_files"
            ]
        )

        print("\nRETRIEVED FILES:")

        for file_path in evaluation_result[
            "retrieved_files"
        ]:
            print(file_path)


@pytest.mark.skipif(
    os.environ.get("RUN_RETRIEVAL_EVAL") != "1",
    reason=(
        "Retrieval evaluation is an integration test (requires a built index "
        "and may need network/model downloads). Set RUN_RETRIEVAL_EVAL=1 to run."
    ),
)
def test_retrieval_quality_integration():
    run_evaluation()


if __name__ == "__main__":
    run_evaluation()