# Excel Laravel Generator + RAG

Excel表定義からLaravelコードを自動生成するツールです。追加でRetrieval Augmented Generation（RAG）を使い、Excel定義をベクトル検索してLLMでマイグレーションを生成できます。

## ディレクトリ構成

```
memoapp/
├── tables.xlsx                          # テーブル定義Excel
├── generate_laravel_app.py              # メインCLI（Excel→Laravel一括生成）
├── requirements.txt
├── generator/                           # コア生成ライブラリ
│   ├── excel_parser.py
│   ├── schema_converter.py
│   ├── migration_generator.py
│   ├── model_generator.py
│   ├── controller_generator.py
│   └── route_generator.py
├── rag_laravel_generator/               # RAG拡張
│   ├── ingest_excel.py
│   ├── embed_schema.py
│   ├── vector_store.py
│   ├── backend_stack_generator.py
│   └── generate_migration.py
└── laravel_output/                      # ★ 生成ファイルの出力先（自動作成）
    ├── database/migrations/
    ├── app/
    │   ├── Models/
    │   ├── Http/
    │   │   ├── Controllers/
    │   │   └── Requests/
    │   ├── Services/
    │   └── Repositories/
    └── routes/
        └── api.php
```

> **注意**: 生成ファイルはすべて `laravel_output/` に出力されます。
> Laravelプロジェクトへの適用は、出力先ディレクトリから手動でコピーしてください。

## アーキテクチャ

1. `generator/excel_parser.py`
   - pandas + openpyxlでExcelを読み込み
   - ヘッダーを正規化してテーブル定義を取り出す

2. `generator/schema_converter.py`
   - 正規化された行を `TableSchema` / `ColumnSchema` に変換

3. 既存ジェネレータ
   - `generator/migration_generator.py` などでLaravelコードを生成

4. RAG拡張
   - `rag_laravel_generator/ingest_excel.py`: Excel定義をテキスト化
   - `rag_laravel_generator/embed_schema.py`: OpenAI埋め込み作成
   - `rag_laravel_generator/vector_store.py`: ChromaDBに保存
   - `rag_laravel_generator/generate_migration.py`: テーブル名指定でマイグレーション生成
   - `rag_laravel_generator/backend_stack_generator.py`: 既存Model/MigrationからController/Service/Repository/Requestを生成

## 使い方

### Step 1: Excel → Migration / Model / Controller を一括生成

```bash
python3 generate_laravel_app.py tables.xlsx
```

`laravel_output/` 以下に全ファイルが生成されます。出力先を変えたい場合:

```bash
python3 generate_laravel_app.py tables.xlsx --output path/to/output
```

### Step 2: Model起点でService / Repository / Request を生成

Step 1 の実行後、`laravel_output/` の Models と Migrations を読み取って残りの層を生成します。

```bash
python3 -m rag_laravel_generator.generate_backend_stack --root laravel_output
```

`User` モデルも生成対象に含める場合:

```bash
python3 -m rag_laravel_generator.generate_backend_stack --root laravel_output --include-user
```

Step 1 で生成済みの Controller は自動的にスキップ（上書きなし）されます。

### Step 3: 特定テーブルのマイグレーションだけ再生成

```bash
python3 rag_laravel_generator/generate_migration.py t_orders
```

テーブル名は部分一致で検索します。Excelファイルのパスや出力先を変える場合:

```bash
python3 rag_laravel_generator/generate_migration.py t_orders \
  --excel path/to/tables.xlsx \
  --output path/to/output
```

### Step 4: スキーマ内容の確認

```bash
python3 rag_laravel_generator/ingest_excel.py tables.xlsx
```

### Laravelプロジェクトへの適用

```bash
# 例: laravel_output の内容を既存プロジェクトにコピー
cp -r laravel_output/database/migrations/* /path/to/laravel/database/migrations/
cp -r laravel_output/app/* /path/to/laravel/app/
cp laravel_output/routes/api.php /path/to/laravel/routes/api.php
```

## 依存関係

```bash
python3 -m pip install -r requirements.txt
```

| パッケージ | 用途 |
|---|---|
| pandas / openpyxl | Excel読み込み |
| chromadb | ベクトルストア（RAG用・任意） |
| openai | 埋め込み生成（RAG用・任意） |
| python-dotenv | 環境変数管理 |
| pytest | テスト |

RAG機能（embed_schema / vector_store）を使わない場合、`chromadb` と `openai` は不要です。

## テスト

```bash
pytest -q
```