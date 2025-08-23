"""
ユーティリティ関数
"""
import json
import os
import time
import subprocess
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class NaturalLanguageTask:
    """自然言語タスクデータクラス"""
    id: str
    name: str
    description: str
    max_retries: int = 3
    timeout: int = 300
    retry_count: int = 0
    last_error: Optional[str] = None
    last_output: Optional[str] = None
    generated_command: Optional[str] = None
    generated_conditions: Optional[List[Dict[str, Any]]] = None
    subtasks: Optional[List['NaturalLanguageTask']] = None


@dataclass
class Task:
    """タスクデータクラス（互換性のため）"""
    id: str
    name: str
    command: str
    completion_conditions: List[Dict[str, Any]]
    max_retries: int = 3
    timeout: int = 300
    retry_count: int = 0
    last_error: Optional[str] = None
    last_output: Optional[str] = None


@dataclass
class ExecutionResult:
    """実行結果データクラス"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0


def load_tasks_from_json(file_path: str) -> List[Task]:
    """JSONファイルからタスクを読み込む"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"タスクファイルが見つかりません: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tasks = []
    for task_data in data.get('tasks', []):
        task = Task(
            id=task_data['id'],
            name=task_data['name'],
            command=task_data['command'],
            completion_conditions=task_data['completion_conditions'],
            max_retries=task_data.get('max_retries', 3),
            timeout=task_data.get('timeout', 300)
        )
        tasks.append(task)
    
    return tasks


def save_tasks_to_json(file_path: str, tasks: List[Task]) -> None:
    """タスクをJSONファイルに保存する"""
    data = {
        'tasks': [
            {
                'id': task.id,
                'name': task.name,
                'command': task.command,
                'completion_conditions': task.completion_conditions,
                'max_retries': task.max_retries,
                'timeout': task.timeout,
                'retry_count': task.retry_count,
                'last_error': task.last_error,
                'last_output': task.last_output
            }
            for task in tasks
        ]
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def execute_command(command: str, timeout: int = 300) -> ExecutionResult:
    """コマンドを実行する"""
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            return ExecutionResult(
                success=True,
                output=result.stdout,
                execution_time=execution_time
            )
        else:
            return ExecutionResult(
                success=False,
                output=result.stdout,
                error=result.stderr,
                execution_time=execution_time
            )
    
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=False,
            error=f"コマンドがタイムアウトしました ({timeout}秒)",
            execution_time=execution_time
        )
    
    except Exception as e:
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=False,
            error=f"コマンド実行中にエラーが発生しました: {str(e)}",
            execution_time=execution_time
        )


def check_file_exists(file_path: str) -> bool:
    """ファイルが存在するかチェック"""
    return os.path.exists(file_path)


def check_output_contains(output: str, pattern: str) -> bool:
    """出力に指定されたパターンが含まれているかチェック"""
    return pattern in output


def check_output_not_contains(output: str, pattern: str) -> bool:
    """出力に指定されたパターンが含まれていないかチェック"""
    return pattern not in output


def check_file_contains(file_path: str, pattern: str) -> bool:
    """ファイルの内容に指定されたパターンが含まれているかチェック"""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return pattern in content
    except Exception:
        return False


