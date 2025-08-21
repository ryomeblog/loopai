"""
タスク実行機能
"""
import time
from typing import List, Optional
from .utils import Task, ExecutionResult, execute_command, should_apply_cool_down, apply_cool_down


class TaskExecutor:
    """タスク実行クラス"""
    
    def __init__(self):
        self.running_tasks = {}
    
    def execute_task(self, task: Task) -> bool:
        """タスクを実行する"""
        print(f"\n=== タスク実行開始: {task.name} ({task.id}) ===")
        print(f"コマンド: {task.command}")
        
        # クールタイムの適用をチェック
        if should_apply_cool_down(task):
            apply_cool_down()
        
        # タスク実行
        result = execute_command(task.command, task.timeout)
        
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
    
    def execute_task_until_completion(self, task: Task) -> bool:
        """完了条件を満たすまでタスクを実行し続ける"""
        max_attempts = task.max_retries
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n--- 尝試 {attempt}/{max_attempts} ---")
            
            # タスク実行
            success = self.execute_task(task)
            
            # 完了条件チェック
            if self._check_completion_conditions(task):
                print(f"\n🎉 タスク '{task.name}' は完了条件を満たしました！")
                return True
            
            # 成功したが完了条件を満たさない場合
            if success:
                print(f"タスクは成功しましたが、完了条件を満たしていません")
                if attempt < max_attempts:
                    print("しばらく待機して再試行します...")
                    time.sleep(10)  # 成功時は短い待機
                continue
            
            # 失敗した場合
            if attempt < max_attempts:
                print(f"タスクが失敗しました。{max_attempts - attempt} 回の再試行が残っています")
                if should_apply_cool_down(task):
                    apply_cool_down()
                else:
                    print("しばらく待機して再試行します...")
                    time.sleep(30)  # 失敗時は長い待機
        
        print(f"\n❌ タスク '{task.name}' は最大試行回数に達しました。完了条件を満たせませんでした。")
        return False
    
    def _check_completion_conditions(self, task: Task) -> bool:
        """完了条件をチェックする"""
        from .utils import check_all_conditions
        
        print("\n--- 完了条件チェック ---")
        all_conditions_met = check_all_conditions(task)
        
        if all_conditions_met:
            print("✅ すべての完了条件を満たしました")
        else:
            print("❌ 完了条件を満たしていません")
            # 各条件の詳細を表示
            for i, condition in enumerate(task.completion_conditions):
                condition_type = condition.get('type')
                condition_met = self._check_single_condition(condition, task)
                status = "✅" if condition_met else "❌"
                print(f"  {status} 条件 {i+1} ({condition_type}): {condition}")
        
        return all_conditions_met
    
    def _check_single_condition(self, condition: dict, task: Task) -> bool:
        """単一の完了条件をチェックする"""
        from .utils import check_condition
        return check_condition(condition, task)
    
    def execute_tasks(self, tasks: List[Task]) -> dict:
        """複数のタスクを実行する"""
        results = {}
        
        for task in tasks:
            print(f"\n{'='*50}")
            print(f"タスク {task.id}: {task.name}")
            print(f"{'='*50}")
            
            success = self.execute_task_until_completion(task)
            results[task.id] = {
                'success': success,
                'task': task
            }
        
        return results
    
    def get_task_summary(self, results: dict) -> str:
        """実行結果のサマリーを生成する"""
        total_tasks = len(results)
        successful_tasks = sum(1 for result in results.values() if result['success'])
        
        summary = f"\n{'='*50}"
        summary += f"\nタスク実行サマリー"
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
        
        return summary