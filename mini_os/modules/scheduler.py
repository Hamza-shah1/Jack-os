import time
from collections import deque


class Process:
    def __init__(self, pid, burst, priority=0, name=None):
        self.pid = pid
        self.burst = burst
        self.original_burst = burst
        self.priority = priority
        self.name = name or f"P{pid}"
        self.waiting = 0
        self.turnaround = 0
        self.arrival = 0
        self.finish_time = 0
        self.start_time = None


class Scheduler:
    def __init__(self, quantum=2):
        self.queue = deque()
        self.quantum = quantum
        self.process_list = []
        self.current_time = 0

    def add(self, process):
        process.arrival = self.current_time
        self.queue.append(process)
        self.process_list.append(process)

    def run_round_robin(self, delay=0.1):
        """Run Round Robin scheduling and return detailed execution log and stats."""
        execution_log = []
        gantt = []
        self.current_time = 0
        local_queue = deque(self.queue)

        while local_queue:
            p = local_queue.popleft()
            run_time = min(self.quantum, p.burst)

            if p.start_time is None:
                p.start_time = self.current_time
                p.waiting = self.current_time - p.arrival

            gantt.append((p.name, self.current_time, self.current_time + run_time))
            execution_log.append(
                f"[t={self.current_time:>3}] {p.name} runs for {run_time}s (remaining: {p.burst - run_time}s)"
            )
            if delay > 0:
                time.sleep(delay)

            self.current_time += run_time
            p.burst -= run_time

            if p.burst > 0:
                local_queue.append(p)
            else:
                p.finish_time = self.current_time
                p.turnaround = p.finish_time - p.arrival
                execution_log.append(
                    f"[t={self.current_time:>3}] {p.name} COMPLETED  "
                    f"| Turnaround={p.turnaround}s, Waiting={p.waiting}s"
                )

        stats = self._compute_stats()
        execution_log.append("")
        execution_log.append("=== Statistics ===")
        execution_log.append(f"Avg Waiting Time     : {stats['avg_waiting']:.2f}s")
        execution_log.append(f"Avg Turnaround Time  : {stats['avg_turnaround']:.2f}s")
        execution_log.append(f"Total Time           : {self.current_time}s")
        execution_log.append(f"CPU Utilization      : {stats['cpu_util']:.1f}%")

        return execution_log, gantt, stats

    def run_fcfs(self, delay=0.1):
        """First Come First Served scheduling."""
        execution_log = []
        gantt = []
        self.current_time = 0
        sorted_queue = sorted(list(self.queue), key=lambda p: p.arrival)

        for p in sorted_queue:
            if self.current_time < p.arrival:
                self.current_time = p.arrival
            p.waiting = self.current_time - p.arrival
            p.start_time = self.current_time
            run_time = p.burst

            gantt.append((p.name, self.current_time, self.current_time + run_time))
            execution_log.append(
                f"[t={self.current_time:>3}] {p.name} runs for {run_time}s"
            )
            if delay > 0:
                time.sleep(delay)

            self.current_time += run_time
            p.burst = 0
            p.finish_time = self.current_time
            p.turnaround = p.finish_time - p.arrival
            execution_log.append(
                f"[t={self.current_time:>3}] {p.name} COMPLETED  "
                f"| Turnaround={p.turnaround}s, Waiting={p.waiting}s"
            )

        stats = self._compute_stats()
        execution_log.append("")
        execution_log.append("=== Statistics ===")
        execution_log.append(f"Avg Waiting Time     : {stats['avg_waiting']:.2f}s")
        execution_log.append(f"Avg Turnaround Time  : {stats['avg_turnaround']:.2f}s")

        return execution_log, gantt, stats

    def run_sjf(self, delay=0.1):
        """Shortest Job First (non-preemptive)."""
        execution_log = []
        gantt = []
        self.current_time = 0
        remaining = sorted(list(self.queue), key=lambda p: p.burst)

        for p in remaining:
            if self.current_time < p.arrival:
                self.current_time = p.arrival
            p.waiting = self.current_time - p.arrival
            p.start_time = self.current_time
            run_time = p.burst

            gantt.append((p.name, self.current_time, self.current_time + run_time))
            execution_log.append(
                f"[t={self.current_time:>3}] {p.name} (burst={run_time}s) runs"
            )
            if delay > 0:
                time.sleep(delay)

            self.current_time += run_time
            p.burst = 0
            p.finish_time = self.current_time
            p.turnaround = p.finish_time - p.arrival
            execution_log.append(
                f"[t={self.current_time:>3}] {p.name} COMPLETED  "
                f"| Turnaround={p.turnaround}s, Waiting={p.waiting}s"
            )

        stats = self._compute_stats()
        execution_log.append("")
        execution_log.append("=== Statistics ===")
        execution_log.append(f"Avg Waiting Time     : {stats['avg_waiting']:.2f}s")
        execution_log.append(f"Avg Turnaround Time  : {stats['avg_turnaround']:.2f}s")

        return execution_log, gantt, stats

    def _compute_stats(self):
        completed = [p for p in self.process_list if p.finish_time > 0]
        if not completed:
            return {"avg_waiting": 0, "avg_turnaround": 0, "cpu_util": 0}
        total_burst = sum(p.original_burst for p in completed)
        avg_waiting = sum(p.waiting for p in completed) / len(completed)
        avg_turnaround = sum(p.turnaround for p in completed) / len(completed)
        cpu_util = (total_burst / self.current_time * 100) if self.current_time > 0 else 0
        return {
            "avg_waiting": avg_waiting,
            "avg_turnaround": avg_turnaround,
            "cpu_util": cpu_util,
        }

    def reset(self):
        self.queue = deque()
        self.process_list = []
        self.current_time = 0

    def get_process_table(self):
        rows = []
        for p in self.process_list:
            rows.append({
                "PID": p.pid,
                "Name": p.name,
                "Burst": p.original_burst,
                "Priority": p.priority,
                "Waiting": p.waiting,
                "Turnaround": p.turnaround,
                "Finish": p.finish_time,
            })
        return rows
