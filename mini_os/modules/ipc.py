from queue import Queue
import threading


class MessageQueue:
    """Shared-memory style IPC via message queues."""

    def __init__(self):
        self._queue = Queue()
        self._history = []

    def send(self, sender, receiver, msg):
        payload = {"sender": sender, "receiver": receiver, "msg": msg}
        self._queue.put(payload)
        self._history.append(payload)

    def receive(self, receiver=None):
        """Receive next message. If receiver specified, only match that receiver."""
        if self._queue.empty():
            return None
        if receiver is None:
            return self._queue.get()
        # Search queue for a matching message
        tmp = []
        result = None
        while not self._queue.empty():
            item = self._queue.get()
            if result is None and item["receiver"] == receiver:
                result = item
            else:
                tmp.append(item)
        for item in tmp:
            self._queue.put(item)
        return result

    def peek_all(self):
        return list(self._queue.queue)

    def history(self):
        return list(self._history)

    def size(self):
        return self._queue.qsize()


class Pipe:
    """Unidirectional pipe between two processes."""

    def __init__(self, name="pipe"):
        self.name = name
        self._buffer = Queue()
        self._closed = False

    def write(self, data):
        if self._closed:
            return False, "Pipe is closed"
        self._buffer.put(data)
        return True, "Data written to pipe"

    def read(self):
        if self._buffer.empty():
            return None
        return self._buffer.get()

    def close(self):
        self._closed = True

    def is_closed(self):
        return self._closed

    def size(self):
        return self._buffer.qsize()


class SharedMemory:
    """Simulated shared memory region for IPC."""

    def __init__(self, name, size=256):
        self.name = name
        self.size = size
        self._data = {}
        self._lock = threading.Lock()

    def write(self, key, value):
        with self._lock:
            self._data[key] = value
        return True

    def read(self, key):
        with self._lock:
            return self._data.get(key)

    def all_data(self):
        with self._lock:
            return dict(self._data)

    def clear(self, key=None):
        with self._lock:
            if key:
                self._data.pop(key, None)
            else:
                self._data.clear()


class IPC:
    """IPC Manager: combines message queues, pipes, and shared memory."""

    def __init__(self):
        self.message_queue = MessageQueue()
        self.pipes = {}
        self.shared_memories = {}

    def send(self, msg, sender="kernel", receiver="user"):
        self.message_queue.send(sender, receiver, msg)

    def receive(self, receiver=None):
        return self.message_queue.receive(receiver)

    def create_pipe(self, name):
        if name in self.pipes:
            return False, f"Pipe '{name}' already exists"
        self.pipes[name] = Pipe(name)
        return True, f"Pipe '{name}' created"

    def pipe_write(self, name, data):
        if name not in self.pipes:
            return False, f"Pipe '{name}' does not exist"
        return self.pipes[name].write(data)

    def pipe_read(self, name):
        if name not in self.pipes:
            return None
        return self.pipes[name].read()

    def create_shared_memory(self, name, size=256):
        if name in self.shared_memories:
            return False, f"Shared memory '{name}' already exists"
        self.shared_memories[name] = SharedMemory(name, size)
        return True, f"Shared memory '{name}' ({size} bytes) created"

    def shm_write(self, name, key, value):
        if name not in self.shared_memories:
            return False, f"Shared memory '{name}' not found"
        self.shared_memories[name].write(key, value)
        return True, "Written"

    def shm_read(self, name, key):
        if name not in self.shared_memories:
            return None
        return self.shared_memories[name].read(key)

    def status(self):
        return {
            "message_queue_size": self.message_queue.size(),
            "pipes": {n: {"size": p.size(), "closed": p.is_closed()} for n, p in self.pipes.items()},
            "shared_memories": {n: sm.all_data() for n, sm in self.shared_memories.items()},
        }
