"""
GPU monitoring and resource management for the GPU Mini-Cluster Orchestrator
"""
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import psutil

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False


@dataclass
class GPUInfo:
    """GPU information data structure"""
    gpu_id: int
    name: str
    memory_total: int  # bytes
    memory_used: int   # bytes
    memory_free: int   # bytes
    utilization_gpu: float  # percentage
    utilization_memory: float  # percentage
    temperature: float  # celsius
    power_usage: float  # watts
    last_updated: datetime
    
    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage"""
        if self.memory_total == 0:
            return 0.0
        return self.memory_used / self.memory_total
    
    @property
    def is_available(self) -> bool:
        """Check if GPU is available for new jobs"""
        return self.memory_usage_percent < 0.9  # Less than 90% memory usage
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'gpu_id': self.gpu_id,
            'name': self.name,
            'memory_total': self.memory_total,
            'memory_used': self.memory_used,
            'memory_free': self.memory_free,
            'utilization_gpu': self.utilization_gpu,
            'utilization_memory': self.utilization_memory,
            'temperature': self.temperature,
            'power_usage': self.power_usage,
            'last_updated': self.last_updated.isoformat(),
            'memory_usage_percent': self.memory_usage_percent,
            'is_available': self.is_available
        }


class GPUMonitor:
    """GPU monitoring and management class"""
    
    def __init__(self, check_interval: float = 1.0, num_gpus: int = 8):
        self.check_interval = check_interval
        self.num_gpus = num_gpus
        self.gpus: Dict[int, GPUInfo] = {}
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Initialize NVML if available
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.nvml_available = True
            except Exception as e:
                print(f"Warning: Failed to initialize NVML: {e}")
                self.nvml_available = False
        else:
            self.nvml_available = False
            print("Warning: pynvml not available, using simulated GPU data")
    
    def start_monitoring(self):
        """Start GPU monitoring in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop GPU monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._update_gpu_info()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in GPU monitoring: {e}")
                time.sleep(self.check_interval)
    
    def _update_gpu_info(self):
        """Update GPU information"""
        with self.lock:
            if self.nvml_available:
                self._update_real_gpu_info()
            else:
                self._update_simulated_gpu_info()
    
    def _update_real_gpu_info(self):
        """Update real GPU information using NVML"""
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Get GPU name
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # Get memory info
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_total = memory_info.total
                memory_used = memory_info.used
                memory_free = memory_info.free
                
                # Get utilization
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                utilization_gpu = utilization.gpu
                utilization_memory = utilization.memory
                
                # Get temperature
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                # Get power usage
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                
                self.gpus[i] = GPUInfo(
                    gpu_id=i,
                    name=name,
                    memory_total=memory_total,
                    memory_used=memory_used,
                    memory_free=memory_free,
                    utilization_gpu=utilization_gpu,
                    utilization_memory=utilization_memory,
                    temperature=temperature,
                    power_usage=power_usage,
                    last_updated=datetime.now()
                )
                
        except Exception as e:
            print(f"Error updating real GPU info: {e}")
            self._update_simulated_gpu_info()
    
    def _update_simulated_gpu_info(self):
        """Update simulated GPU information"""
        import random
        
        # Simulate 8 GPUs to match the 8 GPU nodes
        for i in range(self.num_gpus):
            # Simulate some variation in GPU usage
            base_memory_total = 8 * 1024 * 1024 * 1024  # 8GB
            base_memory_used = random.randint(0, int(base_memory_total * 0.7))
            
            self.gpus[i] = GPUInfo(
                gpu_id=i,
                name=f"Simulated GPU {i}",
                memory_total=base_memory_total,
                memory_used=base_memory_used,
                memory_free=base_memory_total - base_memory_used,
                utilization_gpu=random.uniform(0, 100),
                utilization_memory=random.uniform(0, 100),
                temperature=random.uniform(30, 80),
                power_usage=random.uniform(50, 200),
                last_updated=datetime.now()
            )
    
    def get_gpu_info(self, gpu_id: int) -> Optional[GPUInfo]:
        """Get information for a specific GPU"""
        with self.lock:
            return self.gpus.get(gpu_id)
    
    def get_all_gpus(self) -> List[GPUInfo]:
        """Get information for all GPUs"""
        with self.lock:
            return list(self.gpus.values())
    
    def get_available_gpus(self) -> List[GPUInfo]:
        """Get list of available GPUs"""
        with self.lock:
            return [gpu for gpu in self.gpus.values() if gpu.is_available]
    
    def get_best_gpu(self) -> Optional[GPUInfo]:
        """Get the best available GPU (lowest memory usage)"""
        available_gpus = self.get_available_gpus()
        if not available_gpus:
            return None
        
        return min(available_gpus, key=lambda gpu: gpu.memory_usage_percent)
    
    def get_gpu_count(self) -> int:
        """Get number of GPUs"""
        with self.lock:
            return len(self.gpus)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get overall system information"""
        with self.lock:
            total_gpus = len(self.gpus)
            available_gpus = len([gpu for gpu in self.gpus.values() if gpu.is_available])
            
            total_memory = sum(gpu.memory_total for gpu in self.gpus.values())
            used_memory = sum(gpu.memory_used for gpu in self.gpus.values())
            
            avg_utilization = sum(gpu.utilization_gpu for gpu in self.gpus.values()) / max(total_gpus, 1)
            avg_temperature = sum(gpu.temperature for gpu in self.gpus.values()) / max(total_gpus, 1)
            
            return {
                'total_gpus': total_gpus,
                'available_gpus': available_gpus,
                'total_memory': total_memory,
                'used_memory': used_memory,
                'memory_usage_percent': used_memory / max(total_memory, 1),
                'avg_utilization': avg_utilization,
                'avg_temperature': avg_temperature,
                'nvml_available': self.nvml_available
            }


# Global GPU monitor instance
gpu_monitor = GPUMonitor(num_gpus=8)
