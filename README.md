# LoopAI

Claude CodeをPythonから呼び出してタスクを実行するCLIアプリケーション

## 概要

このツールは、Claude Codeをサブプロセスで実行し、指定されたタスクを実行します。従来のJSON形式のタスク定義に加え、自然言語でタスクを指定してClaude Codeが自律的に解釈・実行・改善する機能をサポートしています。Webサイト確認、テストコマンド実行、Claude Code確認など、多様な完了条件をサポートしています。

## 主な機能

- ✅ **タスク実行**: Claude Codeを呼び出してタスクを実行
- ✅ **完了条件チェック**: 複数の完了条件をサポート（ファイル存在、出力パターンなど）
- ✅ **自動リトライ**: 失敗時の自動再試行機能
- ✅ **クールタイム**: 同じエラー時の1分間の待機機能
- ✅ **CLIインターフェース**: 直感的なコマンドライン操作
- ✅ **JSON設定**: タスク定義をJSONファイルで管理
- ✅ **詳細なログ**: 実行結果と条件チェックの詳細なログ出力

## インストール

### 前提条件

- Python 3.7+
- Claude Codeがインストールされていること

### セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd claude-task-runner

# 依存関係のインストール（基本的には不要）
pip install -r requirements.txt
```

## 使用方法

### 基本的な使い方

#### JSON形式のタスク

```bash
# タスク定義ファイルのテンプレートを作成
python -m loopai create-template my_tasks.json

# タスク定義ファイルを検証
python -m loopai validate my_tasks.json

# タスク一覧を表示
python -m loopai list my_tasks.json

# すべてのタスクを実行
python -m loopai run my_tasks.json

# 特定のタスクを実行
python -m loopai run my_tasks.json --task-id specific_task

# 完了条件をチェック
python -m loopai check my_tasks.json --task-id specific_task

# ドライラン（シミュレーション）
python -m loopai run my_tasks.json --dry-run
```

#### 自然言語形式のタスク

```bash
# 自然言語でタスクを実行
python -m loopai run-natural "Hello, LoopAI!と出力して"

# タスク名を指定して実行
python -m loopai run-natural "現在時刻を表示して" --name "時刻表示タスク"

# 再試行回数とタイムアウトを指定して実行
python -m loopai run-natural "ファイルを作成して" --max-retries 5 --timeout 600
```

### コマンド詳細

#### `run` - タスクを実行

```bash
python -m loopai run <ファイル> [オプション]
```

オプション:
- `--task-id <ID>`: 実行する特定のタスクID
- `--dry-run`: 実際に実行せずにシミュレーション
- `--verbose, -v`: 詳細な出力を表示

#### `check` - 完了条件をチェック

```bash
python -m loopai check <ファイル> --task-id <ID> [オプション]
```

オプション:
- `--export-history <ファイル>`: 条件チェック履歴をエクスポート

#### `list` - タスク一覧を表示

```bash
python -m loopai list <ファイル> [オプション]
```

オプション:
- `--format <形式>`: 出力形式（table/json）

#### `validate` - タスク定義を検証

```bash
python -m loopai validate <ファイル>
```

#### `create-template` - テンプレート作成

```bash
python -m loopai create-template <ファイル>
```

## タスク定義ファイル形式

JSONファイルでタスクを定義します。

### 基本構造

```json
{
  "tasks": [
    {
      "id": "task_1",
      "name": "タスク名",
      "command": "claude code '実行するコマンド'",
      "completion_conditions": [
        {
          "type": "file_exists",
          "path": "./output/result.txt"
        }
      ],
      "max_retries": 3,
      "timeout": 300
    }
  ]
}
```

### 完了条件の種類

#### 1. `file_exists` - ファイル存在チェック

```json
{
  "type": "file_exists",
  "path": "./output/result.txt"
}
```

#### 2. `output_contains` - 出力にパターンが含まれる

```json
{
  "type": "output_contains",
  "pattern": "処理完了"
}
```

#### 3. `output_not_contains` - 出力にパターンが含まれない

```json
{
  "type": "output_not_contains",
  "pattern": "エラー"
}
```

#### 4. `file_contains` - ファイル内容にパターンが含まれる

```json
{
  "type": "file_contains",
  "path": "./output/result.txt",
  "pattern": "成功"
}
```

#### 5. `website_exists` - Webサイトの存在確認

```json
{
  "type": "website_exists",
  "url": "https://www.example.com",
  "timeout": 10
}
```

#### 6. `test_command` - テストコマンド実行

```json
{
  "type": "test_command",
  "command": "echo 'test success' && exit 0",
  "timeout": 30
}
```

#### 7. `claude_code_confirmation` - Claude Codeで確認

```json
{
  "type": "claude_code_confirmation",
  "prompt": "このタスクが正常に完了したらOKと答えてください",
  "timeout": 60
}
```

### パラメータ説明

| パラメータ | 必須 | 説明 |
|-----------|------|------|
| `id` | はい | タスクの一意な識別子 |
| `name` | はい | タスクの表示名 |
| `command` | はい | 実行するClaude Codeコマンド |
| `completion_conditions` | はい | 完了条件のリスト |
| `max_retries` | いいえ | 最大再試行回数（デフォルト: 3） |
| `timeout` | いいえ | タイムアウト秒数（デフォルト: 300） |

## 使用例

### サンプルタスク

```json
{
  "tasks": [
    {
      "id": "data_processing",
      "name": "データ処理タスク",
      "command": "claude code 'データを処理してください'",
      "completion_conditions": [
        {
          "type": "file_exists",
          "path": "./processed_data/output.csv"
        },
        {
          "type": "file_contains",
          "path": "./processed_data/output.csv",
          "pattern": "処理完了"
        }
      ],
      "max_retries": 5,
      "timeout": 600
    }
  ]
}
```

### 実行例

#### JSON形式タスクの実行

```bash
# タスク実行
python -m loopai run tasks/sample_tasks.json

