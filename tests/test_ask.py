from types import SimpleNamespace

from app import ask as ask_module


def test_default_benchmark_models_include_flash_38():
    assert ask_module.DEFAULT_BENCHMARK_MODELS == [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.8-flash",
    ]


def test_main_keeps_history_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []

    class FakeChat:
        def send_message(self, question):
            sent_messages.append(question)
            return SimpleNamespace(
                text=f"回答: {question}",
                usage_metadata=None,
            )

    chat = FakeChat()

    class FakeClient:
        class Chats:
            def create(self, *, model):
                assert model == ask_module.MODEL
                return chat

        chats = Chats()

    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    questions = iter(["続けて質問", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.main()

    assert sent_messages == ["最初の質問", "続けて質問"]
    output = capsys.readouterr().out
    assert "回答: 最初の質問" in output
    assert "回答: 続けて質問" in output
    assert "[応答時間]" in output
    assert "[合計実行時間]" in output


def test_benchmark_runs_each_question_with_each_model(capsys):
    requests = []

    class FakeChat:
        def __init__(self, model):
            self.model = model

        def send_message(self, question):
            requests.append((self.model, question))
            return SimpleNamespace(
                text="テスト回答",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=20,
                ),
            )

    class FakeClient:
        class Chats:
            def create(self, *, model):
                return FakeChat(model)

        chats = Chats()

    ask_module.benchmark(
        FakeClient(),
        ["model-a", "model-b"],
        ["質問1", "質問2"],
    )

    assert requests == [
        ("model-a", "質問1"),
        ("model-a", "質問2"),
        ("model-b", "質問1"),
        ("model-b", "質問2"),
    ]
    output = capsys.readouterr().out
    assert "model-a\t質問1" in output
    assert "10\t20" in output
    assert "model-a\t" in output
    assert "[モデル別平均]" in output
