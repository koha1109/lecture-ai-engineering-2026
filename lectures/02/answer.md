# 第2回 解答

## 提出物の整理

- **提出先**：`lec02` ブランチから自分の fork の `main` へ PR を作成する。
- **必須**：この `answer.md` に演習の結果・考察と、宿題で選んだレベルの結果・考察を書く。
- **任意の添付**：演習の `result.json` や `eval_before.json` / `eval_after.json`、宿題の学習データ・評価データを PR に含めてもよい。
- **現在の進捗**：演習と宿題（発展）の学習・評価を実施し、結果を記入済み。

## 演習

- 使ったモデル・設定：`Qwen/Qwen3.5-0.8B`、LoRA（量子化なし）、seed 42、20 epochs、`lr=0.0002`、`lora_r=16`、`lora_alpha=32`、`max_seq_len=512`。ライブラリは transformers 5.18.0 / peft 0.21.1 / trl 1.14.2 / torch 2.11.0+cu130。
- 自分で学習を実行したか：はい（`executed_training_myself=true`）範囲は全てです。

| 指標（21問） | 学習前 | 学習後 |
|---|---:|---:|
| 形式遵守率 (`format_rate`) | 9.5% (2/21) | 100% (21/21) |
| 内容正解率 (`content_rate`) | 0% (0/21) | 90.5% (19/21) |
| 両方正解率 (`both_rate`) | 0% (0/21) | 90.5% (19/21) |
| 評価時間 | 39.9秒 | 46.9秒 |

- 最終Training Loss / 学習時間： 0.014008 / 256 秒
- 退行した質問：なし（`regressed=[]`）
- 学習後に残った失敗：内容正解率は19/21。形式は全問で守れたが、用語集にない質問6問のうち2問でFAQにない内容を断定した。
  - 「成績はいつ出ますか」：提出期限（9月30日23:59）を回答し、`needs_review=false` と断定した。
  - 「オフィスアワーは事前予約が必要ですか」：オフィスアワーの日時を回答し、予約の要否には答えず `needs_review=false` と断定した。
  - 他の未掲載質問4問（講義録画、文字数制限、フィードバック、参考文献の指定）では、確認が必要と正しく回答した。
- 知識を問う質問の結果：
  - 「この講座の最終課題の締切はいつですか」：学習前 `format_error` → 学習後 `asserted`。FAQの提出期限を最終課題の締切だと取り違えた。
  - 「担当教員の名前は何ですか」：学習前 `format_error` → 学習後 `needs_review`。
  - 「次回の講義のテーマは何ですか」：学習前 `format_error` → 学習後 `needs_review`。
  - 「課題の提出期限はいつですか」：学習前 `format_error` → 学習後 `asserted`。これはFAQに記載された内容への対照質問。
  - `eval_before` / `eval_after` の「FAQ にある」は知識質問の生成時に `q in gold` で判定される。対照質問は評価用 `gold` に入っていないため `false` と表示されるが、FAQ本文にはある質問である。
- 学習で変わったこと・変わらなかったこと：形式遵守率は9.5%から100%に上がり、回答形式と既知のFAQ内容は大きく改善した。一方、形式が整っても未知情報を正しく見分けられるとは限らず、最終課題の締切をFAQの提出期限から推測して断定する誤りが残った。

## 宿題

- 選んだレベル：発展
- 学習データ：[`glossary_sft.jsonl`](./glossary_sft.jsonl)。用語集58件から2種類ずつ質問を作り、計116件で学習した。各データは `system` / `user` / `assistant` の `messages` 形式。
- 評価データ：[`glossary_eval.json`](./glossary_eval.json) の12問（用語集にある語4問、言い換え4問、用語集にない語・情報4問）。
- 実行したか：はい（[`homework_result/result.json`](./homework_result/result.json) の `executed_training_myself=true`）。モデルは `Qwen/Qwen3.5-0.8B`、LoRA（量子化なし）、seed 42、3 epochs、`lr=0.0002`、`lora_r=16`、`max_new_tokens=384`。ライブラリは transformers 5.18.0 / peft 0.21.1 / trl 1.14.2 / torch 2.11.0+cu130。

| 指標（12問） | 学習前 | 学習後 |
|---|---:|---:|
| 形式遵守率 (`format_rate`) | 91.7% (11/12) | 91.7% (11/12) |
| 内容正解率 (`content_rate`) | 8.3% (1/12) | 0% (0/12) |
| 両方正解率 (`both_rate`) | 8.3% (1/12) | 0% (0/12) |
| 評価時間 | 44.9秒 | 54.5秒 |

- 退行した質問：1問。「DPO（Direct Preference Optimization）の講座内での定義を教えてください」は学習前に確認要求で内容正解だったが、学習後は長い不正なJSONになり、`format_error` となった。
- 学習後の失敗：形式は11/12問で守ったが、内容正解は0/12問。用語集にある4語・言い換え4問はいずれも、正しい定義や必須語句を十分に返せなかった。FAQにない質問4問もすべて不正解で、FlashAttention-3、投機的デコード、GPU予約時間には根拠のない説明を生成し、DPOではJSON形式自体が崩れた。
- 知識質問：学習前はFlashAttention-3とDPO、GPU予約時間で確認要求できた一方、投機的デコードは誤答した。学習後は未掲載の4問すべてで確認要求できず、別概念を当てはめて断定するか形式を崩した。対照のLoRA質問は学習前後とも `needs_review=false` だが、定義は用語集に沿わず内容不正解だった。
- 最終Training Loss / 学習時間：[`homework_result/result.json`](./homework_result/result.json) に記録なし。44.9秒・54.5秒は学習前後それぞれの評価時間であり、学習時間ではない。
- 学習データは全116件が `needs_review:false` の既知用語の回答例で、未知語に対して確認要求する正例を含めていない。このため、未掲載の質問に対する判断を学ぶ教師信号が不足していた可能性がある。結果からは、データを用語集のQ&Aに置き換えただけでは定義の正確さも未知語への慎重さも改善しなかった。

生の評価結果：[`homework_result/eval_before.json`](./homework_result/eval_before.json) / [`homework_result/eval_after.json`](./homework_result/eval_after.json)。演習の生の結果は [`exercise_result/result.json`](./exercise_result/result.json)、[`exercise_result/eval_before.json`](./exercise_result/eval_before.json)、[`exercise_result/eval_after.json`](./exercise_result/eval_after.json)。

### ファインチューニングと用語集検索エージェントの比較

今回の用語集SFTでは、学習後の内容正解率が0%で、未掲載語の4問にも適切に確認要求できなかった。今回の結果に限れば、用語の定義を正確に参照する用途では、用語集検索エージェントの方が適していると考える。検索なら質問時に元の定義を参照でき、用語の更新に再学習も要らない。ただし、検索エージェントとの同一質問による直接比較は今回実施していないため、優位性を実測したわけではない。ファインチューニングは回答形式や口調を安定させる用途に使い、検索と組み合わせる方法も考えられる。
