import threading

class GPUResourceManager:
    """Manages GPU resource limits across threads for VLM or large models."""
    def __init__(self, max_concurrent: int = 1):
        self.semaphore = threading.Semaphore(max_concurrent)
        
    def acquire(self):
        self.semaphore.acquire()
        
    def release(self):
        self.semaphore.release()
        
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# Global instances for heavy backends if needed
vl_gpu_lock = GPUResourceManager(max_concurrent=1)
