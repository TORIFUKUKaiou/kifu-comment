# kifu-comment-try

将棋の棋譜（.kif）をOpenAI APIで解析し、局面のポイントをJSON形式で出力する。
盤面再生・評価値グラフ・AIコメントをブラウザで表示。

## ローカル実行

```bash
export OPENAI_API_KEY='your-key-here'
uv run analyze.py game.kif
```

## AWSデプロイ

```bash
# Lambda依存パッケージ
cd lambda
pip install openai -t .

# CDKデプロイ
cd ../infra
npm install
npx cdk deploy --parameters OpenAIApiKey=your-key
```

デプロイ後、出力される SiteUrl にアクセス。
初回アクセス時に ApiEndpoint の URL を入力する。

## 構成

- Lambda (Python 3.14): .kif解析 + OpenAI API呼び出し
- API Gateway: POST /analyze
- S3 + CloudFront: フロントエンド配信
- フロント: KifuForJS（盤面再生）+ Chart.js（評価値グラフ）

## 入力

- `.kif` ファイル（Shift_JIS / CP932）
- 評価値・候補手・読み筋が含まれていること
