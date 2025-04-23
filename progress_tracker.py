import time

class ProgressTracker:
    def __init__(self, total_steps):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self._last_update = 0
    
    def update(self, step_name):
        current_time = time.time()
        if current_time - self._last_update < 0.1:  # 限制更新频率
            return
            
        self.current_step += 1
        self._last_update = current_time
        elapsed_time = current_time - self.start_time
        
        if self.current_step > 0:
            estimated_total = elapsed_time / self.current_step * self.total_steps
            remaining_time = max(0, estimated_total - elapsed_time)
            
            print(f"\r进度: {self.current_step}/{self.total_steps} - {step_name} "
                  f"(预计剩余: {remaining_time:.1f}秒)", end="")
            
        if self.current_step >= self.total_steps:
            print("\n完成!")
