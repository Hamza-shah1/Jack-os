"""
Terminal Tab — Simulates the Kafka Shell commands inside the Python GUI.
Supports: cd, ls, ps, kill, history, export, unset, help, exit,
          I/O redirection (>, >>), piping (|), fg/bg job control,
          filesystem operations, and IPC/memory commands.
"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import io


class TerminalTab:
    PROMPT = "kafka> "
    BANNER = (
        "==============================================\n"
        "         Welcome to Kafka Shell (Python)    \n"
        "==============================================\n"
        "       A Lightweight Customized Shell        \n"
        "==============================================\n"
        "   Made by 24CS070, 24CS062, 24CS028         \n"
        "==============================================\n"
        "Type 'help' to see available commands.\n\n"
    )

    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = tk.Frame(parent, bg="#1e1e2e")

        # Shell state
        self.env_vars = {}
        self.history = []
        self.history_index = -1
        self.jobs = []           # list of {"id": int, "cmd": str, "status": "running"|"stopped"}
        self.cwd = []            # current directory path (list of path parts)
        self.input_buffer = {}   # for I/O redirection input files

        self._build()
        self._print(self.BANNER)
        self._print_prompt()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build(self):
        f = self.frame

        header = tk.Label(
            f, text="Kafka Shell — Terminal Emulator",
            bg="#181825", fg="#cba6f7", font=("Courier", 11, "bold"), pady=4
        )
        header.pack(fill="x")

        self.output = scrolledtext.ScrolledText(
            f, bg="#0d0d1a", fg="#a6e3a1", insertbackground="#cba6f7",
            font=("Courier New", 10), wrap="word", state="disabled"
        )
        self.output.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        # Colour tags
        self.output.tag_config("prompt", foreground="#cba6f7")
        self.output.tag_config("error",  foreground="#f38ba8")
        self.output.tag_config("info",   foreground="#89dceb")
        self.output.tag_config("success",foreground="#a6e3a1")
        self.output.tag_config("warn",   foreground="#f9e2af")

        inp_frame = tk.Frame(f, bg="#1e1e2e")
        inp_frame.pack(fill="x", padx=4, pady=4)

        tk.Label(inp_frame, text=self.PROMPT, bg="#1e1e2e", fg="#cba6f7",
                 font=("Courier New", 10)).pack(side="left")

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            inp_frame, textvariable=self.input_var, bg="#181825", fg="#cdd6f4",
            insertbackground="#cba6f7", font=("Courier New", 10), relief="flat"
        )
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_entry.bind("<Return>",   self._on_enter)
        self.input_entry.bind("<Up>",       self._history_up)
        self.input_entry.bind("<Down>",     self._history_down)
        self.input_entry.bind("<Tab>",      self._tab_complete)
        self.input_entry.focus()

        tk.Button(inp_frame, text="Run", bg="#cba6f7", fg="#1e1e2e",
                  font=("Courier", 9), command=self._on_enter).pack(side="right", padx=4)

    # ------------------------------------------------------------------ #
    # Output helpers
    # ------------------------------------------------------------------ #
    def _print(self, text, tag=None):
        self.output.config(state="normal")
        if tag:
            self.output.insert("end", text, tag)
        else:
            self.output.insert("end", text)
        self.output.see("end")
        self.output.config(state="disabled")

    def _println(self, text, tag=None):
        self._print(text + "\n", tag)

    def _print_prompt(self):
        cwd_str = "/" + "/".join(self.cwd) if self.cwd else "/"
        self._print(f"\n[{cwd_str}] {self.PROMPT}", "prompt")

    def _error(self, msg):
        self._println(f"kafka: {msg}", "error")

    # ------------------------------------------------------------------ #
    # Input handling
    # ------------------------------------------------------------------ #
    def _on_enter(self, event=None):
        raw = self.input_var.get()
        self.input_var.set("")
        self._print(raw + "\n")
        if raw.strip():
            self.history.append(raw)
            self.history_index = len(self.history)
        self._execute(raw.strip())
        self._print_prompt()

    def _history_up(self, event=None):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.input_var.set(self.history[self.history_index])

    def _history_down(self, event=None):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input_var.set(self.history[self.history_index])
        else:
            self.history_index = len(self.history)
            self.input_var.set("")

    def _tab_complete(self, event=None):
        partial = self.input_var.get()
        parts = partial.split()
        if not parts:
            return "break"
        all_cmds = list(COMMANDS.keys())
        matches = [c for c in all_cmds if c.startswith(parts[-1])]
        if len(matches) == 1:
            parts[-1] = matches[0]
            self.input_var.set(" ".join(parts))
        elif matches:
            self._println("\n" + "  ".join(matches), "info")
        return "break"

    # ------------------------------------------------------------------ #
    # Command dispatch
    # ------------------------------------------------------------------ #
    def _execute(self, line):
        if not line:
            return

        # Expand env vars
        for k, v in self.env_vars.items():
            line = line.replace(f"${k}", v)

        # Handle pipe
        if "|" in line:
            self._handle_pipe(line)
            return

        # Handle I/O redirection
        if ">" in line or "<" in line:
            self._handle_redirect(line)
            return

        # Background job
        background = False
        if line.endswith("&"):
            background = True
            line = line[:-1].strip()

        args = line.split()
        if not args:
            return
        cmd, *rest = args

        handler = COMMANDS.get(cmd)
        if handler:
            if background:
                job_id = len(self.jobs) + 1
                self.jobs.append({"id": job_id, "cmd": line, "status": "running"})
                self._println(f"[{job_id}] {job_id} (background)", "info")
                threading.Thread(target=handler, args=(self, rest), daemon=True).start()
            else:
                handler(self, rest)
        else:
            self._error(f"command not found: '{cmd}'. Type 'help' for commands.")

    # ------------------------------------------------------------------ #
    # I/O Redirection
    # ------------------------------------------------------------------ #
    def _handle_redirect(self, line):
        append = ">>" in line
        if append:
            parts = line.split(">>", 1)
            mode = "append"
        elif ">" in line:
            parts = line.split(">", 1)
            mode = "write"
        elif "<" in line:
            parts = line.split("<", 1)
            mode = "read"
        else:
            self._execute(line)
            return

        cmd_part = parts[0].strip()
        file_part = parts[1].strip() if len(parts) > 1 else ""

        if mode in ("write", "append"):
            # Capture output of command and write to virtual file
            output_lines = []
            orig_print = self._println
            collected = []

            def capture(text, tag=None):
                collected.append(text)
                orig_print(text, tag)

            old = self._println
            self._println = capture
            self._execute(cmd_part)
            self._println = old

            content = "\n".join(collected)
            path_parts = file_part.split("/")
            name = path_parts[-1]
            path = self.cwd + path_parts[:-1] if path_parts[:-1] else self.cwd
            # Create file if needed
            self.kernel.fs.create(path, name)
            if mode == "append":
                ok, existing = self.kernel.fs.read(path + [name])
                content = (existing if ok else "") + content
            self.kernel.fs.write(path + [name], content)
            self._println(f"Output written to '{file_part}'", "info")

        else:  # read
            path_parts = file_part.split("/")
            name = path_parts[-1]
            path = self.cwd + path_parts[:-1] if path_parts[:-1] else self.cwd
            ok, content = self.kernel.fs.read(path + [name])
            if ok:
                self._println(f"[Input from '{file_part}']", "info")
                self._println(content)
            else:
                self._error(f"cannot read '{file_part}': {content}")

    # ------------------------------------------------------------------ #
    # Piping
    # ------------------------------------------------------------------ #
    def _handle_pipe(self, line):
        segments = [s.strip() for s in line.split("|")]
        self._println(f"[Pipe: {' | '.join(segments)}]", "info")
        # Simulate: run each command, feed output of one to next as stdin
        stdin_data = None
        for seg in segments:
            collected = []
            args = seg.split()
            if not args:
                continue
            cmd = args[0]
            rest = args[1:]
            if stdin_data is not None:
                self._println(f"  stdin → {seg}", "warn")
            handler = COMMANDS.get(cmd)
            if handler:
                handler(self, rest)
            else:
                self._error(f"pipe: command not found '{cmd}'")


# ------------------------------------------------------------------ #
# Built-in command implementations
# ------------------------------------------------------------------ #

def cmd_help(term, args):
    term._println("")
    term._println("Available Commands in Kafka Shell:", "prompt")
    term._println("-----------------------------------", "prompt")
    cmds = [
        ("help",               "Show this help menu"),
        ("cd <dir>",           "Change directory in virtual filesystem"),
        ("ls [path]",          "List directory contents"),
        ("pwd",                "Print working directory"),
        ("mkdir <name>",       "Create a directory"),
        ("touch <name>",       "Create an empty file"),
        ("rm <name>",          "Delete a file or empty directory"),
        ("cat <name>",         "Print file contents"),
        ("write <name> <text>","Write text to a file"),
        ("chmod <name> <perm>","Change file permissions"),
        ("find <name>",        "Search for files by name"),
        ("tree",               "Show filesystem tree"),
        ("ps",                 "List all processes"),
        ("spawn <name> <burst>","Spawn a new process"),
        ("kill <pid>",         "Kill a process by PID"),
        ("mem",                "Show memory status"),
        ("memalloc <pid> <sz>","Allocate memory for PID"),
        ("memfree <pid>",      "Free memory for PID"),
        ("memcompact",         "Compact (defragment) memory"),
        ("ipc send <to> <msg>","Send IPC message"),
        ("ipc recv [from]",    "Receive IPC message"),
        ("ipc pipes",          "List IPC pipes"),
        ("history",            "Show command history"),
        ("export <var> <val>", "Set an environment variable"),
        ("unset <var>",        "Unset an environment variable"),
        ("env",                "Show all environment variables"),
        ("echo <text>",        "Print text to terminal"),
        ("whoami",             "Show current user"),
        ("sysinfo",            "Show system information"),
        ("log [level]",        "Show system log"),
        ("devices",            "Show all device statuses"),
        ("clear",              "Clear the terminal"),
        ("fg <job_id>",        "Bring a background job to foreground"),
        ("bg <job_id>",        "Resume a stopped job in background"),
        ("jobs",               "List background jobs"),
        ("exit",               "Exit the shell (closes app)"),
    ]
    for name, desc in cmds:
        term._println(f"  {name:<28} {desc}")
    term._println("-----------------------------------")
    term._println("I/O Redirection: cmd > file  |  cmd >> file  |  cmd < file", "info")
    term._println("Piping         : cmd1 | cmd2 | cmd3", "info")
    term._println("Background     : cmd &", "info")
    term._println("")


def cmd_cd(term, args):
    if not args:
        term._error("cd: expected argument")
        return
    target = args[0]
    if target == "..":
        if term.cwd:
            term.cwd.pop()
        return
    if target == "/":
        term.cwd = []
        return
    # Strip leading slash
    parts = target.strip("/").split("/")
    new_path = list(term.cwd) + parts
    ok, _ = term.kernel.fs.list_dir(new_path)
    if ok:
        term.cwd = new_path
    else:
        term._error(f"cd: no such directory: '{target}'")


def cmd_ls(term, args):
    path = term.cwd
    if args:
        path = term.cwd + args[0].strip("/").split("/")
    ok, entries = term.kernel.fs.list_dir(path)
    if not ok:
        term._error(str(entries))
        return
    if not entries:
        term._println("(empty)", "warn")
        return
    term._println(f"{'NAME':<20}{'TYPE':<6}{'SIZE':<8}{'OWNER':<10}PERMS")
    term._println("-" * 52)
    for e in entries:
        tag = "info" if e["type"] == "DIR" else None
        term._println(f"{e['name']:<20}{e['type']:<6}{str(e['size']):<8}{e['owner']:<10}{e['permissions']}", tag)


def cmd_pwd(term, args):
    cwd_str = "/" + "/".join(term.cwd) if term.cwd else "/"
    term._println(cwd_str, "info")


def cmd_mkdir(term, args):
    if not args:
        term._error("mkdir: expected directory name")
        return
    ok, msg = term.kernel.fs.create_dir(term.cwd, args[0])
    term._println(msg, "success" if ok else "error")
    if ok:
        term.kernel.logger.info(f"mkdir {args[0]}", module="terminal")


def cmd_touch(term, args):
    if not args:
        term._error("touch: expected file name")
        return
    ok, msg = term.kernel.fs.create(term.cwd, args[0], is_file=True)
    term._println(msg, "success" if ok else "error")


def cmd_rm(term, args):
    if not args:
        term._error("rm: expected file name")
        return
    ok, msg = term.kernel.fs.delete(term.cwd + [args[0]])
    term._println(msg, "success" if ok else "error")
    if ok:
        term.kernel.logger.info(f"rm {args[0]}", module="terminal")


def cmd_cat(term, args):
    if not args:
        term._error("cat: expected file name")
        return
    ok, content = term.kernel.fs.read(term.cwd + [args[0]])
    if ok:
        term._println(content if content else "(empty file)", "info")
    else:
        term._error(str(content))


def cmd_write(term, args):
    if len(args) < 2:
        term._error("write: usage: write <filename> <text...>")
        return
    name = args[0]
    content = " ".join(args[1:])
    # Create if not exists
    term.kernel.fs.create(term.cwd, name, is_file=True)
    ok, msg = term.kernel.fs.write(term.cwd + [name], content)
    term._println(msg, "success" if ok else "error")


def cmd_chmod(term, args):
    if len(args) < 2:
        term._error("chmod: usage: chmod <name> <permissions>")
        return
    ok, msg = term.kernel.fs.chmod(term.cwd + [args[0]], args[1])
    term._println(msg, "success" if ok else "error")


def cmd_find(term, args):
    if not args:
        term._error("find: expected search term")
        return
    results = term.kernel.fs.search(args[0])
    if results:
        term._println(f"Found {len(results)} result(s):", "info")
        for r in results:
            term._println(f"  /{r}")
    else:
        term._println("No results found", "warn")


def cmd_tree(term, args):
    lines = term.kernel.fs.tree()
    for line in lines:
        term._println(line)


def cmd_ps(term, args):
    procs = term.kernel.scheduler.process_list
    if not procs:
        term._println("No processes", "warn")
        return
    term._println(f"{'PID':<6}{'NAME':<12}{'BURST':<8}{'WAIT':<8}{'FINISH'}", "info")
    term._println("-" * 40)
    for p in procs:
        term._println(f"{p.pid:<6}{p.name:<12}{p.original_burst:<8}{p.waiting:<8}{p.finish_time or 'running'}")


def cmd_spawn(term, args):
    if len(args) < 2:
        term._error("spawn: usage: spawn <name> <burst>")
        return
    try:
        burst = int(args[1])
    except ValueError:
        term._error("spawn: burst must be an integer")
        return
    pid, p = term.kernel.spawn_process(args[0], burst)
    term._println(f"Process '{p.name}' spawned with PID={pid}, burst={burst}", "success")


def cmd_kill(term, args):
    if not args:
        term._error("kill: expected PID")
        return
    try:
        pid = int(args[0])
    except ValueError:
        term._error("kill: PID must be an integer")
        return
    result = term.kernel.kill_process(pid)
    if not result["found"]:
        term._error(f"kill: no such process with PID {pid}")
        return
    mem_msg = "memory freed" if result["memory_freed"] else "no memory to free"
    term._println(f"PID {pid} killed ({mem_msg})", "success")


def cmd_mem(term, args):
    summ = term.kernel.memory.summary()
    term._println(f"Memory: total={summ['total']} | used={summ['used']} ({summ['used_pct']}%) | free={summ['free']}", "info")
    term._println("Allocations:")
    for pid, blk in summ["allocations"].items():
        term._println(f"  PID {pid}: start={blk['start']}, size={blk['size']}")
    term._println("Free blocks:")
    for start, size in summ["free_blocks"]:
        term._println(f"  start={start}, size={size}")


def cmd_memalloc(term, args):
    if len(args) < 2:
        term._error("memalloc: usage: memalloc <pid> <size>")
        return
    try:
        pid, size = int(args[0]), int(args[1])
    except ValueError:
        term._error("memalloc: pid and size must be integers")
        return
    addr = term.kernel.memory.allocate(pid, size)
    if addr == -1:
        term._println(f"Allocation failed for PID {pid} size={size}: no free space", "error")
    else:
        term._println(f"PID {pid} allocated {size} units at address {addr}", "success")


def cmd_memfree(term, args):
    if not args:
        term._error("memfree: expected PID")
        return
    try:
        pid = int(args[0])
    except ValueError:
        return
    ok = term.kernel.memory.deallocate(pid)
    term._println(f"PID {pid} memory freed", "success" if ok else "error")


def cmd_memcompact(term, args):
    term.kernel.memory.compact()
    term._println("Memory compacted (defragmented)", "success")


def cmd_ipc(term, args):
    if not args:
        term._error("ipc: subcommand required: send, recv, pipes, shm")
        return
    sub = args[0]
    if sub == "send":
        if len(args) < 3:
            term._error("ipc send: usage: ipc send <receiver> <message>")
            return
        receiver = args[1]
        msg = " ".join(args[2:])
        term.kernel.ipc.send(msg, sender="terminal", receiver=receiver)
        term._println(f"Message sent to '{receiver}': {msg}", "success")
    elif sub == "recv":
        receiver = args[1] if len(args) > 1 else None
        msg = term.kernel.ipc.receive(receiver)
        if msg:
            term._println(f"Received from '{msg['sender']}': {msg['msg']}", "info")
        else:
            term._println("No messages", "warn")
    elif sub == "pipes":
        status = term.kernel.ipc.status()
        for name, info in status["pipes"].items():
            term._println(f"  {name}: size={info['size']}, closed={info['closed']}", "info")
    elif sub == "shm":
        status = term.kernel.ipc.status()
        for name, data in status["shared_memories"].items():
            term._println(f"  {name}: {data}", "info")
    else:
        term._error(f"ipc: unknown subcommand '{sub}'")


def cmd_history(term, args):
    if not term.history:
        term._println("No history", "warn")
        return
    term._println("Command History:", "info")
    for i, cmd in enumerate(term.history, 1):
        term._println(f"  {i:>3}  {cmd}")


def cmd_export(term, args):
    if len(args) < 2:
        term._error("export: usage: export <VAR> <value>")
        return
    term.env_vars[args[0]] = " ".join(args[1:])
    term._println(f"${args[0]} = '{term.env_vars[args[0]]}'", "success")
    term.kernel.logger.info(f"export {args[0]}={term.env_vars[args[0]]}", module="terminal")


def cmd_unset(term, args):
    if not args:
        term._error("unset: expected variable name")
        return
    if args[0] in term.env_vars:
        del term.env_vars[args[0]]
        term._println(f"${args[0]} unset", "success")
    else:
        term._println(f"${args[0]}: not set", "warn")


def cmd_env(term, args):
    if not term.env_vars:
        term._println("(no env vars set)", "warn")
        return
    for k, v in term.env_vars.items():
        term._println(f"  {k}={v}", "info")


def cmd_echo(term, args):
    text = " ".join(args)
    # Expand $VAR
    for k, v in term.env_vars.items():
        text = text.replace(f"${k}", v)
    term._println(text)


def cmd_whoami(term, args):
    term._println(term.kernel.security.sessions.get(
        next(iter(term.kernel.security.sessions), ""),
        "unknown"
    ), "info")


def cmd_sysinfo(term, args):
    status = term.kernel.system_status()
    term._println("=== System Information ===", "prompt")
    term._println(f"  OS      : {status['os']} v{status['version']}", "info")
    term._println(f"  Boot    : {status['boot_time']}")
    mem = status["memory"]
    term._println(f"  Memory  : {mem['used']}/{mem['total']} used ({mem['used_pct']}%)")
    devs = status["devices"]
    term._println(f"  Devices : {', '.join(devs.keys())}")
    logs = status["log_summary"]
    errs = logs.get("ERROR", 0) + logs.get("CRITICAL", 0)
    term._println(f"  Errors  : {errs}", "error" if errs else None)


def cmd_log(term, args):
    level = args[0].upper() if args else None
    entries = term.kernel.logger.get_entries(level=level, limit=30)
    if not entries:
        term._println("No log entries", "warn")
        return
    tags = {
        "DEBUG": None, "INFO": "info", "WARNING": "warn",
        "ERROR": "error", "CRITICAL": "error"
    }
    for e in entries:
        tag = tags.get(e["level"])
        term._println(f"[{e['timestamp']}] [{e['level']:<8}] [{e['module']:<10}] {e['msg']}", tag)


def cmd_devices(term, args):
    status = term.kernel.driver.all_status()
    term._println("=== Devices ===", "info")
    for dev, info in status.items():
        connected = info.get("connected", "?")
        tag = "success" if connected else "error"
        term._println(f"  {dev:<12}: connected={connected}  {info}", tag)


def cmd_clear(term, args):
    term.output.config(state="normal")
    term.output.delete("1.0", "end")
    term.output.config(state="disabled")
    term._print(term.BANNER)


def cmd_fg(term, args):
    if not args:
        term._println("Usage: fg <job_id>", "warn")
        return
    try:
        jid = int(args[0])
    except ValueError:
        return
    job = next((j for j in term.jobs if j["id"] == jid), None)
    if job:
        job["status"] = "running"
        term._println(f"Foreground job [{jid}]: {job['cmd']}", "info")
    else:
        term._println(f"No such job [{jid}]", "error")


def cmd_bg(term, args):
    if not args:
        term._println("Usage: bg <job_id>", "warn")
        return
    try:
        jid = int(args[0])
    except ValueError:
        return
    job = next((j for j in term.jobs if j["id"] == jid), None)
    if job:
        job["status"] = "running"
        term._println(f"Resuming job [{jid}] in background: {job['cmd']}", "info")
    else:
        term._println(f"No such job [{jid}]", "error")


def cmd_jobs(term, args):
    if not term.jobs:
        term._println("No background jobs", "warn")
        return
    for j in term.jobs:
        term._println(f"  [{j['id']}] {j['status']:<10} {j['cmd']}", "info")


def cmd_exit(term, args):
    term._println("Goodbye from Kafka Shell!", "warn")
    term.kernel.logger.info("Shell exit", module="terminal")
    term.frame.winfo_toplevel().quit()


# ------------------------------------------------------------------ #
# Command registry
# ------------------------------------------------------------------ #
COMMANDS = {
    "help":       cmd_help,
    "cd":         cmd_cd,
    "ls":         cmd_ls,
    "pwd":        cmd_pwd,
    "mkdir":      cmd_mkdir,
    "touch":      cmd_touch,
    "rm":         cmd_rm,
    "cat":        cmd_cat,
    "write":      cmd_write,
    "chmod":      cmd_chmod,
    "find":       cmd_find,
    "tree":       cmd_tree,
    "ps":         cmd_ps,
    "spawn":      cmd_spawn,
    "kill":       cmd_kill,
    "mem":        cmd_mem,
    "memalloc":   cmd_memalloc,
    "memfree":    cmd_memfree,
    "memcompact": cmd_memcompact,
    "ipc":        cmd_ipc,
    "history":    cmd_history,
    "export":     cmd_export,
    "unset":      cmd_unset,
    "env":        cmd_env,
    "echo":       cmd_echo,
    "whoami":     cmd_whoami,
    "sysinfo":    cmd_sysinfo,
    "log":        cmd_log,
    "devices":    cmd_devices,
    "clear":      cmd_clear,
    "fg":         cmd_fg,
    "bg":         cmd_bg,
    "jobs":       cmd_jobs,
    "exit":       cmd_exit,
}
