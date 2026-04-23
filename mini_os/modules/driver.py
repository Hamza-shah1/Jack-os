import datetime
import queue
import threading


class InputBuffer:
    def __init__(self):
        self._buf = queue.Queue()

    def feed(self, data):
        self._buf.put(data)

    def read(self, block=False, timeout=0.5):
        try:
            return self._buf.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def size(self):
        return self._buf.qsize()


class OutputBuffer:
    def __init__(self, max_lines=200):
        self._lines = []
        self.max_lines = max_lines

    def write(self, data):
        line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {data}"
        self._lines.append(line)
        if len(self._lines) > self.max_lines:
            self._lines = self._lines[-self.max_lines:]
        return line

    def read_all(self):
        return list(self._lines)

    def clear(self):
        self._lines = []


class KeyboardDevice:
    """Simulated keyboard input device."""

    DEVICE_NAME = "keyboard"

    def __init__(self):
        self.buffer = InputBuffer()
        self.connected = True
        self.events = []

    def press_key(self, key):
        event = {"type": "keypress", "key": key, "time": datetime.datetime.now().isoformat()}
        self.events.append(event)
        self.buffer.feed(key)
        return event

    def read(self):
        return self.buffer.read()

    def status(self):
        return {"device": self.DEVICE_NAME, "connected": self.connected, "buffer_size": self.buffer.size()}


class DisplayDevice:
    """Simulated display output device."""

    DEVICE_NAME = "display"

    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height
        self.buffer = OutputBuffer()
        self.connected = True

    def print(self, data):
        return self.buffer.write(str(data))

    def clear(self):
        self.buffer.clear()

    def screen(self):
        return self.buffer.read_all()

    def status(self):
        return {
            "device": self.DEVICE_NAME,
            "connected": self.connected,
            "resolution": f"{self.width}x{self.height}",
            "lines": len(self.buffer.read_all()),
        }


class DiskDevice:
    """Simulated disk device with read/write tracking."""

    DEVICE_NAME = "disk"

    def __init__(self, name="sda", capacity_mb=512):
        self.name = name
        self.capacity_mb = capacity_mb
        self._storage = {}
        self.reads = 0
        self.writes = 0
        self.connected = True

    def write_block(self, sector, data):
        self._storage[sector] = data
        self.writes += 1
        return True

    def read_block(self, sector):
        self.reads += 1
        return self._storage.get(sector)

    def used_sectors(self):
        return len(self._storage)

    def status(self):
        return {
            "device": self.DEVICE_NAME,
            "name": self.name,
            "connected": self.connected,
            "capacity_mb": self.capacity_mb,
            "used_sectors": self.used_sectors(),
            "reads": self.reads,
            "writes": self.writes,
        }


class NetworkDevice:
    """Simulated network interface."""

    DEVICE_NAME = "eth0"

    def __init__(self, ip="192.168.1.1", mac="00:1A:2B:3C:4D:5E"):
        self.ip = ip
        self.mac = mac
        self.connected = False
        self.packets_sent = 0
        self.packets_received = 0
        self._inbox = queue.Queue()

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def send_packet(self, dest, data):
        if not self.connected:
            return False, "Not connected"
        self.packets_sent += 1
        return True, f"Packet sent to {dest}: {data}"

    def receive_packet(self):
        if self._inbox.empty():
            return None
        self.packets_received += 1
        return self._inbox.get()

    def inject_packet(self, data):
        """Simulate receiving a packet (for testing)."""
        self._inbox.put(data)

    def status(self):
        return {
            "device": self.DEVICE_NAME,
            "ip": self.ip,
            "mac": self.mac,
            "connected": self.connected,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
        }


class DeviceDriver:
    """Device Driver Manager: manages all hardware devices."""

    def __init__(self):
        self.keyboard = KeyboardDevice()
        self.display = DisplayDevice()
        self.disk = DiskDevice()
        self.network = NetworkDevice()
        self._devices = {
            "keyboard": self.keyboard,
            "display": self.display,
            "disk": self.disk,
            "network": self.network,
        }

    def input(self, data=None):
        """Read from keyboard buffer or provide data."""
        if data is not None:
            self.keyboard.press_key(data)
        return self.keyboard.read()

    def output(self, data):
        """Write to display."""
        return self.display.print(data)

    def all_status(self):
        return {name: dev.status() for name, dev in self._devices.items()}

    def get_device(self, name):
        return self._devices.get(name)

    def list_devices(self):
        return [
            {"name": name, "connected": dev.status().get("connected", False)}
            for name, dev in self._devices.items()
        ]