# 特定タスクの実行
python -m loopai run tasks/sample_tasks.json --task-id hello_task

# 完了条件チェック
python -m loopai check tasks/sample_tasks.json --task-id hello_task

# 詳細な出力付きで実行
python -m loopai run tasks/sample_tasks.json --verbose
```

#### 自然言語タスクの実行

```bash
# 基本的な自然言語タスク
python -m loopai run-natural "Hello, LoopAI!と出力して"

# ファイル操作タスク
python -m loopai run-natural "テキストファイルを作成して、'Hello World'と書き込む"

# Web関連タスク
python -m loopai run-natural "https://www.google.comにアクセスできるか確認する"

# 複雑なタスク
python -m loopai run-natural "現在の日時を取得して、ログファイルに記録する"
```

### 新しい条件タイプの使用例

```json
{
  "tasks": [
    {
      "id": "web_check",
      "name": "Webサイト確認",
      "command": "echo 'Webサイトを確認します'",
      "completion_conditions": [
        {
          "type": "website_exists",
          "url": "https://www.google.com",
          "timeout": 10
        }
      ]
    },
    {
      "id": "test_validation",
      "name": "テスト検証",
      "command": "echo 'テストを実行します'",
      "completion_conditions": [
        {
          "type": "test_command",
          "command": "python -m pytest tests/ --tb=short",
          "timeout": 120
        }
      ]
    },
    {
      "id": "claude_approval",
      "name": "Claude承認",
      "command": "echo 'Claudeに承認を求めます'",
      "completion_conditions": [
        {
          "type": "claude_code_confirmation",
          "prompt": "この変更を承認しますか？承認する場合はOKと答えてください",
          "timeout": 60
        }
      ]
    }
  ]
}
```

## 動作仕様

### JSON形式タスクの流れ

1. タスク定義ファイルを読み込む
2. 指定されたタスクを実行
3. 完了条件をチェック
4. 条件を満たさない場合は再試行
5. 最大試行回数に達するまで繰り返し

### 自然言語タスクの流れ

1. 自然言語タスク説明を受け取る
2. Claude Codeがタスクを解釈して実行コマンドを生成
3. Claude Codeが完了条件を動的に生成
4. 生成されたコマンドを実行
5. 完了条件をチェック
6. 条件を満たさない場合は以下の自律的改善を実行：
   - 失敗原因の分析
   - 改善されたコマンドの生成
   - サブタスクの作成と実行
   - メインタスクの改善
7. 最大試行回数に達するまで繰り返し

### クールタイム機能

- 同じエラーが連続して発生した場合、1分間のクールタイムを適用
- クールタイム中はカウントダウンを表示
- 成功時は短い待機（10秒）、失敗時は長い待機（30秒）

### エラーハンドリング

- タイムアウト処理
- コマンド実行エラーの検出
- ファイルアクセスエラーの処理
- JSON形式エラーの検証

### 自律的改善機能

- **失敗原因分析**: Claude Codeがタスク失敗の原因を分析
- **コマンド改善**: 分析結果に基づいて改善されたコマンドを生成
- **サブタスク生成**: 改善のためのサブタスクを自動作成
- **自律的実行**: サブタスクを実行してメインタスクを改善
- **繰り返し改善**: 必要に応じて繰り返し改善プロセスを実行

## ディレクトリ構成

```
loopai/
├── loopai/
│   ├── __init__.py
│   ├── cli.py          # メインCLIモジュール
│   ├── task_executor.py # タスク実行機能
│   ├── condition_checker.py # 完了条件チェック
│   └── utils.py        # ユーティリティ関数
├── tasks/
│   └── sample_tasks.json # サンプルタスク
├── requirements.txt
└── README.md
```

## 開発

### プロジェクトのセットアップ

```bash
# 開発環境のセットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### テスト

```bash
# テスト用タスクの実行
python -m loopai run tasks/sample_tasks.json --dry-run

# 特定タスクのテスト
python -m loopai check tasks/sample_tasks.json --task-id hello_task
```

## 注意事項

- Claude Codeがシステムにインストールされている必要があります
- タスク実行には十分な権限が必要です
- 長時間実行するタスクには適切なタイムアウトを設定してください
- クールタイム機能は同じエラーが連続した場合にのみ適用されます

## ライセンス

このプロジェクトはMITライセンスで提供されています。

## 更新履歴

### v1.0.0
- 初期リリース
- 基本的なタスク実行機能
- 複数完了条件のサポート
- クールタイム機能
- CLIインターフェースの実装

### v1.1.0
- 新しい完了条件タイプの追加
  - `website_exists`: Webサイトの存在確認
  - `test_command`: テストコマンド実行
  - `claude_code_confirmation`: Claude Codeで確認
- コマンド名を `loopai` から `loopai` に変更
- Webサイト確認機能のための `requests` ライブラリの追加
- 詳細な条件チェックログの改善
- サンプルタスクの拡充