def check_website_exists(url: str, timeout: int = 10) -> bool:
    """Webサイトが存在するかチェック"""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def execute_test_command(command: str, timeout: int = 60) -> bool:
    """テストコマンドを実行し、成功したかチェック"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def check_claude_code_confirmation(prompt: str, timeout: int = 120) -> bool:
    """Claude Codeで確認し、OKが出るかチェック"""
    try:
        # Claude Codeを実行してプロンプトを送信
        command = f'claude code "{prompt}"'
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        # 出力に"OK"が含まれているかチェック
        if result.returncode == 0 and "OK" in result.stdout:
            return True
        else:
            return False
            
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def check_condition(condition: Dict[str, Any], task: Task) -> bool:
    """完了条件をチェックする"""
    condition_type = condition.get('type')
    
    if condition_type == 'file_exists':
        return check_file_exists(condition['path'])
    
    elif condition_type == 'output_contains':
        if task.last_output is None:
            return False
        return check_output_contains(task.last_output, condition['pattern'])
    
    elif condition_type == 'output_not_contains':
        if task.last_output is None:
            return True  # 出力がない場合は条件を満たすとみなす
        return check_output_not_contains(task.last_output, condition['pattern'])
    
    elif condition_type == 'file_contains':
        return check_file_contains(condition['path'], condition['pattern'])
    
    elif condition_type == 'website_exists':
        url = condition.get('url')
        timeout = condition.get('timeout', 10)
        if not url:
            print("警告: website_exists条件にURLが指定されていません")
            return False
        return check_website_exists(url, timeout)
    
    elif condition_type == 'test_command':
        command = condition.get('command')
        timeout = condition.get('timeout', 60)
        if not command:
            print("警告: test_command条件にコマンドが指定されていません")
            return False
        return execute_test_command(command, timeout)
    
    elif condition_type == 'claude_code_confirmation':
        prompt = condition.get('prompt')
        timeout = condition.get('timeout', 120)
        if not prompt:
            print("警告: claude_code_confirmation条件にプロンプトが指定されていません")
            return False
        return check_claude_code_confirmation(prompt, timeout)
    
    else:
        print(f"警告: 未知の条件タイプ '{condition_type}' をスキップします")
        return False


def check_all_conditions(task: Task) -> bool:
    """すべての完了条件をチェックする"""
    for condition in task.completion_conditions:
        if not check_condition(condition, task):
            return False
    return True


def should_apply_cool_down(task: Task) -> bool:
    """クールタイムを適用すべきか判断する"""
    if task.retry_count == 0 or task.last_error is None:
        return False
    
    # 直前のエラーと同じエラーの場合はクールタイムを適用
    # 簡易的な実装：エラーメッセージの先頭50文字を比較
    current_error_hash = hash(task.last_error[:50])
    # 実際の実装では、過去のエラー履歴を保持する必要がある
    return True


def apply_cool_down(seconds: int = 60) -> None:
    """クールタイムを適用する"""
    print(f"クールタイム中です... {seconds}秒待機します")
    for remaining in range(seconds, 0, -1):
        print(f"残り時間: {remaining}秒", end='\r')
        time.sleep(1)
    print()


def generate_command_from_description(description: str, timeout: int = 60) -> str:
    """自然言語のタスク説明からClaude Codeコマンドを生成する"""
    prompt = f"""
以下の自然言語タスク説明を、実行可能なClaude Codeコマンドに変換してください。

タスク説明: {description}

要件:
1. 実行可能なコマンドを生成してください
2. 出力結果がわかるようにしてください
3. エラー処理を含めてください
4. コマンドは一行で記述してください

生成したコマンドだけを返してください:
"""
    
    try:
        result = subprocess.run(
            ['claude', 'code', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Claude Codeの出力からコマンドを抽出
            lines = result.stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('生成したコマンド'):
                    return line
            return result.stdout.strip()
        else:
            raise Exception(f"Claude Codeの実行に失敗: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise Exception("Claude Codeの実行がタイムアウトしました")
    except Exception as e:
        raise Exception(f"Claude Codeの実行中にエラーが発生しました: {str(e)}")


def generate_completion_conditions(description: str, command: str, timeout: int = 60) -> List[Dict[str, Any]]:
    """タスク完了条件を動的に生成する"""
    prompt = f"""
以下のタスク情報から、適切な完了条件をJSON形式で生成してください。

タスク説明: {description}
生成されたコマンド: {command}

完了条件の種類:
- output_contains: 出力に特定のパターンが含まれる
- file_exists: 特定のファイルが存在する
- file_contains: ファイルに特定のパターンが含まれる
- website_exists: Webサイトにアクセスできる
- claude_code_confirmation: Claude Codeで確認できる

要件:
1. タスクが完了したことを確認できる条件を2-3個生成してください
2. JSON形式で返してください
3. 各条件にはtypeと必要なパラメータを含めてください

JSON形式で返してください:
"""
    
    try:
        result = subprocess.run(
            ['claude', 'code', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Claude Codeの出力からJSONを抽出
            import json
            lines = result.stdout.strip().split('\n')
            json_start = -1
            json_end = -1
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('{'):
                    json_start = i
                    break
            
            if json_start >= 0:
                # JSONの終わりを見つける
                bracket_count = 0
                for i in range(json_start, len(lines)):
                    line = lines[i]
                    bracket_count += line.count('{') - line.count('}')
                    if bracket_count == 0:
                        json_end = i
                        break
                
                if json_end >= 0:
                    json_str = '\n'.join(lines[json_start:json_end+1])
                    try:
                        conditions = json.loads(json_str)
                        if isinstance(conditions, list):
                            return conditions
                    except json.JSONDecodeError:
                        pass
            
            # デフォルトの条件を返す
            return [
                {
                    "type": "output_contains",
                    "pattern": "完了"
                }
            ]
        else:
            # デフォルトの条件を返す
            return [
                {
                    "type": "output_contains",
                    "pattern": "完了"
                }
            ]
            
    except subprocess.TimeoutExpired:
        # デフォルトの条件を返す
        return [
            {
                "type": "output_contains",
                "pattern": "完了"
            }
        ]
    except Exception:
        # デフォルトの条件を返す
        return [
            {
                "type": "output_contains",
                "pattern": "完了"
            }
        ]


def analyze_failure_and_improve(task: NaturalLanguageTask, timeout: int = 60) -> str:
    """タスク失敗の原因を分析し、改善されたコマンドを生成する"""
    prompt = f"""
