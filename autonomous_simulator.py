"""
Autonomous GPU Cluster Simulator
Simulates real-world data center behavior with automatic job generation and fault injection
"""
import time
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

from job_types import Job, JobStatus, JobPriority, job_executor_registry, create_job
from gpu_monitor import gpu_monitor
from utils import logger, generate_job_id


@dataclass
class WorkerInfo:
    """Worker node information"""
    worker_id: str
    status: str  # "online", "offline", "busy", "failed"
    current_job: Optional[Job] = None
    last_heartbeat: datetime = None
    failure_probability: float = 0.0  # Chance of failure per minute
    recovery_time: int = 30  # Seconds to recover after failure
    
    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()
    
    @property
    def is_available(self) -> bool:
        return self.status == "online" and self.current_job is None


class AutonomousClusterSimulator:
    """Simulates autonomous GPU cluster behavior"""
    
    def __init__(self):
        self.workers: Dict[str, WorkerInfo] = {}
        self.jobs: Dict[str, Job] = {}
        self.job_queue: List[Job] = []
        self.running = False
        self.lock = threading.Lock()
        
        # Simulation parameters
        self.job_generation_rate = 2.0  # Jobs per minute
        self.failure_rate = 0.1  # 10% chance of worker failure per hour
        self.recovery_time = 30  # Seconds to recover
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'worker_failures': 0,
            'worker_recoveries': 0,
            'active_workers': 0,
            'simulation_start': datetime.now()
        }
        
        # Start GPU monitoring
        gpu_monitor.start_monitoring()
        
        logger.info("Autonomous cluster simulator initialized")
    
    def set_job_generation_rate(self, rate: float):
        """Update the job generation rate"""
        with self.lock:
            self.job_generation_rate = rate
            logger.info(f"Job generation rate updated to {rate} jobs/minute")
    
    def start(self):
        """Start the autonomous simulation"""
        self.running = True
        
        # Start background tasks
        threading.Thread(target=self._job_generator, daemon=True).start()
        threading.Thread(target=self._job_scheduler, daemon=True).start()
        threading.Thread(target=self._job_executor, daemon=True).start()
        threading.Thread(target=self._fault_injector, daemon=True).start()
        threading.Thread(target=self._worker_monitor, daemon=True).start()
        
        logger.info("Autonomous cluster simulation started")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False
        gpu_monitor.stop_monitoring()
        logger.info("Autonomous cluster simulation stopped")
    
    def add_worker(self, worker_id: str, failure_probability: float = 0.1):
        """Add a worker with configurable failure probability"""
        with self.lock:
            self.workers[worker_id] = WorkerInfo(
                worker_id=worker_id,
                status="online",
                last_heartbeat=datetime.now(),
                failure_probability=failure_probability,
                recovery_time=self.recovery_time
            )
            self.stats['active_workers'] += 1
            logger.info(f"Worker {worker_id} added (failure rate: {failure_probability:.1%}/min)")
    
    def _job_generator(self):
        """Automatically generate realistic jobs"""
        job_types = [
            ("sleep", 0.3, {"duration": (1, 5)}),
            ("compute", 0.4, {"iterations": (100000, 1000000)}),
            ("matrix", 0.2, {"matrix_size": (500, 2000)}),
            ("fault_injection", 0.1, {"failure_rate": (0.05, 0.2), "duration": (2, 8)})
        ]
        
        while self.running:
            try:
                # Generate job based on rate
                if random.random() < (self.job_generation_rate / 60.0):
                    job_type, weight, param_range = random.choices(
                        job_types, 
                        weights=[w for _, w, _ in job_types]
                    )[0]
                    
                    # Generate parameters
                    params = {}
                    for param, (min_val, max_val) in param_range.items():
                        if isinstance(min_val, int):
                            params[param] = random.randint(min_val, max_val)
                        else:
                            params[param] = random.uniform(min_val, max_val)
                    
                    # Create job with realistic priority distribution
                    priority_weights = [0.2, 0.5, 0.2, 0.1]  # LOW, NORMAL, HIGH, CRITICAL
                    priority = random.choices(
                        [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.CRITICAL],
                        weights=priority_weights
                    )[0]
                    
                    job = create_job(job_type, priority, params)
                    
                    with self.lock:
                        self.jobs[job.job_id] = job
                        self.job_queue.append(job)
                        self.stats['total_jobs'] += 1
                    
                    logger.info(f"Auto-generated {job.job_type} job: {job.job_id} (priority: {job.priority.name})")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in job generator: {e}")
                time.sleep(1)
    
    def _fault_injector(self):
        """Simulate realistic worker failures"""
        while self.running:
            try:
                with self.lock:
                    for worker_id, worker in self.workers.items():
                        if worker.status == "online":
                            # Check if worker should fail based on probability
                            failure_chance = worker.failure_probability / 60.0  # Per second
                            if random.random() < failure_chance:
                                self._simulate_worker_failure(worker_id)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in fault injector: {e}")
                time.sleep(5)
    
    def _simulate_worker_failure(self, worker_id: str):
        """Simulate a worker failure"""
        worker = self.workers[worker_id]
        
        logger.warning(f"🚨 WORKER FAILURE: {worker_id} has failed!")
        
        # Mark worker as failed
        worker.status = "failed"
        self.stats['worker_failures'] += 1
        self.stats['active_workers'] -= 1
        
        # If worker has a job, requeue it
        if worker.current_job:
            job = worker.current_job
            job.status = JobStatus.PENDING
            job.worker_id = None
            job.started_at = None
            job.retry_count += 1
            
            if job.retry_count <= job.max_retries:
                self.job_queue.append(job)
                logger.info(f"Job {job.job_id} requeued due to worker failure (retry {job.retry_count})")
            else:
                job.status = JobStatus.FAILED
                job.error_message = "Max retries exceeded due to worker failures"
                self.stats['failed_jobs'] += 1
                logger.error(f"Job {job.job_id} failed after max retries")
            
            worker.current_job = None
        
        # Schedule recovery
        threading.Thread(
            target=self._recover_worker, 
            args=(worker_id,), 
            daemon=True
        ).start()
    
    def _recover_worker(self, worker_id: str):
        """Simulate worker recovery after failure"""
        time.sleep(self.recovery_time)
        
        with self.lock:
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                worker.status = "online"
                worker.last_heartbeat = datetime.now()
                self.stats['worker_recoveries'] += 1
                self.stats['active_workers'] += 1
                
                logger.info(f"🔄 WORKER RECOVERY: {worker_id} is back online!")
    
    def _worker_monitor(self):
        """Monitor worker health and simulate heartbeat failures"""
        while self.running:
            try:
                current_time = datetime.now()
                
                with self.lock:
                    for worker_id, worker in self.workers.items():
                        if worker.status == "online":
                            # Simulate occasional heartbeat failures
                            if random.random() < 0.001:  # 0.1% chance per check
                                self._simulate_worker_failure(worker_id)
                            else:
                                worker.last_heartbeat = current_time
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in worker monitor: {e}")
                time.sleep(10)
    
    def _job_scheduler(self):
        """Schedule jobs to available workers"""
        while self.running:
            try:
                with self.lock:
                    if self.job_queue:
                        # Sort jobs by priority
                        self.job_queue.sort(key=lambda job: job.priority.value, reverse=True)
                        
                        # Find available workers
                        available_workers = [w for w in self.workers.values() if w.is_available]
                        
                        if available_workers:
                            job = self.job_queue.pop(0)
                            # Choose worker with lowest current load (simple load balancing)
                            worker = random.choice(available_workers)
                            
                            # Assign job to worker
                            worker.current_job = job
                            worker.status = "busy"
                            job.status = JobStatus.RUNNING
                            job.started_at = datetime.now()
                            job.worker_id = worker.worker_id
                            
                            logger.info(f"Job {job.job_id} assigned to worker {worker.worker_id}")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in job scheduler: {e}")
                time.sleep(0.5)
    
    def _job_executor(self):
        """Execute jobs assigned to workers"""
        while self.running:
            try:
                with self.lock:
                    for worker in self.workers.values():
                        if worker.current_job and worker.current_job.status == JobStatus.RUNNING:
                            job = worker.current_job
                            
                            # Execute the job
                            try:
                                result = job_executor_registry.execute_job(job)
                                
                                # Mark job as completed
                                job.status = JobStatus.COMPLETED
                                job.completed_at = datetime.now()
                                job.result = result
                                self.stats['completed_jobs'] += 1
                                
                                logger.info(f"✅ Job {job.job_id} completed successfully on {worker.worker_id}")
                                
                            except Exception as e:
                                # Mark job as failed
                                job.status = JobStatus.FAILED
                                job.completed_at = datetime.now()
                                job.error_message = str(e)
                                self.stats['failed_jobs'] += 1
                                
                                logger.error(f"❌ Job {job.job_id} failed on {worker.worker_id}: {e}")
                            
                            # Free the worker
                            worker.current_job = None
                            worker.status = "online"
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in job executor: {e}")
                time.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        with self.lock:
            uptime = (datetime.now() - self.stats['simulation_start']).total_seconds()
            
            # Create a copy of stats with datetime converted to string
            stats_copy = self.stats.copy()
            stats_copy['simulation_start'] = self.stats['simulation_start'].isoformat()
            
            return {
                'simulation_info': {
                    'uptime': uptime,
                    'job_generation_rate': self.job_generation_rate,
                    'failure_rate': self.failure_rate,
                    'recovery_time': self.recovery_time
                },
                'workers': {worker_id: {
                    'worker_id': worker.worker_id,
                    'status': worker.status,
                    'failure_probability': worker.failure_probability,
                    'current_job': worker.current_job.to_dict() if worker.current_job else None,
                    'is_available': worker.is_available,
                    'last_heartbeat': worker.last_heartbeat.isoformat()
                } for worker_id, worker in self.workers.items()},
                'jobs': {job_id: job.to_dict() for job_id, job in self.jobs.items()},
                'job_queue': [job.to_dict() for job in self.job_queue],
                'stats': stats_copy,
                'gpu_info': gpu_monitor.get_system_info()
            }


