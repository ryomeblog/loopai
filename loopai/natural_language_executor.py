"""
自然言語タスク実行機能
"""
import time
from typing import List, Optional, Dict, Any
from .utils import NaturalLanguageTask, ExecutionResult, execute_command, should_apply_cool_down, apply_cool_down


class NaturalLanguageTaskExecutor:
    """自然言語タスク実行クラス"""
    
    def __init__(self):
        self.running_tasks = {}
    
    def execute_natural_language_task(self, task: NaturalLanguageTask) -> bool:
        """自然言語タスクを実行する"""
        print(f"\n=== 自然言語タスク実行開始: {task.name} ({task.id}) ===")
        print(f"タスク説明: {task.description}")
        
        # 最初のコマンド生成
        if task.generated_command is None:
            print("🤖 Claude Codeがタスクを解釈してコマンドを生成します...")
            try:
                task.generated_command = self._generate_initial_command(task)
                print(f"生成されたコマンド: {task.generated_command}")
            except Exception as e:
                print(f"❌ コマンド生成に失敗しました: {e}")
                task.last_error = str(e)
                return False
        
        # 完了条件の生成
        if task.generated_conditions is None:
            print("🎯 Claude Codeが完了条件を生成します...")
            try:
                task.generated_conditions = self._generate_initial_conditions(task)
                print(f"生成された完了条件: {len(task.generated_conditions)}個")
            except Exception as e:
                print(f"⚠️ 完了条件の生成に失敗しました: {e}")
                task.generated_conditions = [{"type": "output_contains", "pattern": "完了"}]
        
        # クールタイムの適用をチェック
        if should_apply_cool_down(task):
            apply_cool_down()
        
        # タスク実行
        result = execute_command(task.generated_command, task.timeout)
        
        # 実行結果を保存
        task.last_output = result.output
        task.last_error = result.error
        task.retry_count += 1
        
        # 実行結果の表示
        if result.success:
            print(f"✅ タスク実行成功 (実行時間: {result.execution_time:.2f}秒)")
            if result.output:
                print("出力:")
                print(result.output)
        else:
            print(f"❌ タスク実行失敗 (実行時間: {result.execution_time:.2f}秒)")
            if result.error:
                print("エラー:")
                print(result.error)
        
        return result.success
    
    def execute_natural_language_task_until_completion(self, task: NaturalLanguageTask) -> bool:
        """完了条件を満たすまで自然言語タスクを実行し続ける"""
        max_attempts = task.max_retries
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n--- 尝試 {attempt}/{max_attempts} ---")
            
            # タスク実行
            success = self.execute_natural_language_task(task)
            
            # 完了条件チェック
            if self._check_completion_conditions(task):
                print(f"\n🎉 タスク '{task.name}' は完了条件を満たしました！")
                return True
            
            # 成功したが完了条件を満たさない場合 - 自律的改善
            if success:
                print(f"タスクは成功しましたが、完了条件を満たしていません")
                print("🤖 Claude Codeが改善策を検討します...")
                
                # 改善のためのサブタスクを実行
                if self._execute_improvement_subtasks(task):
                    print("改善処理が完了しました。再試行します...")
                    time.sleep(5)  # 改善後の短い待機
                    continue
            
            # 失敗した場合 - 原因分析と改善
            if not success:
                print(f"タスクが失敗しました。原因を分析します...")
                print("🤖 Claude Codeが失敗原因を分析します...")
                
                # 原因分析と改善
                if self._analyze_and_improve(task):
                    print("改善策が見つかりました。再試行します...")
                    time.sleep(5)  # 改善後の短い待機
                    continue
            
            # 最大試行回数に達した場合
            if attempt < max_attempts:
                print(f"タスクが失敗しました。{max_attempts - attempt} 回の再試行が残っています")
                if should_apply_cool_down(task):
                    apply_cool_down()
                else:
                    print("しばらく待機して再試行します...")
                    time.sleep(30)  # 失敗時は長い待機
        
        print(f"\n❌ タスク '{task.name}' は最大試行回数に達しました。完了条件を満たせませんでした。")
        return False
    
    def _generate_initial_command(self, task: NaturalLanguageTask) -> str:
        """最初のコマンドを生成する"""
        from .utils import generate_command_from_description
        return generate_command_from_description(task.description, task.timeout)
    
    def _generate_initial_conditions(self, task: NaturalLanguageTask) -> List[Dict[str, Any]]:
        """最初の完了条件を生成する"""
        from .utils import generate_completion_conditions
        if task.generated_command:
            return generate_completion_conditions(task.description, task.generated_command, task.timeout)
        else:
            return [{"type": "output_contains", "pattern": "完了"}]
    
    def _check_completion_conditions(self, task: NaturalLanguageTask) -> bool:
        """完了条件をチェックする"""
        if not task.generated_conditions:
            return False
        
        print("\n--- 完了条件チェック ---")
        all_conditions_met = True
        
        for i, condition in enumerate(task.generated_conditions):
            condition_type = condition.get('type')
            condition_met = self._check_single_condition(condition, task)
            status = "✅" if condition_met else "❌"
            print(f"  {status} 条件 {i+1} ({condition_type}): {condition}")
            if not condition_met:
                all_conditions_met = False
        
        return all_conditions_met
    
    def _check_single_condition(self, condition: dict, task: NaturalLanguageTask) -> bool:
        """単一の完了条件をチェックする"""
        from .utils import check_condition
        # NaturalLanguageTaskをTaskに変換してチェック
        temp_task = task
        return check_condition(condition, temp_task)
    
    def _execute_improvement_subtasks(self, task: NaturalLanguageTask) -> bool:
        """改善のためのサブタスクを実行する"""
        if not task.subtasks:
            # サブタスクがなければ生成
            improvement_prompt = "このタスクの完了条件を満たすために、どのような改善を行うべきか分析してください"
            subtask = self._create_improvement_subtask(task, improvement_prompt)
            task.subtasks = [subtask]
        
        # サブタスクを実行
        for subtask in task.subtasks:
            print(f"  📋 サブタスク実行: {subtask.name}")
            subtask_success = self.execute_natural_language_task(subtask)
            if not subtask_success:
                print(f"  ❌ サブタスク '{subtask.name}' が失敗しました")
                return False
        
        print(f"  ✅ すべてのサブタスクが成功しました")
        return True
    
    def _analyze_and_improve(self, task: NaturalLanguageTask) -> bool:
        """失敗原因を分析し、改善する"""
        try:
            from .utils import analyze_failure_and_improve, create_subtask_for_improvement
            
            # 失敗原因の分析と改善コマンドの生成
            improved_command = analyze_failure_and_improve(task, task.timeout)
            print(f"  📝 改善されたコマンド: {improved_command}")
            
            # 改善のためのサブタスクを作成
            improvement_description = "タスク失敗の原因を分析し、改善策を実行する"
            subtask = create_subtask_for_improvement(task, improvement_description, task.timeout)
            subtask.generated_command = improved_command
            
            # サブタスクを実行
            print(f"  📋 改善サブタスク実行: {subtask.name}")
            subtask_success = self.execute_natural_language_task(subtask)
            
            if subtask_success:
                # 改善されたコマンドをメインタスクに適用
                task.generated_command = improved_command
                print(f"  ✅ 改善が成功しました。コマンドを更新しました")
                return True
            else:
                print(f"  ❌ 改善サブタスクが失敗しました")
                return False
                
        except Exception as e:
            print(f"  ❌ 改善処理中にエラーが発生しました: {e}")
            return False
    
    def _create_improvement_subtask(self, main_task: NaturalLanguageTask, improvement_description: str) -> 'NaturalLanguageTask':
        """改善のためのサブタスクを作成する"""
        from .utils import create_subtask_for_improvement
        return create_subtask_for_improvement(main_task, improvement_description, main_task.timeout)
    
    def execute_natural_language_tasks(self, tasks: List[NaturalLanguageTask]) -> dict:
        """複数の自然言語タスクを実行する"""
        results = {}
        
        for task in tasks:
            print(f"\n{'='*50}")
            print(f"自然言語タスク {task.id}: {task.name}")
            print(f"{'='*50}")
            
            success = self.execute_natural_language_task_until_completion(task)
            results[task.id] = {
                'success': success,
                'task': task
            }
        
        return results
    
    def get_natural_language_task_summary(self, results: dict) -> str:
        """自然言語タスク実行結果のサマリーを生成する"""
        total_tasks = len(results)
        successful_tasks = sum(1 for result in results.values() if result['success'])
        
        summary = f"\n{'='*50}"
        summary += f"\n自然言語タスク実行サマリー"
        summary += f"\n{'='*50}"
        summary += f"\n総タスク数: {total_tasks}"
        summary += f"\n成功タスク数: {successful_tasks}"
        summary += f"\n失敗タスク数: {total_tasks - successful_tasks}"
        summary += f"\n成功率: {successful_tasks/total_tasks*100:.1f}%"
        
        summary += f"\n\n詳細結果:"
        for task_id, result in results.items():
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            task = result['task']
            summary += f"\n  {task_id}: {task.name} - {status}"
            if task.retry_count > 0:
                summary += f" (再試行: {task.retry_count}回)"
            if task.subtasks and len(task.subtasks) > 0:
                summary += f" (サブタスク: {len(task.subtasks)}個)"
        
        return summary