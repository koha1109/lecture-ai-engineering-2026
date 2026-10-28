import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sft_dataset_is_jsonl_with_two_examples_per_glossary_term():
    result = subprocess.run(
        [sys.executable, "scripts/make_sft_dataset.py"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    records = [json.loads(line) for line in result.stdout.splitlines()]
    terms = json.loads((ROOT / "data/glossary.json").read_text(encoding="utf-8"))[
        "terms"
    ]

    assert len(records) == len(terms) * 2
    for record in records:
        messages = record["messages"]
        assert [message["role"] for message in messages] == [
            "system",
            "user",
            "assistant",
        ]
        assert messages[0]["content"]
        assert messages[1]["content"]

        target = json.loads(messages[2]["content"])
        assert set(target) == {"answer", "needs_review"}
        assert isinstance(target["answer"], str)
        assert target["needs_review"] is False

    answers = {json.loads(r["messages"][2]["content"])["answer"] for r in records}
    assert answers == {term["definition"] for term in terms}


def test_glossary_evaluation_covers_known_paraphrased_and_unknown_questions():
    terms = json.loads((ROOT / "data/glossary.json").read_text(encoding="utf-8"))[
        "terms"
    ]
    glossary_text = json.dumps(terms, ensure_ascii=False).casefold()
    evaluation = json.loads(
        (ROOT / "lectures/02/glossary_eval.json").read_text(encoding="utf-8")
    )
    cases = evaluation["cases"]

    assert Counter(case["category"] for case in cases) == {
        "用語集にある語": 4,
        "言い換え": 4,
        "用語集にない語": 4,
    }
    for case in cases:
        if case["expected_needs_review"]:
            assert case["must_include"] == ["確認が必要"]
        else:
            assert all(
                any(word in term["definition"] for term in terms)
                for word in case["must_include"]
            )

    for absent_term in ("FlashAttention-3", "DPO", "speculative decoding"):
        assert absent_term.casefold() not in glossary_text
