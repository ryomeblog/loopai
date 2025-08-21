"""
完了条件チェック機能
"""
import os
import time
from typing import Dict, List, Any, Optional
from .utils import Task, ExecutionResult


class ConditionChecker:
    """完了条件チェッククラス"""
    
    def __init__(self):
        self.condition_history = {}
    
    def check_conditions(self, task: Task) -> Dict[str, bool]:
        """タスクの完了条件をチェックする"""
        results = {}
        
        print(f"\n--- 完了条件チェック: {task.name} ---")
        
        for i, condition in enumerate(task.completion_conditions):
            condition_id = f"{task.id}_condition_{i}"
            condition_type = condition.get('type')
            condition_name = condition.get('name', f'条件 {i+1}')
            
            print(f"\nチェック中: {condition_name} ({condition_type})")
            
            result = self._check_single_condition(condition, task)
            results[condition_id] = result
            
            status = "✅ 満たしている" if result else "❌ 満たしていない"
            print(f"結果: {status}")
            
            # 詳細情報を表示
            if condition_type == 'file_exists':
                file_path = condition.get('path')
                exists = os.path.exists(file_path)
                print(f"  ファイルパス: {file_path}")
                print(f"  存在: {'あり' if exists else 'なし'}")
            
            elif condition_type in ['output_contains', 'output_not_contains']:
                pattern = condition.get('pattern')
                output = task.last_output or ""
                if condition_type == 'output_contains':
                    contains = pattern in output
                    print(f"  パターン: '{pattern}'")
                    print(f"  出力に含まれている: {'はい' if contains else 'いいえ'}")
                else:
                    not_contains = pattern not in output
                    print(f"  パターン: '{pattern}'")
                    print(f"  出力に含まれていない: {'はい' if not_contains else 'いいえ'}")
                
                # パターンが見つかる位置を表示
                if condition_type == 'output_contains' and pattern in output:
                    line_num = output.count('\n', 0, output.find(pattern)) + 1
                    print(f"  見つかった行: {line_num}")
            
            elif condition_type == 'file_contains':
                file_path = condition.get('path')
                pattern = condition.get('pattern')
                file_exists = os.path.exists(file_path)
                print(f"  ファイルパス: {file_path}")
                print(f"  パターン: '{pattern}'")
                
                if file_exists:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            contains = pattern in content
                            print(f"  ファイル存在: あり")
                            print(f"  パターン含まれている: {'はい' if contains else 'いいえ'}")
                            
                            if contains:
                                line_num = content.count('\n', 0, content.find(pattern)) + 1
                                print(f"  見つかった行: {line_num}")
                    except Exception as e:
                        print(f"  ファイル読み込みエラー: {e}")
                        results[condition_id] = False
                else:
                    print(f"  ファイル存在: なし")
                    results[condition_id] = False
            
            elif condition_type == 'website_exists':
                url = condition.get('url')
                timeout = condition.get('timeout', 10)
                print(f"  URL: {url}")
                print(f"  タイムアウト: {timeout}秒")
                
                try:
                    import requests
                    response = requests.get(url, timeout=timeout, allow_redirects=True)
                    status_code = response.status_code
                    print(f"  ステータスコード: {status_code}")
                    print(f"  結果: {'✅ アクセス成功' if status_code == 200 else '❌ アクセス失敗'}")
                    results[condition_id] = (status_code == 200)
                except Exception as e:
                    print(f"  エラー: {e}")
                    results[condition_id] = False
            
            elif condition_type == 'test_command':
                command = condition.get('command')
                timeout = condition.get('timeout', 60)
                print(f"  コマンド: {command}")
                print(f"  タイムアウト: {timeout}秒")
                
                try:
                    import subprocess
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        encoding='utf-8',
                        errors='replace'
                    )
                    print(f"  終了コード: {result.returncode}")
                    print(f"  結果: {'✅ 成功' if result.returncode == 0 else '❌ 失敗'}")
                    if result.stdout:
                        print(f"  標準出力: {result.stdout.strip()}")
                    if result.stderr:
                        print(f"  標準エラー: {result.stderr.strip()}")
                    results[condition_id] = (result.returncode == 0)
                except subprocess.TimeoutExpired:
                    print(f"  結果: ❌ タイムアウト")
                    results[condition_id] = False
                except Exception as e:
                    print(f"  エラー: {e}")
                    results[condition_id] = False
            
            elif condition_type == 'claude_code_confirmation':
                prompt = condition.get('prompt')
                timeout = condition.get('timeout', 120)
                print(f"  プロンプト: '{prompt}'")
                print(f"  タイムアウト: {timeout}秒")
                
                try:
                    import subprocess
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
                    print(f"  終了コード: {result.returncode}")
                    print(f"  標準出力: {result.stdout.strip()}")
                    if result.stderr:
                        print(f"  標準エラー: {result.stderr.strip()}")
                    
                    if result.returncode == 0 and "OK" in result.stdout:
                        print(f"  結果: ✅ Claude CodeがOKを返しました")
                        results[condition_id] = True
                    else:
                        print(f"  結果: ❌ Claude CodeがOKを返しませんでした")
                        results[condition_id] = False
                except subprocess.TimeoutExpired:
                    print(f"  結果: ❌ タイムアウト")
                    results[condition_id] = False
                except Exception as e:
                    print(f"  エラー: {e}")
                    results[condition_id] = False
        
        return results
    
    def _check_single_condition(self, condition: Dict[str, Any], task: Task) -> bool:
        """単一の完了条件をチェックする"""
        condition_type = condition.get('type')
        
        if condition_type == 'file_exists':
            return self._check_file_exists(condition['path'])
        
        elif condition_type == 'output_contains':
            return self._check_output_contains(task.last_output or "", condition['pattern'])
        
        elif condition_type == 'output_not_contains':
            return self._check_output_not_contains(task.last_output or "", condition['pattern'])
        
        elif condition_type == 'file_contains':
            return self._check_file_contains(condition['path'], condition['pattern'])
        
        elif condition_type == 'website_exists':
            return self._check_website_exists(condition['url'], condition.get('timeout', 10))
        
        elif condition_type == 'test_command':
            return self._check_test_command(condition['command'], condition.get('timeout', 60))
        
        elif condition_type == 'claude_code_confirmation':
            return self._check_claude_code_confirmation(condition['prompt'], condition.get('timeout', 120))
        
        else:
            print(f"警告: 未知の条件タイプ '{condition_type}' をスキップします")
            return False
    
    def _check_file_exists(self, file_path: str) -> bool:
        """ファイルが存在するかチェック"""
        exists = os.path.exists(file_path)
        self._log_condition_check('file_exists', file_path, exists)
        return exists
    
    def _check_output_contains(self, output: str, pattern: str) -> bool:
        """出力に指定されたパターンが含まれているかチェック"""
        contains = pattern in output
        self._log_condition_check('output_contains', pattern, contains, output_length=len(output))
        return contains
    
    def _check_output_not_contains(self, output: str, pattern: str) -> bool:
        """出力に指定されたパターンが含まれていないかチェック"""
        not_contains = pattern not in output
        self._log_condition_check('output_not_contains', pattern, not_contains, output_length=len(output))
        return not_contains
    
    def _check_file_contains(self, file_path: str, pattern: str) -> bool:
        """ファイルの内容に指定されたパターンが含まれているかチェック"""
        if not os.path.exists(file_path):
            self._log_condition_check('file_contains', f"{file_path}:{pattern}", False, reason="ファイル不存在")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                contains = pattern in content
                self._log_condition_check('file_contains', f"{file_path}:{pattern}", contains,
                                        file_size=len(content))
                return contains
        except Exception as e:
            self._log_condition_check('file_contains', f"{file_path}:{pattern}", False, reason=str(e))
            return False
    
    def _check_website_exists(self, url: str, timeout: int = 10) -> bool:
        """Webサイトが存在するかチェック"""
        try:
            import requests
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            result = response.status_code == 200
            self._log_condition_check('website_exists', url, result, status_code=response.status_code)
            return result
        except Exception as e:
            self._log_condition_check('website_exists', url, False, reason=str(e))
            return False
    
    def _check_test_command(self, command: str, timeout: int = 60) -> bool:
        """テストコマンドを実行し、成功したかチェック"""
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            success = result.returncode == 0
            self._log_condition_check('test_command', command, success,
                                      return_code=result.returncode, output_length=len(result.stdout))
            return success
        except subprocess.TimeoutExpired:
            self._log_condition_check('test_command', command, False, reason="タイムアウト")
            return False
        except Exception as e:
            self._log_condition_check('test_command', command, False, reason=str(e))
            return False
    
    def _check_claude_code_confirmation(self, prompt: str, timeout: int = 120) -> bool:
        """Claude Codeで確認し、OKが出るかチェック"""
        try:
            import subprocess
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
            
            success = result.returncode == 0 and "OK" in result.stdout
            self._log_condition_check('claude_code_confirmation', prompt, success,
                                      return_code=result.returncode, output_length=len(result.stdout))
            return success
            
        except subprocess.TimeoutExpired:
            self._log_condition_check('claude_code_confirmation', prompt, False, reason="タイムアウト")
            return False
        except Exception as e:
            self._log_condition_check('claude_code_confirmation', prompt, False, reason=str(e))
            return False
    
    def _log_condition_check(self, condition_type: str, identifier: str, result: bool, **kwargs):
        """条件チェックのログを記録する"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'type': condition_type,
            'identifier': identifier,
            'result': result,
            **kwargs
        }
        
        if condition_type not in self.condition_history:
            self.condition_history[condition_type] = []
        
        self.condition_history[condition_type].append(log_entry)
    
    def get_condition_summary(self, task: Task) -> str:
        """条件チェックのサマリーを生成する"""
        results = self.check_conditions(task)
        
        total_conditions = len(results)
        met_conditions = sum(1 for result in results.values() if result)
        
        summary = f"\n{'='*50}"
        summary += f"\n完了条件サマリー: {task.name}"
        summary += f"\n{'='*50}"
        summary += f"\n総条件数: {total_conditions}"
        summary += f"\n満たした条件数: {met_conditions}"
        summary += f"\n満たしていない条件数: {total_conditions - met_conditions}"
        
        if total_conditions > 0:
            summary += f"\n充足率: {met_conditions/total_conditions*100:.1f}%"
        
        summary += f"\n\n詳細:"
        for condition_id, result in results.items():
            status = "✅" if result else "❌"
            summary += f"\n  {status} {condition_id}"
        
        return summary
    
    def export_condition_history(self, file_path: str) -> None:
        """条件チェック履歴をエクスポートする"""
        import json
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.condition_history, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"条件チェック履歴を {file_path} にエクスポートしました")