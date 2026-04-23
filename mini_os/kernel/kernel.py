from modules.scheduler import Scheduler, Process
from modules.memory import MemoryManager
from modules.filesystem import FileSystem
from modules.ipc import IPC
from modules.security import Security
from modules.logger import Logger
from modules.driver import DeviceDriver


class Kernel:
    """
    Mini OS Kernel — coordinates all OS subsystems.
    Acts as the central controller for the operating system simulation.
    """

    VERSION = "1.0.0"
    OS_NAME = "Jack OS"

    def __init__(self):
        self.logger = Logger()
        self.scheduler = Scheduler(quantum=2)
        self.memory = MemoryManager(size=64)
        self.fs = FileSystem()
        self.ipc = IPC()
        self.security = Security()
        self.driver = DeviceDriver()
        self.running = False
        self.boot_time = None
        self._pid_counter = 1

    def boot(self):
        """Boot the OS kernel and initialize all subsystems."""
        import datetime
        self.boot_time = datetime.datetime.now()
        self.running = True

        self.logger.info("=== Jack OS Kernel Booting ===", module="kernel")
        self.logger.info(f"Version: {self.VERSION}", module="kernel")
        self.logger.info("Initializing scheduler (Round Robin, quantum=2)", module="scheduler")
        self.logger.info("Initializing memory manager (64 units)", module="memory")
        self.logger.info("Initializing file system", module="fs")
        self.logger.info("Initializing IPC subsystem", module="ipc")
        self.logger.info("Initializing security module", module="security")
        self.logger.info("Initializing device drivers", module="driver")
        self.logger.info("=== Boot complete ===", module="kernel")

        # Seed filesystem with default structure
        self.fs.create_dir([], "home")
        self.fs.create_dir(["home"], "admin")
        self.fs.create_dir([], "tmp")
        self.fs.create_dir([], "var")
        self.fs.create_dir(["var"], "log")
        self.fs.create(["var", "log"], "system.log", is_file=True)
        self.fs.write(["var", "log", "system.log"], f"Jack OS started at {self.boot_time}\n")

        # IPC defaults
        self.ipc.create_pipe("sys_pipe")
        self.ipc.create_shared_memory("sys_shm", 256)

        self.driver.display.print(f"{self.OS_NAME} {self.VERSION} — Boot OK")
        return True

    def shutdown(self):
        """Graceful shutdown."""
        self.logger.info("Shutting down kernel...", module="kernel")
        self.running = False
        self.logger.info("Shutdown complete", module="kernel")

    def next_pid(self):
        pid = self._pid_counter
        self._pid_counter += 1
        return pid

    def spawn_process(self, name, burst, priority=0):
        """Create and register a new process."""
        pid = self.next_pid()
        p = Process(pid, burst, priority=priority, name=name)
        self.scheduler.add(p)
        size = max(2, burst // 2)
        addr = self.memory.allocate(pid, size)
        self.logger.info(
            f"Process '{name}' (PID={pid}, burst={burst}) spawned, mem@{addr}",
            module="scheduler"
        )
        return pid, p

    def kill_process(self, pid):
        """Remove a process from the scheduler and release its memory.

        Returns a dict: {'found': bool, 'memory_freed': bool}
        """
        # Find process in scheduler
        target = None
        for p in self.scheduler.process_list:
            if p.pid == pid:
                target = p
                break

        if target is None:
            self.logger.warning(f"kill_process: PID {pid} not found", module="kernel")
            return {"found": False, "memory_freed": False}

        # Remove from scheduler list and queue
        self.scheduler.process_list.remove(target)
        try:
            self.scheduler.queue.remove(target)
        except ValueError:
            pass

        freed = self.memory.deallocate(pid)
        self.logger.info(f"Process PID={pid} ({target.name}) killed, memory freed={freed}", module="kernel")
        return {"found": True, "memory_freed": freed}

    def system_status(self):
        """Return a snapshot of the entire system state."""
        return {
            "os": self.OS_NAME,
            "version": self.VERSION,
            "boot_time": str(self.boot_time),
            "running": self.running,
            "memory": self.memory.summary(),
            "ipc": self.ipc.status(),
            "devices": self.driver.all_status(),
            "log_summary": self.logger.summary(),
        }
