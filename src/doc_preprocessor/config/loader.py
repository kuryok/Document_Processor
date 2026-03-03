from typing import List, Optional
from pydantic import BaseModel
import yaml
from pathlib import Path

class HardwareConfig(BaseModel):
    device: str = "cuda"
    gpu_memory_gb: int = 8
    ram_gb: int = 16

class RenderingConfig(BaseModel):
    dpi_default: int = 200
    dpi_high: int = 300

class OcrConfig(BaseModel):
    backend: str = "paddleocr"
    lang: List[str] = ["pt", "en"]
    use_gpu: bool = True
    batch_size: int = 4

class OcrVlConfig(BaseModel):
    backend: str = "paddleocr_vl"
    use_gpu: bool = True
    batch_size: int = 1

class LayoutConfig(BaseModel):
    backend: str = "docling"
    use_gpu: bool = True

class ParallelismConfig(BaseModel):
    parallel_pages: int = 2
    page_queue_size: int = 10

class CacheConfig(BaseModel):
    enabled: bool = True
    dir: str = "preprocess/cache"
    backend: str = "sqlite"

class ThresholdsConfig(BaseModel):
    native_min_chars: int = 30
    native_min_coverage: float = 0.01
    ocr_confidence_threshold: float = 0.75
    ocr_vl_escalation_confidence: float = 0.75
    complex_layout_column_threshold: int = 2
    min_image_area_px2: int = 50000

class LimitsConfig(BaseModel):
    max_pages_per_doc: int = 500
    max_render_memory_mb: int = 512

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    file: str = "preprocess/logs/pipeline.jsonl"

class Config(BaseModel):
    hardware: HardwareConfig = HardwareConfig()
    rendering: RenderingConfig = RenderingConfig()
    ocr: OcrConfig = OcrConfig()
    ocr_vl: OcrVlConfig = OcrVlConfig()
    layout: LayoutConfig = LayoutConfig()
    parallelism: ParallelismConfig = ParallelismConfig()
    cache: CacheConfig = CacheConfig()
    thresholds: ThresholdsConfig = ThresholdsConfig()
    limits: LimitsConfig = LimitsConfig()
    logging: LoggingConfig = LoggingConfig()

def load_config(path: str) -> Config:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    if not data:
        data = {}
        
    return Config(**data)

def get_default_config() -> Config:
    # Look for config/default.yaml relative to project root
    # Note: in a real package this might be bundled or user-provided
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    default_path = root_dir / "config" / "default.yaml"
    if default_path.exists():
        return load_config(str(default_path))
    return Config()
