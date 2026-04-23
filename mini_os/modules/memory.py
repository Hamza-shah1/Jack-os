class MemoryBlock:
    def __init__(self, pid, start, size):
        self.pid = pid
        self.start = start
        self.size = size


class MemoryManager:
    def __init__(self, size=64):
        self.total_size = size
        self.memory = [None] * size
        self.allocations = {}

    def allocate(self, pid, size):
        """First Fit allocation. Returns start index or -1 on failure."""
        if size <= 0 or size > self.total_size:
            return -1

        # Find first contiguous free block of `size`
        i = 0
        while i <= self.total_size - size:
            if all(x is None for x in self.memory[i:i + size]):
                for j in range(i, i + size):
                    self.memory[j] = pid
                self.allocations[pid] = MemoryBlock(pid, i, size)
                return i
            i += 1
        return -1

    def best_fit(self, pid, size):
        """Best Fit allocation. Returns start index or -1."""
        best_start = -1
        best_size = self.total_size + 1

        i = 0
        while i < self.total_size:
            if self.memory[i] is None:
                # Find run length
                j = i
                while j < self.total_size and self.memory[j] is None:
                    j += 1
                run = j - i
                if size <= run < best_size:
                    best_size = run
                    best_start = i
                i = j
            else:
                i += 1

        if best_start == -1:
            return -1
        for j in range(best_start, best_start + size):
            self.memory[j] = pid
        self.allocations[pid] = MemoryBlock(pid, best_start, size)
        return best_start

    def deallocate(self, pid):
        """Release memory held by process pid."""
        if pid not in self.allocations:
            return False
        block = self.allocations.pop(pid)
        for j in range(block.start, block.start + block.size):
            self.memory[j] = None
        return True

    def status(self):
        """Return full memory array."""
        return list(self.memory)

    def free_blocks(self):
        """Return list of (start, size) tuples of free contiguous blocks."""
        blocks = []
        i = 0
        while i < self.total_size:
            if self.memory[i] is None:
                j = i
                while j < self.total_size and self.memory[j] is None:
                    j += 1
                blocks.append((i, j - i))
                i = j
            else:
                i += 1
        return blocks

    def used_percent(self):
        used = sum(1 for x in self.memory if x is not None)
        return round(used / self.total_size * 100, 1)

    def free_percent(self):
        return round(100 - self.used_percent(), 1)

    def summary(self):
        used = sum(1 for x in self.memory if x is not None)
        free = self.total_size - used
        return {
            "total": self.total_size,
            "used": used,
            "free": free,
            "used_pct": self.used_percent(),
            "allocations": {
                pid: {"start": b.start, "size": b.size}
                for pid, b in self.allocations.items()
            },
            "free_blocks": self.free_blocks(),
        }

    def compact(self):
        """Compact memory: move all allocated blocks to the front (defragment)."""
        pids = [x for x in self.memory if x is not None]
        self.memory = pids + [None] * (self.total_size - len(pids))
        # Rebuild allocation map
        pos = 0
        new_allocs = {}
        for pid, block in self.allocations.items():
            new_allocs[pid] = MemoryBlock(pid, pos, block.size)
            pos += block.size
        self.allocations = new_allocs
