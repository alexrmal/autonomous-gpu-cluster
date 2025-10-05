"""
Job types and execution logic for the GPU Mini-Cluster Orchestrator
"""
import time
import random
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Callable
from datetime import datetime


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority enumeration"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Job:
    """Job data structure"""
    job_id: str
    job_type: str
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    parameters: Dict[str, Any] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'worker_id': self.worker_id,
            'parameters': self.parameters,
            'result': self.result,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'duration': self.duration
        }


class JobExecutor(ABC):
    """Abstract base class for job executors"""
    
    @abstractmethod
    def execute(self, job: Job) -> Any:
        """Execute a job and return the result"""
        pass
    
    @abstractmethod
    def can_execute(self, job: Job) -> bool:
        """Check if this executor can handle the given job"""
        pass


class SleepJobExecutor(JobExecutor):
    """Executor for sleep-based jobs (simulating GPU work)"""
    
    def execute(self, job: Job) -> Any:
        """Execute sleep job"""
        duration = job.parameters.get('duration', 5)
        time.sleep(duration)
        return f"Sleep job completed after {duration} seconds"
    
    def can_execute(self, job: Job) -> bool:
        """Check if this is a sleep job"""
        return job.job_type == "sleep"


class ComputeJobExecutor(JobExecutor):
    """Executor for compute-intensive jobs (simulating GPU computation)"""
    
    def execute(self, job: Job) -> Any:
        """Execute compute job"""
        iterations = job.parameters.get('iterations', 1000000)
        result = 0
        
        # Simulate GPU computation
        for i in range(iterations):
            result += i * random.random()
        
        return f"Compute job completed: {result:.2f}"
    
    def can_execute(self, job: Job) -> bool:
        """Check if this is a compute job"""
        return job.job_type == "compute"


class MatrixJobExecutor(JobExecutor):
    """Executor for matrix operations (simulating GPU matrix computations)"""
    
    def execute(self, job: Job) -> Any:
        """Execute matrix job"""
        size = job.parameters.get('matrix_size', 1000)
        
        # Try to use numpy for matrix multiplication
        try:
            import numpy as np
            # Create random matrices
            a = np.random.rand(size, size)
            b = np.random.rand(size, size)
            # Perform matrix multiplication
            result = np.dot(a, b)
            return f"Matrix multiplication completed: {result.shape}"
        except (ImportError, OSError, RuntimeError) as e:
            # Fallback simulation if numpy fails for any reason
            # Simulate matrix multiplication with nested loops
            result = 0
            iterations = min(size, 100)  # Limit iterations for performance
            for i in range(iterations):
                for j in range(iterations):
                    result += (i * j) % 1000  # Simulate computation
            
            # Simulate processing time
            time.sleep(0.1)
            
            return f"Matrix simulation completed (fallback): {result} (size: {iterations}x{iterations})"
    
    def can_execute(self, job: Job) -> bool:
        """Check if this is a matrix job"""
        return job.job_type == "matrix"


class FaultInjectionJobExecutor(JobExecutor):
    """Executor that can simulate failures for testing"""
    
    def execute(self, job: Job) -> Any:
        """Execute job with potential failure injection"""
        failure_rate = job.parameters.get('failure_rate', 0.1)
        
        if random.random() < failure_rate:
            raise Exception(f"Simulated failure in job {job.job_id}")
        
        duration = job.parameters.get('duration', 3)
        time.sleep(duration)
        return f"Fault injection job completed after {duration} seconds"
    
    def can_execute(self, job: Job) -> bool:
        """Check if this is a fault injection job"""
        return job.job_type == "fault_injection"


class JobExecutorRegistry:
    """Registry for job executors"""
    
    def __init__(self):
        self._executors = []
        self._register_default_executors()
    
    def _register_default_executors(self):
        """Register default job executors"""
        self.register(SleepJobExecutor())
        self.register(ComputeJobExecutor())
        self.register(MatrixJobExecutor())
        self.register(FaultInjectionJobExecutor())
    
    def register(self, executor: JobExecutor):
        """Register a job executor"""
        self._executors.append(executor)
    
    def get_executor(self, job: Job) -> Optional[JobExecutor]:
        """Get executor for a job"""
        for executor in self._executors:
            if executor.can_execute(job):
                return executor
        return None
    
    def execute_job(self, job: Job) -> Any:
        """Execute a job using the appropriate executor"""
        executor = self.get_executor(job)
        if executor is None:
            raise ValueError(f"No executor found for job type: {job.job_type}")
        
        return executor.execute(job)


# Global job executor registry
job_executor_registry = JobExecutorRegistry()


def create_job(job_type: str, priority: JobPriority = JobPriority.NORMAL, 
               parameters: Optional[Dict[str, Any]] = None) -> Job:
    """Create a new job"""
    from utils import generate_job_id
    
    return Job(
        job_id=generate_job_id(job_type, priority.name.lower()),
        job_type=job_type,
        priority=priority,
        status=JobStatus.PENDING,
        created_at=datetime.now(),
        parameters=parameters or {}
    )


def create_sleep_job(duration: int = 5, priority: JobPriority = JobPriority.NORMAL) -> Job:
    """Create a sleep job"""
    return create_job("sleep", priority, {"duration": duration})


def create_compute_job(iterations: int = 1000000, priority: JobPriority = JobPriority.NORMAL) -> Job:
    """Create a compute job"""
    return create_job("compute", priority, {"iterations": iterations})


def create_matrix_job(matrix_size: int = 1000, priority: JobPriority = JobPriority.NORMAL) -> Job:
    """Create a matrix job"""
    return create_job("matrix", priority, {"matrix_size": matrix_size})


def create_fault_injection_job(failure_rate: float = 0.1, duration: int = 3, 
                              priority: JobPriority = JobPriority.NORMAL) -> Job:
    """Create a fault injection job"""
    return create_job("fault_injection", priority, {
        "failure_rate": failure_rate,
        "duration": duration
    })
