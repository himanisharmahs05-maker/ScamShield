# backend/app/utils/timer.py
import time

class ExecutionTimer:
    """A precise stopwatch to measure backend execution speeds."""
    def __init__(self, block_name: str):
        self.block_name = block_name

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.execution_time = self.end_time - self.start_time
        print(f"[TIMER] [SPEED TEST] '{self.block_name}' took {self.execution_time:.4f} seconds")