以下のタスクが失敗しました。原因を分析し、改善されたコマンドを生成してください。

タスクID: {task.id}
タスク名: {task.name}
タスク説明: {task.description}
生成されたコマンド: {task.generated_command}
最後の出力: {task.last_output}
最後のエラー: {task.last_error}

要件:
1. 失敗の原因を分析してください
2. 改善されたコマンドを生成してください
3. エラーを回避するための対策を含めてください
4. コマンドは一行で記述してください

改善されたコマンドだけを返してください:
"""
    
    try:
        result = subprocess.run(
            ['claude', 'code', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Claude Codeの出力からコマンドを抽出
            lines = result.stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('改善されたコマンド'):
                    return line
            return result.stdout.strip()
        else:
            raise Exception(f"Claude Codeの実行に失敗: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise Exception("Claude Codeの実行がタイムアウトしました")
    except Exception as e:
        raise Exception(f"Claude Codeの実行中にエラーが発生しました: {str(e)}")


def create_subtask_for_improvement(main_task: NaturalLanguageTask, improvement_description: str, timeout: int = 60) -> NaturalLanguageTask:
    """改善のためのサブタスクを作成する"""
    subtask_id = f"{main_task.id}_sub_{main_task.retry_count + 1}"
    
    prompt = f"""
以下の改善タスクから、実行可能なサブタスクを生成してください。

メインタスク: {main_task.name}
改善内容: {improvement_description}

要件:
1. 具体的な実行コマンドを生成してください
2. 適切な完了条件を設定してください
3. サブタスクの目的を明確にしてください

サブタスク情報をJSON形式で返してください:
"""
    
    try:
        result = subprocess.run(
            ['claude', 'code', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Claude Codeの出力からJSONを抽出
            import json
            lines = result.stdout.strip().split('\n')
            json_start = -1
            json_end = -1
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('{'):
                    json_start = i
                    break
            
            if json_start >= 0:
                # JSONの終わりを見つける
                bracket_count = 0
                for i in range(json_start, len(lines)):
                    line = lines[i]
                    bracket_count += line.count('{') - line.count('}')
                    if bracket_count == 0:
                        json_end = i
                        break
                
                if json_end >= 0:
                    json_str = '\n'.join(lines[json_start:json_end+1])
                    try:
                        subtask_data = json.loads(json_str)
                        if isinstance(subtask_data, dict):
                            subtask = NaturalLanguageTask(
                                id=subtask_id,
                                name=subtask_data.get('name', f'サブタスク{main_task.retry_count + 1}'),
                                description=subtask_data.get('description', improvement_description),
                                max_retries=2,
                                timeout=120
                            )
                            subtask.generated_command = subtask_data.get('command', '')
                            subtask.generated_conditions = subtask_data.get('completion_conditions', [
                                {"type": "output_contains", "pattern": "成功"}
                            ])
                            return subtask
                    except json.JSONDecodeError:
                        pass
            
            # デフォルトのサブタスクを返す
            return NaturalLanguageTask(
                id=subtask_id,
                name=f'改善サブタスク{main_task.retry_count + 1}',
                description=improvement_description,
                max_retries=2,
                timeout=120,
                generated_command=f"echo '改善処理を実行します: {improvement_description}'",
                generated_conditions=[
                    {"type": "output_contains", "pattern": "成功"}
                ]
            )
        else:
            # デフォルトのサブタスクを返す
            return NaturalLanguageTask(
                id=subtask_id,
                name=f'改善サブタスク{main_task.retry_count + 1}',
                description=improvement_description,
                max_retries=2,
                timeout=120,
                generated_command=f"echo '改善処理を実行します: {improvement_description}'",
                generated_conditions=[
                    {"type": "output_contains", "pattern": "成功"}
                ]
            )
            
    except subprocess.TimeoutExpired:
        # デフォルトのサブタスクを返す
        return NaturalLanguageTask(
            id=subtask_id,
            name=f'改善サブタスク{main_task.retry_count + 1}',
            description=improvement_description,
            max_retries=2,
            timeout=120,
            generated_command=f"echo '改善処理を実行します: {improvement_description}'",
            generated_conditions=[
                {"type": "output_contains", "pattern": "成功"}
            ]
        )
    except Exception:
        # デフォルトのサブタスクを返す
        return NaturalLanguageTask(
            id=subtask_id,
            name=f'改善サブタスク{main_task.retry_count + 1}',
            description=improvement_description,
            max_retries=2,
            timeout=120,
            generated_command=f"echo '改善処理を実行します: {improvement_description}'",
            generated_conditions=[
                {"type": "output_contains", "pattern": "成功"}
            ]
        )