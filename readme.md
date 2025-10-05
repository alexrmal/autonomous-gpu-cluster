# Autonomous GPU Cluster Simulator

A lightweight distributed system that simulates an autonomous GPU cluster with fault tolerance. This simulator automatically generates jobs, distributes them across 8 GPU nodes, and demonstrates real-world data center behavior with worker failures and recovery.

## Features

- **Autonomous Job Generation**: Automatically creates jobs with realistic names and priorities
- **8 GPU Node Simulation**: Simulates 8 GPU nodes with different failure rates
- **Fault Tolerance**: Automatic detection of node failures and job recovery
- **GPU Resource Monitoring**: Real-time GPU utilization tracking using NVML
- **Interactive Web Dashboard**: Real-time monitoring with customizable job generation rates
- **Heartbeat Mechanism**: Continuous health monitoring of worker nodes
- **Load Balancing**: Intelligent job distribution across available GPUs
- **Multiple Job Types**: Sleep, compute, matrix, and fault injection jobs
- **Real-time Statistics**: Comprehensive monitoring and metrics
- **Customizable Job Rates**: Adjust job generation from 0.1 to 50 jobs/minute

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Master Node   │    │   Worker Node   │    │   Worker Node   │
│   (Orchestrator)│◄──►│   (GPU Node 1)  │    │   (GPU Node 2)  │
│                 │    │                 │    │                 │
│ • Job Scheduler │    │ • GPU Monitor   │    │ • GPU Monitor   │
│ • Fault Detector│    │ • Job Executor  │    │ • Job Executor  │
│ • Web Dashboard │    │ • Heartbeat     │    │ • Heartbeat     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Step 1: Install Dependencies
```bash
pip3 install -r requirements.txt
```

### Step 2: Start the Autonomous Simulator
```bash
python3 autonomous_simulator.py
```

You'll see output like:
```
Autonomous cluster simulator initialized
Worker gpu-node-01 added (failure rate: 5.0%/min)
Worker gpu-node-02 added (failure rate: 8.0%/min)
...
Access the dashboard at: http://localhost:8080
```

### Step 3: Access the Web Dashboard
Open your web browser and go to: **http://localhost:8080**

The simulator will automatically:
- Start 8 GPU nodes with different failure rates (5%-12%)
- Generate jobs at 2 jobs/minute (customizable via dashboard)
- Monitor GPU resources and worker health
- Handle failures and recovery automatically

### Step 4: Customize Job Generation
In the web dashboard, you can:
1. Use the slider to adjust job generation rate (0.1 to 50 jobs/minute)
2. Click preset buttons for common rates (Light Load, Normal, High Load, Extreme, MAXIMUM)
3. Watch jobs get automatically distributed across workers
4. Observe fault tolerance as workers fail and recover

## Usage

The autonomous simulator runs completely independently. Once started, it will:

1. **Automatically generate jobs** with realistic names like "calc-urgent-1234" or "gpu-matrix-5678"
2. **Distribute jobs** across 8 GPU nodes with different failure rates (5% to 12%)
3. **Monitor GPU resources** including utilization, memory, and temperature
4. **Handle failures** by detecting failed workers and reassigning their jobs
5. **Provide real-time monitoring** through the web dashboard

### Dashboard Features

- **Job Generation Rate Control**: Slider to adjust from 0.1 to 50 jobs/minute
- **Preset Buttons**: Quick access to Light Load, Normal, High Load, Extreme, and MAXIMUM rates
- **Real-time Statistics**: Live updates of jobs, workers, and GPU metrics
- **Worker Status**: Monitor health and current jobs for all 8 nodes
- **GPU Monitoring**: Track utilization, memory usage, and temperature

## Project Structure

```
orchestrator/
├── autonomous_simulator.py      # Main autonomous simulator and web server
├── gpu_monitor.py              # GPU resource monitoring (NVML)
├── job_types.py                # Job definitions and execution logic
├── utils.py                    # Utility functions and logging
├── templates/
│   └── autonomous_dashboard.html # Web dashboard interface
├── requirements.txt            # Python dependencies
├── readme.md                   # This file - complete documentation
└── project_summary.md          # Project overview and technical summary
```