# Global simulator instance
simulator = AutonomousClusterSimulator()

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gpu_orchestrator_secret'
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/')
def index():
    return render_template('autonomous_dashboard.html')


@app.route('/api/status')
def get_status():
    return jsonify(simulator.get_status())


@app.route('/api/update-job-rate', methods=['POST'])
def update_job_rate():
    """Update the job generation rate"""
    try:
        data = request.get_json()
        new_rate = float(data.get('rate', 2.0))
        
        # Validate rate (0.1 to 50 jobs per minute)
        if new_rate < 0.1:
            new_rate = 0.1
        elif new_rate > 50.0:
            new_rate = 50.0
            
        simulator.set_job_generation_rate(new_rate)
        
        logger.info(f"Job generation rate updated to {new_rate} jobs/minute")
        return jsonify({
            'success': True,
            'new_rate': new_rate,
            'message': f'Job generation rate set to {new_rate} jobs/minute'
        })
        
    except Exception as e:
        logger.error(f"Error updating job rate: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


def start_autonomous_simulation():
    """Start the autonomous cluster simulation"""
    logger.info("=== Starting Autonomous GPU Cluster Simulation ===")
    
    # Start simulator
    simulator.start()
    
    # Add workers with different failure probabilities
    simulator.add_worker("gpu-node-01", failure_probability=0.05)  # 5% failure rate
    simulator.add_worker("gpu-node-02", failure_probability=0.08)  # 8% failure rate
    simulator.add_worker("gpu-node-03", failure_probability=0.12)  # 12% failure rate
    simulator.add_worker("gpu-node-04", failure_probability=0.06)  # 6% failure rate
    simulator.add_worker("gpu-node-05", failure_probability=0.10)  # 10% failure rate
    simulator.add_worker("gpu-node-06", failure_probability=0.07)  # 7% failure rate
    simulator.add_worker("gpu-node-07", failure_probability=0.09)  # 9% failure rate
    simulator.add_worker("gpu-node-08", failure_probability=0.11)  # 11% failure rate
    
    # Start background updates
    def update_loop():
        while simulator.running:
            try:
                socketio.emit('status_update', simulator.get_status())
                time.sleep(0.5)  # Update every 500ms for smooth experience
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(0.5)
    
    threading.Thread(target=update_loop, daemon=True).start()
    
    logger.info("Autonomous simulation started!")
    logger.info("Simulating real-world data center behavior:")
    logger.info("- Automatic job generation (2 jobs/minute)")
    logger.info("- Worker failures and recovery")
    logger.info("- Load balancing across GPU nodes")
    logger.info("- Fault tolerance and job recovery")
    logger.info("Access the dashboard at: http://localhost:8080")
    
    try:
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        simulator.stop()


if __name__ == "__main__":
    start_autonomous_simulation()
