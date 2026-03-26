# kifu-comment-try

将棋の棋譜（.kif）をOpenAI APIで解析し、局面のポイントをJSON形式で出力する。

## 実行方法

```bash
export OPENAI_API_KEY='your-key-here'
uv run analyze.py game.kif
```

## 入力

- `.kif` ファイル（Shift_JIS）
- 評価値・候補手・読み筋が含まれていること

## 出力

JSON（標準出力）
