import datetime
import os

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Logger:
    def __init__(self, log_file="log.txt", max_entries=500):
        self.log_file = log_file
        self.max_entries = max_entries
        self._entries = []

    def _write(self, level, module, msg):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "level": level,
            "module": module,
            "msg": msg,
        }
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        line = f"[{timestamp}] [{level:<8}] [{module:<12}] {msg}\n"
        try:
            with open(self.log_file, "a") as f:
                f.write(line)
        except OSError:
            pass
        return entry

    def debug(self, msg, module="system"):
        return self._write("DEBUG", module, msg)

    def info(self, msg, module="system"):
        return self._write("INFO", module, msg)

    def warning(self, msg, module="system"):
        return self._write("WARNING", module, msg)

    def error(self, msg, module="system"):
        return self._write("ERROR", module, msg)

    def critical(self, msg, module="system"):
        return self._write("CRITICAL", module, msg)

    def log(self, msg, module="system"):
        """Backward-compatible generic log (INFO level)."""
        return self.info(msg, module)

    def get_entries(self, level=None, module=None, limit=100):
        entries = self._entries
        if level:
            entries = [e for e in entries if e["level"] == level.upper()]
        if module:
            entries = [e for e in entries if e["module"] == module]
        return entries[-limit:]

    def clear(self):
        self._entries = []
        try:
            if os.path.exists(self.log_file):
                open(self.log_file, "w").close()
        except OSError:
            pass

    def summary(self):
        counts = {lvl: 0 for lvl in LOG_LEVELS}
        for e in self._entries:
            if e["level"] in counts:
                counts[e["level"]] += 1
        return counts

    def export(self, dest_file):
        try:
            with open(dest_file, "w") as f:
                for e in self._entries:
                    f.write(f"[{e['timestamp']}] [{e['level']:<8}] [{e['module']:<12}] {e['msg']}\n")
            return True, f"Log exported to '{dest_file}'"
        except OSError as ex:
            return False, str(ex)
