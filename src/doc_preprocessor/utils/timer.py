import time

class Timer:
    """Context manager for timing execution blocks."""
    def __init__(self, name: str):
        self.name = name
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time
        
    @property
    def elapsed_ms(self) -> float:
        return self.elapsed * 1000.0
