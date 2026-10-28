"""第2回 宿題（発展）: 用語集から SFT 用の Q&A データ（JSONL）を作る。

使い方:
    uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl

1 用語につき質問を 2 通り作り、assistant の回答は needs_review を含む JSON にする。
できたファイルを Colab にアップロードし、LoRA 学習のデータとして使う。
"""

import json
import sys
from pathlib import Path

GLOSSARY = Path(__file__).resolve().parent.parent / "data" / "glossary.json"
TEMPLATES = ["「{term}」とは何ですか？", "{term}について簡単に説明してください。"]
SYSTEM_PROMPT = (
    "あなたは講座用語集の回答係です。学習データに根拠がある質問には、"
    "定義を answer にして needs_review を false にした JSON 1 行だけで答えてください。"
    "学習データに根拠がない質問には、answer に"
    "『用語集に記載がありません。確認が必要です。』と書き、needs_review を true にしてください。"
)


def main() -> None:
    terms = json.loads(GLOSSARY.read_text(encoding="utf-8"))["terms"]
    for t in terms:
        for template in TEMPLATES:
            target = json.dumps(
                {"answer": t["definition"], "needs_review": False},
                ensure_ascii=False,
            )
            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": template.format(term=t["term"])},
                    {"role": "assistant", "content": target},
                ]
            }
            sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
