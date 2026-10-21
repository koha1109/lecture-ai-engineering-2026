"""第1回: 素のLLMに会話形式で質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

最初の質問に答えたあと、空行を入力するまで会話履歴を保って続けて質問できる。
ツールは使わない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai.chats import Chat
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
DEFAULT_BENCHMARK_QUESTIONS = [
    DEFAULT_QUESTION,
    "LoRAとは何ですか？",
]
DEFAULT_BENCHMARK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]


def send_message(chat: Chat, question: str) -> tuple[str, float, int | None, int | None]:
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed = time.perf_counter() - started_at

    usage = response.usage_metadata
    prompt_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    return response.text, elapsed, prompt_tokens, output_tokens


def ask(chat: Chat, question: str) -> str:
    answer, elapsed, prompt_tokens, output_tokens = send_message(chat, question)
    print(f"[応答時間] {elapsed:.2f} 秒")
    if prompt_tokens is not None or output_tokens is not None:
        print(
            f"[トークン数] 入力: {prompt_tokens if prompt_tokens is not None else '不明'}, "
            f"出力: {output_tokens if output_tokens is not None else '不明'}"
        )
    return answer


def benchmark(client: genai.Client, models: list[str], questions: list[str]) -> None:
    print("[計測] 各モデル・質問につき1回ずつ実行します")
    print("[model]\t[質問]\t[応答時間(秒)]\t[入力トークン]\t[出力トークン]")
    measurements: dict[str, list[tuple[float, int | None, int | None]]] = {
        model: [] for model in models
    }
    for model in models:
        for question in questions:
            chat = client.chats.create(model=model)
            answer, elapsed, prompt_tokens, output_tokens = send_message(chat, question)
            measurements[model].append((elapsed, prompt_tokens, output_tokens))
            prompt_display = prompt_tokens if prompt_tokens is not None else "不明"
            output_display = output_tokens if output_tokens is not None else "不明"
            print(
                f"{model}\t{question}\t{elapsed:.2f}\t"
                f"{prompt_display}\t{output_display}"
            )
            print(f"[回答] {answer}\n")

    print("[モデル別平均]")
    print("[model]\t[平均応答時間(秒)]\t[平均入力トークン]\t[平均出力トークン]")
    for model, rows in measurements.items():
        avg_elapsed = sum(row[0] for row in rows) / len(rows)
        prompt_counts = [row[1] for row in rows if row[1] is not None]
        output_counts = [row[2] for row in rows if row[2] is not None]
        avg_prompt = sum(prompt_counts) / len(prompt_counts) if prompt_counts else None
        avg_output = sum(output_counts) / len(output_counts) if output_counts else None
        prompt_display = f"{avg_prompt:.1f}" if avg_prompt is not None else "不明"
        output_display = f"{avg_output:.1f}" if avg_output is not None else "不明"
        print(
            f"{model}\t{avg_elapsed:.2f}\t{prompt_display}\t{output_display}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに会話形式で質問する")
    parser.add_argument("questions", nargs="*")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="複数の質問を複数モデルで比較する",
    )
    parser.add_argument(
        "--models",
        metavar="MODEL1,MODEL2,...",
        help="比較するモデル（--benchmark 時。既定は3.5 Flash-Lite、3.5 Flash、3.8 Flash）",
    )
    args = parser.parse_args()

    if args.benchmark:
        requested_models = (
            [model.strip() for model in args.models.split(",") if model.strip()]
            if args.models
            else DEFAULT_BENCHMARK_MODELS
        )
        models = list(dict.fromkeys(requested_models))
        if len(models) < 2:
            parser.error("--benchmark では異なるモデルを2つ以上指定してください")
        questions = args.questions or DEFAULT_BENCHMARK_QUESTIONS
        if any(not question.strip() for question in questions):
            parser.error("空の質問は指定できません")
    else:
        if len(args.questions) > 1:
            parser.error("質問を複数指定する場合は --benchmark を付けてください")
        models = []
        questions = args.questions or [DEFAULT_QUESTION]

    print(f"[model] {', '.join(models) if args.benchmark else MODEL}")
    started_at = time.perf_counter()
    try:
        client = genai.Client(api_key=get_api_key())
        if args.benchmark:
            benchmark(client, models, questions)
            return

        question = questions[0]
        print(f"[質問] {question}\n")
        chat = client.chats.create(model=MODEL)
        print(ask(chat, question))

        while True:
            try:
                question = input("[続けて質問（空行で終了）] ")
            except EOFError:
                print()
                break
            if not question.strip():
                break
            print(f"\n[質問] {question}")
            print(ask(chat, question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    finally:
        print(f"[合計実行時間] {time.perf_counter() - started_at:.2f} 秒")


if __name__ == "__main__":
    main()
