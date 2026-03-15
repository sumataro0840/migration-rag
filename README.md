# Excel Laravel Generator

Excelのテーブル定義から Laravel の Migration / Model / Controller / Route / Service / Repository / Request / Blade View を自動生成するツールです。

## 使い方

### 1. Excelにテーブル定義を書く

`tables.xlsx` の各シートに以下の列を用意する。

| カラム名 | 論理名 | 型 | 桁数 | NOT NULL | デフォルト | PK |
|---|---|---|---|---|---|---|

### 2. 依存パッケージをインストール

```WSL2
python3 -m venv venv
pip install -r requirements.txt
```

### 3. 一括生成（これだけでOK）

```bash
python3 generate_laravel_app.py tables.xlsx && \
python3 -m rag_laravel_generator.generate_backend_stack --root laravel_output && \
python3 generate_views.py tables.xlsx
```

`laravel_output/` に以下がすべて生成されます。

```
laravel_output/
├── database/migrations/
├── app/
│   ├── Models/
│   ├── Http/Controllers/
│   ├── Http/Requests/
│   ├── Services/
│   └── Repositories/
├── resources/views/
│   ├── layouts/app.blade.php     # 共通レイアウト（Tailwind）
│   ├── dashboard.blade.php       # トップページ
│   └── {table}/                  # テーブルごと
│       ├── index.blade.php
│       ├── create.blade.php
│       ├── edit.blade.php
│       ├── show.blade.php
│       └── partials/form.blade.php
└── routes/
    ├── web.php
    └── api.php
```

### 4. Laravelプロジェクトにコピー

```bash
cp -r laravel_output/database/migrations/* /path/to/laravel/database/migrations/
cp -r laravel_output/app/* /path/to/laravel/app/
cp -r laravel_output/resources/views/* /path/to/laravel/resources/views/
cp laravel_output/routes/web.php /path/to/laravel/routes/web.php
cp laravel_output/routes/api.php /path/to/laravel/routes/api.php
```

### 5. マイグレーション実行

```bash
php artisan migrate
php artisan serve
```

`http://localhost:8000` にアクセスするとダッシュボードが表示されます。

---

## 個別コマンド

特定テーブルのマイグレーションだけ再生成：
```bash
python3 rag_laravel_generator/generate_migration.py t_orders
```

スキーマ内容の確認：
```bash
python3 rag_laravel_generator/ingest_excel.py tables.xlsx
```