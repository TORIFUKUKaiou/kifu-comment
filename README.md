# kifu-comment-try

将棋の棋譜（.kif）をAIで解析し、盤面再生・評価値グラフ・局面コメントをブラウザで表示する。

## デプロイ

```bash
cd infra
npm install
npx cdk deploy --parameters OpenAIApiKey=your-key
```

デプロイ後、出力される SiteUrl にアクセスするだけ。
Lambda では OpenAI SDK を vendoring せず、標準ライブラリの HTTP クライアントで Responses API を呼ぶため、macOS/CloudShell/Lambda 間のネイティブ依存差分を気にせずにデプロイできる。

## ローカル実行（解析のみ）

```bash
export OPENAI_API_KEY='your-key'
python3 analyze.py game.kif
```

## 構成

- S3 + CloudFront — フロント配信 + API配信（同一ドメイン）
- API Gateway + Lambda (Python 3.14) — .kif解析 + OpenAI API
- フロント — KifuForJS（盤面再生）+ Chart.js（評価値グラフ）

## 入力

- `.kif` ファイル（Shift_JIS / CP932）
- 評価値・候補手・読み筋が含まれていること
