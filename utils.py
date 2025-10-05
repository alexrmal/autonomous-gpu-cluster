"""
Utility functions and logging for the GPU Mini-Cluster Orchestrator
"""
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging with colored console output and optional file output"""
    
    # Create logger
    logger = logging.getLogger("orchestrator")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def generate_job_id(job_type: str = "compute", priority: str = "normal") -> str:
    """Generate a realistic job ID with descriptive naming"""
    import random
    
    # Job type prefixes
    type_prefixes = {
        "sleep": ["io", "wait", "idle", "pause", "delay"],
        "compute": ["calc", "process", "analyze", "compute", "run"],
        "matrix": ["matrix", "gpu", "tensor", "linear", "algebra"],
        "fault_injection": ["test", "check", "verify", "validate", "inject"]
    }
    
    # Priority suffixes
    priority_suffixes = {
        "low": ["batch", "background", "low-priority"],
        "normal": ["standard", "regular", "normal"],
        "high": ["urgent", "priority", "important"],
        "critical": ["critical", "emergency", "immediate"]
    }
    
    # Get random prefix and suffix
    prefix = random.choice(type_prefixes.get(job_type, ["job"]))
    suffix = random.choice(priority_suffixes.get(priority.lower(), ["normal"]))
    
    # Add a random number for uniqueness
    number = random.randint(1000, 9999)
    
    # Create realistic job name
    if job_type == "matrix":
        return f"gpu-{prefix}-{number}"
    elif job_type == "fault_injection":
        return f"{prefix}-test-{number}"
    else:
        return f"{prefix}-{suffix}-{number}"


def generate_worker_id() -> str:
    """Generate a unique worker ID"""
    return f"worker_{uuid.uuid4().hex[:8]}"


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_percentage(value: float) -> str:
    """Format percentage with color coding"""
    if value >= 0.9:
        color = Fore.RED
    elif value >= 0.7:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN
    
    return f"{color}{value:.1%}{Style.RESET_ALL}"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"{Fore.CYAN}{self.operation_name} completed in {format_duration(duration)}{Style.RESET_ALL}")


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with default"""
    return dictionary.get(key, default)


def validate_port(port: int) -> bool:
    """Validate port number"""
    return 1 <= port <= 65535


def validate_hostname(hostname: str) -> bool:
    """Basic hostname validation"""
    return len(hostname) > 0 and len(hostname) <= 255


# Global logger instance
logger = setup_logging()