## Job Types

The simulator automatically generates four types of jobs with realistic names:

### Sleep Jobs
Simulate GPU idle time or simple operations:
- Examples: "wait-urgent-1234", "pause-critical-5678", "idle-normal-9012"

### Compute Jobs
Simulate GPU computation workloads:
- Examples: "calc-important-3456", "process-standard-7890", "analyze-critical-1234"

### Matrix Jobs
Simulate GPU matrix operations (requires numpy):
- Examples: "gpu-algebra-5678", "matrix-linear-9012", "tensor-gpu-3456"

### Fault Injection Jobs
Test fault tolerance with configurable failure rates:
- Examples: "validate-test-7890", "check-verify-1234", "inject-test-5678"

## Fault Tolerance Features

- **Automatic Failure Detection**: Heartbeat monitoring detects failed workers
- **Job Recovery**: Failed jobs are automatically requeued to healthy workers
- **Retry Logic**: Configurable retry attempts for failed jobs
- **Timeout Handling**: Jobs that run too long are automatically terminated
- **Worker Health Monitoring**: Continuous monitoring of worker status and GPU resources

## Web Dashboard Features

- **Real-time Monitoring**: Live updates of system status every 500ms
- **Interactive Job Rate Controls**: Slider and preset buttons for job generation
- **Worker Status**: Monitor health and current jobs for all 8 nodes
- **GPU Metrics**: Real-time GPU utilization, memory usage, and temperature
- **Job Queue**: View pending and running jobs
- **Statistics**: Comprehensive system statistics and performance metrics

## Monitoring and Logging

The system provides comprehensive logging with color-coded output:

- **INFO**: General system information (green)
- **WARNING**: Potential issues (yellow)
- **ERROR**: Error conditions (red)
- **DEBUG**: Detailed debugging information (cyan)

Logs are written to both console and file (`orchestrator.log`).

## Troubleshooting

### "Command not found: python"
Use `python3` instead of `python`

### "Module not found" errors
Run: `pip3 install -r requirements.txt`

### Can't access web dashboard
Make sure the simulator is running and check http://localhost:8080

### Port 8080 already in use
Kill any existing processes: `pkill -f autonomous_simulator`

### System not responding
Check the terminal output for error messages and verify all dependencies are installed.

## Advanced Usage

### Custom Job Executors

Create custom job executors by extending the `JobExecutor` class:

```python
from job_types import JobExecutor, Job

class CustomJobExecutor(JobExecutor):
    def execute(self, job: Job) -> Any:
        # Custom job execution logic
        return "Custom job completed"
    
    def can_execute(self, job: Job) -> bool:
        return job.job_type == "custom"

# Register the executor
from job_types import job_executor_registry
job_executor_registry.register(CustomJobExecutor())
```

### GPU Integration

The system automatically detects and uses NVIDIA GPUs via NVML when available. For systems without NVIDIA GPUs, it falls back to simulated GPU data.

### Scaling

The system is designed to scale horizontally by modifying the worker configuration in `autonomous_simulator.py`. You can add more GPU nodes by adding additional `simulator.add_worker()` calls with different failure rates.

## Contributing

This project demonstrates key concepts in distributed systems, fault tolerance, and GPU resource management. It's designed as a learning tool and proof-of-concept for more sophisticated cluster management systems.

## License

This project is provided as-is for educational and demonstration purposes.

## Learning Outcomes

By studying and running this project, you'll understand:

- **Distributed Systems**: Master-worker architecture, message passing, consensus
- **Fault Tolerance**: Failure detection, recovery mechanisms, redundancy
- **Resource Management**: GPU monitoring, load balancing, scheduling algorithms
- **Real-time Systems**: Heartbeat mechanisms, timeout handling, live monitoring
- **Web Technologies**: Real-time dashboards, WebSocket communication, REST APIs

This mini-orchestrator showcases the fundamental principles used in production systems like Kubernetes, Slurm, and other cluster management platforms.
