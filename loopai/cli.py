"""
CLIメインモジュール
"""
import argparse
import sys
import os
import json
from typing import List, Optional
from .utils import Task, NaturalLanguageTask, load_tasks_from_json, save_tasks_to_json
from .task_executor import TaskExecutor
from .natural_language_executor import NaturalLanguageTaskExecutor
from .condition_checker import ConditionChecker


def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成する"""
    parser = argparse.ArgumentParser(
        description='Claude Codeを呼び出してタスクを実行するCLIツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python -m loopai run tasks.json
  python -m loopai run-natural "Hello, LoopAI!と出力して"
  python -m loopai check tasks.json --task-id task_1
  python -m loopai list tasks.json
  python -m loopai validate tasks.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    # runコマンド（従来のJSON形式）
    run_parser = subparsers.add_parser('run', help='JSON形式のタスクを実行する')
    run_parser.add_argument('file', help='タスク定義ファイルのパス')
    run_parser.add_argument('--task-id', help='実行するタスクID (指定しない場合はすべて実行)')
    run_parser.add_argument('--dry-run', action='store_true', help='実際に実行せずにシミュレーションする')
    run_parser.add_argument('--verbose', '-v', action='store_true', help='詳細な出力を表示する')
    
    # run-naturalコマンド（自然言語形式）
    natural_parser = subparsers.add_parser('run-natural', help='自然言語でタスクを実行する')
    natural_parser.add_argument('description', help='実行するタスクの自然言語説明')
    natural_parser.add_argument('--name', help='タスク名（指定しない場合は自動生成）')
    natural_parser.add_argument('--max-retries', type=int, default=3, help='最大再試行回数')
    natural_parser.add_argument('--timeout', type=int, default=300, help='タイムアウト秒数')
    
    # checkコマンド
    check_parser = subparsers.add_parser('check', help='完了条件をチェックする')
    check_parser.add_argument('file', help='タスク定義ファイルのパス')
    check_parser.add_argument('--task-id', required=True, help='チェックするタスクID')
    check_parser.add_argument('--export-history', help='条件チェック履歴をエクスポートするファイルパス')
    
    # listコマンド
    list_parser = subparsers.add_parser('list', help='タスク一覧を表示する')
    list_parser.add_argument('file', help='タスク定義ファイルのパス')
    list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='出力形式')
    
    # validateコマンド
    validate_parser = subparsers.add_parser('validate', help='タスク定義ファイルを検証する')
    validate_parser.add_argument('file', help='タスク定義ファイルの_path')
    
    # create-templateコマンド
    template_parser = subparsers.add_parser('create-template', help='タスク定義ファイルのテンプレートを作成する')
    template_parser.add_argument('file', help='作成するテンプレートファイルのパス')
    
    return parser


def run_tasks(args) -> None:
    """JSON形式のタスクを実行する"""
    try:
        # タスクファイルを読み込む
        tasks = load_tasks_from_json(args.file)
        
        # タスクIDが指定されている場合はフィルタリング
        if args.task_id:
            tasks = [task for task in tasks if task.id == args.task_id]
            if not tasks:
                print(f"エラー: タスクID '{args.task_id}' が見つかりません")
                sys.exit(1)
        
        if args.dry_run:
            print("=== ドライラン（シミュレーション）===")
            for task in tasks:
                print(f"\nタスク: {task.name} ({task.id})")
                print(f"コマンド: {task.command}")
                print(f"完了条件: {len(task.completion_conditions)}個")
                for i, condition in enumerate(task.completion_conditions):
                    print(f"  条件{i+1}: {condition}")
            return
        
        # タスク実行
        executor = TaskExecutor()
        results = executor.execute_tasks(tasks)
        
        # 結果の表示
        summary = executor.get_task_summary(results)
        print(summary)
        
        # 終了コードを設定
        all_success = all(result['success'] for result in results.values())
        sys.exit(0 if all_success else 1)
        
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSONエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        sys.exit(1)


def run_natural_language_task(args) -> None:
    """自然言語タスクを実行する"""
    try:
        # タスク名の生成
        task_name = args.name or f"自然言語タスク_{hash(args.description) % 10000}"
        task_id = f"natural_{hash(args.description) % 10000}"
        
        # 自然言語タスクの作成
        task = NaturalLanguageTask(
            id=task_id,
            name=task_name,
            description=args.description,
            max_retries=args.max_retries,
            timeout=args.timeout
        )
        
        print(f"🚀 自然言語タスクを開始します")
        print(f"タスク名: {task_name}")
        print(f"タスク説明: {args.description}")
        print(f"最大再試行回数: {args.max_retries}")
        print(f"タイムアウト: {args.timeout}秒")
        print("=" * 50)
        
        # 自然言語タスク実行
        executor = NaturalLanguageTaskExecutor()
        results = {task_id: {'success': False, 'task': task}}
        
        success = executor.execute_natural_language_task_until_completion(task)
        results[task_id]['success'] = success
        
        # 結果の表示
        summary = executor.get_natural_language_task_summary(results)
        print(summary)
        
        # 終了コードを設定
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        sys.exit(1)


def check_conditions(args) -> None:
    """完了条件をチェックする"""
    try:
        # タスクファイルを読み込む
        tasks = load_tasks_from_json(args.file)
        
        # 指定されたタスクを検索
        task = None
        for t in tasks:
            if t.id == args.task_id:
                task = t
                break
        
        if not task:
            print(f"エラー: タスクID '{args.task_id}' が見つかりません")
            sys.exit(1)
        
        # 条件チェック
        checker = ConditionChecker()
        summary = checker.get_condition_summary(task)
        print(summary)
        
        # 履歴のエクスポート
        if args.export_history:
            checker.export_condition_history(args.export_history)
        
        # 終了コードを設定
        all_conditions_met = all(checker._check_single_condition(condition, task) 
                               for condition in task.completion_conditions)
        sys.exit(0 if all_conditions_met else 1)
        
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSONエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        sys.exit(1)


def list_tasks(args) -> None:
    """タスク一覧を表示する"""
    try:
        tasks = load_tasks_from_json(args.file)
        
        if args.format == 'json':
            # JSON形式で出力
            task_list = []
            for task in tasks:
                task_list.append({
                    'id': task.id,
                    'name': task.name,
                    'command': task.command,
                    'completion_conditions_count': len(task.completion_conditions),
                    'max_retries': task.max_retries,
                    'timeout': task.timeout
                })
            print(json.dumps(task_list, ensure_ascii=False, indent=2))
        else:
            # テーブル形式で出力
            print(f"{'ID':<15} {'名前':<20} {'条件数':<8} {'最大再試行':<10} {'タイムアウト':<10}")
            print("-" * 70)
            for task in tasks:
                print(f"{task.id:<15} {task.name[:19]:<20} {len(task.completion_conditions):<8} "
                      f"{task.max_retries:<10} {task.timeout:<10}")
        
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSONエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        sys.exit(1)


def validate_tasks(args) -> None:
    """タスク定義ファイルを検証する"""
    try:
        tasks = load_tasks_from_json(args.file)
        
        print(f"✅ ファイル形式が正しいことを確認しました")
        print(f"📋 タスク数: {len(tasks)}")
        
        errors = []
        warnings = []
        
        for task in tasks:
            # 必須フィールドのチェック
            if not task.id:
                errors.append(f"タスク '{task.name}' にIDがありません")
            if not task.name:
                errors.append(f"タスク '{task.id}' に名前がありません")
            if not task.command:
                errors.append(f"タスク '{task.name}' にコマンドがありません")
            if not task.completion_conditions:
                warnings.append(f"タスク '{task.name}' に完了条件がありません")
            
            # 完了条件のチェック
            for i, condition in enumerate(task.completion_conditions):
                condition_type = condition.get('type')
                if not condition_type:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} にタイプがありません")
                elif condition_type not in ['file_exists', 'output_contains', 'output_not_contains', 'file_contains',
                                          'website_exists', 'test_command', 'claude_code_confirmation']:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} に未知のタイプ '{condition_type}' があります")
                elif condition_type in ['file_exists', 'file_contains'] and 'path' not in condition:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} にパスがありません")
                elif condition_type in ['output_contains', 'output_not_contains', 'file_contains'] and 'pattern' not in condition:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} にパターンがありません")
                elif condition_type == 'website_exists' and 'url' not in condition:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} にURLがありません")
                elif condition_type == 'test_command' and 'command' not in condition:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} にコマンドがありません")
                elif condition_type == 'claude_code_confirmation' and 'prompt' not in condition:
                    errors.append(f"タスク '{task.name}' の条件 {i+1} にプロンプトがありません")
        
        # 結果の表示
        if errors:
            print(f"\n❌ エラーが {len(errors)} 個見つかりました:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        elif warnings:
            print(f"\n⚠️  警告が {len(warnings)} 個あります:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print(f"\n✅ すべてのタスクが正常に検証されました")
        
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSONエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        sys.exit(1)


def create_template(args) -> None:
    """タスク定義ファイルのテンプレートを作成する"""
    template = {
        "tasks": [
            {
                "id": "sample_task_1",
                "name": "サンプルタスク1",
                "command": "echo 'Hello, World!'",
                "completion_conditions": [
                    {
                        "type": "output_contains",
                        "pattern": "Hello"
                    }
                ],
                "max_retries": 3,
                "timeout": 300
            },
            {
                "id": "sample_task_2",
                "name": "サンプルタスク2",
                "command": "touch sample.txt && echo 'Sample content' > sample.txt",
                "completion_conditions": [
                    {
                        "type": "file_exists",
                        "path": "sample.txt"
                    },
                    {
                        "type": "file_contains",
                        "path": "sample.txt",
                        "pattern": "Sample content"
                    }
                ],
                "max_retries": 5,
                "timeout": 600
            }
        ]
    }
    
    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(args.file), exist_ok=True)
        
        with open(args.file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"✅ テンプレートファイルを作成しました: {args.file}")
        print(f"\nこのファイルを編集して、ご自身のタスクを定義してください。")
        
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


def main() -> None:
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'run':
        run_tasks(args)
    elif args.command == 'run-natural':
        run_natural_language_task(args)
    elif args.command == 'check':
        check_conditions(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'validate':
        validate_tasks(args)
    elif args.command == 'create-template':
        create_template(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()