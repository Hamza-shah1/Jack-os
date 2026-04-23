import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import threading

from modules.scheduler import Process
from gui.terminal import TerminalTab


class LoginWindow:
    """Login dialog shown on startup."""

    def __init__(self, kernel, on_success):
        self.kernel = kernel
        self.on_success = on_success
        self.token = None

        self.win = tk.Toplevel()
        self.win.title("Jack OS — Login")
        self.win.geometry("360x280")
        self.win.resizable(False, False)
        self.win.configure(bg="#1e1e2e")
        self.win.grab_set()

        tk.Label(self.win, text="Jack OS", font=("Courier", 22, "bold"),
                 bg="#1e1e2e", fg="#cba6f7").pack(pady=(20, 5))
        tk.Label(self.win, text="Secure Login", font=("Arial", 10),
                 bg="#1e1e2e", fg="#a6adc8").pack()

        frame = tk.Frame(self.win, bg="#1e1e2e")
        frame.pack(pady=20)

        tk.Label(frame, text="Username:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=8, pady=6)
        self.user_entry = tk.Entry(frame, width=20, font=("Arial", 10))
        self.user_entry.grid(row=0, column=1, pady=6)
        self.user_entry.insert(0, "admin")

        tk.Label(frame, text="Password:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.pass_entry = tk.Entry(frame, width=20, show="*", font=("Arial", 10))
        self.pass_entry.grid(row=1, column=1, pady=6)
        self.pass_entry.insert(0, "admin123")

        self.status_label = tk.Label(self.win, text="", bg="#1e1e2e", fg="#f38ba8",
                                     font=("Arial", 9))
        self.status_label.pack()

        btn = tk.Button(self.win, text="Login", font=("Arial", 11, "bold"),
                        bg="#cba6f7", fg="#1e1e2e", width=12,
                        command=self._do_login)
        btn.pack(pady=10)

        self.win.bind("<Return>", lambda e: self._do_login())
        self.pass_entry.focus()

    def _do_login(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        ok, result = self.kernel.security.login(u, p)
        if ok:
            self.token = result
            self.win.destroy()
            self.on_success(self.token, u)
        else:
            self.status_label.config(text=result)


class SchedulerTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        ctrl = tk.Frame(f, bg="#313244")
        ctrl.pack(fill="x", padx=10, pady=8)

        tk.Label(ctrl, text="Process Name:", bg="#313244", fg="#cdd6f4").grid(row=0, column=0, padx=5)
        self.name_var = tk.StringVar(value="P")
        tk.Entry(ctrl, textvariable=self.name_var, width=8).grid(row=0, column=1, padx=4)

        tk.Label(ctrl, text="Burst Time:", bg="#313244", fg="#cdd6f4").grid(row=0, column=2, padx=5)
        self.burst_var = tk.StringVar(value="5")
        tk.Entry(ctrl, textvariable=self.burst_var, width=6).grid(row=0, column=3, padx=4)

        tk.Label(ctrl, text="Priority:", bg="#313244", fg="#cdd6f4").grid(row=0, column=4, padx=5)
        self.prio_var = tk.StringVar(value="0")
        tk.Entry(ctrl, textvariable=self.prio_var, width=5).grid(row=0, column=5, padx=4)

        tk.Button(ctrl, text="Add Process", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._add_process).grid(row=0, column=6, padx=8)

        algo_frame = tk.Frame(f, bg="#313244")
        algo_frame.pack(fill="x", padx=10, pady=2)
        tk.Label(algo_frame, text="Algorithm:", bg="#313244", fg="#cdd6f4").pack(side="left", padx=5)
        self.algo_var = tk.StringVar(value="Round Robin")
        for algo in ["Round Robin", "FCFS", "SJF"]:
            tk.Radiobutton(algo_frame, text=algo, variable=self.algo_var, value=algo,
                           bg="#313244", fg="#cdd6f4", selectcolor="#45475a").pack(side="left", padx=5)

        tk.Label(algo_frame, text="Quantum:", bg="#313244", fg="#cdd6f4").pack(side="left", padx=8)
        self.quantum_var = tk.StringVar(value="2")
        tk.Entry(algo_frame, textvariable=self.quantum_var, width=4).pack(side="left")

        btn_frame = tk.Frame(f)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Run Scheduler", bg="#cba6f7", fg="#1e1e2e",
                  font=("Arial", 10, "bold"), command=self._run_scheduler).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Reset", bg="#f38ba8", fg="#1e1e2e",
                  command=self._reset).pack(side="left", padx=6)

        # Process table
        cols = ("Name", "Burst", "Priority", "Waiting", "Turnaround", "Finish")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=5)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        self.tree.pack(fill="x", padx=10, pady=4)

        # Log output
        self.log_text = scrolledtext.ScrolledText(f, height=12, bg="#1e1e2e", fg="#a6e3a1",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=4)

    def _add_process(self):
        try:
            burst = int(self.burst_var.get())
            prio = int(self.prio_var.get())
        except ValueError:
            messagebox.showerror("Error", "Burst and priority must be integers")
            return
        name = self.name_var.get().strip() or "P"
        pid = self.kernel.next_pid()
        p = Process(pid, burst, priority=prio, name=f"{name}{pid}")
        self.kernel.scheduler.add(p)
        size = max(2, burst // 2)
        self.kernel.memory.allocate(pid, size)
        self.kernel.logger.info(f"Process {p.name} added (burst={burst})", module="scheduler")
        self._refresh_table()
        self.log_text.insert("end", f"Added {p.name} burst={burst} prio={prio}\n")
        self.log_text.see("end")

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for p in self.kernel.scheduler.process_list:
            self.tree.insert("", "end", values=(
                p.name, p.original_burst, p.priority,
                p.waiting, p.turnaround, p.finish_time or "-"
            ))

    def _run_scheduler(self):
        if not self.kernel.scheduler.queue:
            messagebox.showwarning("Warning", "No processes in queue. Add some first.")
            return
        try:
            self.kernel.scheduler.quantum = int(self.quantum_var.get())
        except ValueError:
            pass

        self.log_text.insert("end", f"\n--- Running {self.algo_var.get()} ---\n")

        def do_run():
            algo = self.algo_var.get()
            if algo == "Round Robin":
                log, gantt, stats = self.kernel.scheduler.run_round_robin(delay=0)
            elif algo == "FCFS":
                log, gantt, stats = self.kernel.scheduler.run_fcfs(delay=0)
            else:
                log, gantt, stats = self.kernel.scheduler.run_sjf(delay=0)

            self.log_text.insert("end", "\n".join(log) + "\n")
            self.log_text.see("end")
            self._refresh_table()
            self.kernel.logger.info(
                f"Scheduler completed ({algo}): avg_wait={stats['avg_waiting']:.2f}",
                module="scheduler"
            )

        threading.Thread(target=do_run, daemon=True).start()

    def _reset(self):
        self.kernel.scheduler.reset()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.log_text.insert("end", "\n[Reset]\n")


class MemoryTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        ctrl = tk.Frame(f, bg="#313244")
        ctrl.pack(fill="x", padx=10, pady=8)

        tk.Label(ctrl, text="PID:", bg="#313244", fg="#cdd6f4").grid(row=0, column=0, padx=5)
        self.pid_var = tk.StringVar(value="10")
        tk.Entry(ctrl, textvariable=self.pid_var, width=6).grid(row=0, column=1)

        tk.Label(ctrl, text="Size:", bg="#313244", fg="#cdd6f4").grid(row=0, column=2, padx=5)
        self.size_var = tk.StringVar(value="8")
        tk.Entry(ctrl, textvariable=self.size_var, width=6).grid(row=0, column=3)

        tk.Button(ctrl, text="Allocate (First Fit)", bg="#a6e3a1", fg="#1e1e2e",
                  command=lambda: self._alloc("first")).grid(row=0, column=4, padx=4)
        tk.Button(ctrl, text="Allocate (Best Fit)", bg="#89b4fa", fg="#1e1e2e",
                  command=lambda: self._alloc("best")).grid(row=0, column=5, padx=4)
        tk.Button(ctrl, text="Deallocate", bg="#f38ba8", fg="#1e1e2e",
                  command=self._dealloc).grid(row=0, column=6, padx=4)
        tk.Button(ctrl, text="Compact", bg="#fab387", fg="#1e1e2e",
                  command=self._compact).grid(row=0, column=7, padx=4)

        # Canvas for memory visualization
        self.canvas = tk.Canvas(f, height=60, bg="#1e1e2e")
        self.canvas.pack(fill="x", padx=10, pady=6)

        self.info_text = scrolledtext.ScrolledText(f, height=14, bg="#1e1e2e", fg="#89dceb",
                                                   font=("Courier", 9))
        self.info_text.pack(fill="both", expand=True, padx=10, pady=4)

        self._refresh()

    def _alloc(self, method):
        try:
            pid = int(self.pid_var.get())
            size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Error", "PID and size must be integers")
            return
        if method == "first":
            addr = self.kernel.memory.allocate(pid, size)
        else:
            addr = self.kernel.memory.best_fit(pid, size)
        if addr == -1:
            self.info_text.insert("end", f"[FAIL] Cannot allocate PID={pid} size={size} — no space\n")
        else:
            self.info_text.insert("end", f"[OK] PID={pid} allocated {size} units at addr {addr}\n")
            self.kernel.logger.info(f"Memory allocated PID={pid} size={size} addr={addr}", module="memory")
        self.info_text.see("end")
        self._refresh()

    def _dealloc(self):
        try:
            pid = int(self.pid_var.get())
        except ValueError:
            return
        freed = self.kernel.memory.deallocate(pid)
        msg = f"[OK] PID={pid} freed\n" if freed else f"[FAIL] PID={pid} not found\n"
        self.info_text.insert("end", msg)
        self.info_text.see("end")
        self.kernel.logger.info(f"Memory deallocated PID={pid}", module="memory")
        self._refresh()

    def _compact(self):
        self.kernel.memory.compact()
        self.info_text.insert("end", "[OK] Memory compacted (defragmented)\n")
        self.info_text.see("end")
        self._refresh()

    def _refresh(self):
        mem = self.kernel.memory.status()
        summ = self.kernel.memory.summary()

        # Draw canvas
        self.canvas.delete("all")
        self.canvas.update_idletasks()
        w = self.canvas.winfo_width() or 600
        cell_w = max(1, w / len(mem))
        colors = {}
        color_cycle = ["#cba6f7", "#89b4fa", "#a6e3a1", "#fab387", "#f38ba8", "#89dceb", "#f9e2af"]
        for i, pid in enumerate(mem):
            if pid is not None and pid not in colors:
                colors[pid] = color_cycle[len(colors) % len(color_cycle)]
            x0, x1 = i * cell_w, (i + 1) * cell_w
            fill = colors.get(pid, "#313244") if pid else "#1e1e2e"
            self.canvas.create_rectangle(x0, 5, x1, 55, fill=fill, outline="#45475a")

        # Legend
        legend_x = 10
        for pid, color in colors.items():
            self.canvas.create_rectangle(legend_x, 8, legend_x + 14, 22, fill=color, outline="")
            self.canvas.create_text(legend_x + 18, 15, text=f"P{pid}", fill="#cdd6f4",
                                    anchor="w", font=("Arial", 7))
            legend_x += 50

        self.info_text.delete("1.0", "end")
        self.info_text.insert("end", f"Total: {summ['total']} | Used: {summ['used']} ({summ['used_pct']}%) | Free: {summ['free']} ({100 - summ['used_pct']}%)\n\n")
        self.info_text.insert("end", "Allocations:\n")
        for pid, block in summ["allocations"].items():
            self.info_text.insert("end", f"  PID {pid:>4}: start={block['start']}, size={block['size']}\n")
        self.info_text.insert("end", "\nFree Blocks:\n")
        for start, size in summ["free_blocks"]:
            self.info_text.insert("end", f"  start={start}, size={size}\n")


class FileSystemTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._current_path = []
        self._build()

    def _build(self):
        f = self.frame

        path_frame = tk.Frame(f, bg="#313244")
        path_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(path_frame, text="Path (space-sep):", bg="#313244", fg="#cdd6f4").pack(side="left", padx=4)
        self.path_var = tk.StringVar()
        tk.Entry(path_frame, textvariable=self.path_var, width=20).pack(side="left", padx=4)
        tk.Label(path_frame, text="Name:", bg="#313244", fg="#cdd6f4").pack(side="left", padx=4)
        self.name_var = tk.StringVar()
        tk.Entry(path_frame, textvariable=self.name_var, width=14).pack(side="left", padx=4)

        btn_frame = tk.Frame(f)
        btn_frame.pack(fill="x", padx=10, pady=4)
        for label, cmd in [
            ("Create File", self._create_file),
            ("Create Dir", self._create_dir),
            ("Delete", self._delete),
            ("List Dir", self._list_dir),
        ]:
            tk.Button(btn_frame, text=label, bg="#89b4fa", fg="#1e1e2e",
                      command=cmd).pack(side="left", padx=4)

        content_frame = tk.Frame(f, bg="#313244")
        content_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(content_frame, text="Content:", bg="#313244", fg="#cdd6f4").pack(side="left", padx=4)
        self.content_var = tk.StringVar()
        tk.Entry(content_frame, textvariable=self.content_var, width=40).pack(side="left", padx=4)
        tk.Button(content_frame, text="Write File", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._write_file).pack(side="left", padx=4)
        tk.Button(content_frame, text="Read File", bg="#fab387", fg="#1e1e2e",
                  command=self._read_file).pack(side="left", padx=4)

        tk.Label(f, text="Search:").pack(anchor="w", padx=12)
        search_frame = tk.Frame(f)
        search_frame.pack(fill="x", padx=10)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side="left", padx=4)
        tk.Button(search_frame, text="Search", bg="#cba6f7", fg="#1e1e2e",
                  command=self._search).pack(side="left")
        tk.Button(search_frame, text="Show Tree", bg="#f9e2af", fg="#1e1e2e",
                  command=self._show_tree).pack(side="left", padx=6)

        self.log_text = scrolledtext.ScrolledText(f, height=14, bg="#1e1e2e", fg="#a6e3a1",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=4)

    def _path(self):
        raw = self.path_var.get().strip()
        return raw.split() if raw else []

    def _create_file(self):
        ok, msg = self.kernel.fs.create(self._path(), self.name_var.get().strip())
        self._log(msg)
        self.kernel.logger.info(msg, module="fs")

    def _create_dir(self):
        ok, msg = self.kernel.fs.create_dir(self._path(), self.name_var.get().strip())
        self._log(msg)

    def _delete(self):
        full = self._path() + ([self.name_var.get().strip()] if self.name_var.get().strip() else [])
        ok, msg = self.kernel.fs.delete(full)
        self._log(msg)
        self.kernel.logger.info(msg, module="fs")

    def _list_dir(self):
        ok, entries = self.kernel.fs.list_dir(self._path())
        if not ok:
            self._log(str(entries))
            return
        if not entries:
            self._log("(empty directory)")
            return
        self._log("NAME".ljust(20) + "TYPE".ljust(6) + "SIZE".ljust(8) + "OWNER".ljust(10) + "PERMS")
        for e in entries:
            self._log(f"{e['name']:<20}{e['type']:<6}{str(e['size']):<8}{e['owner']:<10}{e['permissions']}")

    def _write_file(self):
        full = self._path() + ([self.name_var.get().strip()] if self.name_var.get().strip() else [])
        ok, msg = self.kernel.fs.write(full, self.content_var.get())
        self._log(msg)

    def _read_file(self):
        full = self._path() + ([self.name_var.get().strip()] if self.name_var.get().strip() else [])
        ok, content = self.kernel.fs.read(full)
        self._log(content if ok else content)

    def _search(self):
        results = self.kernel.fs.search(self.search_var.get())
        if results:
            self._log("Search results:")
            for r in results:
                self._log(f"  {r}")
        else:
            self._log("No results found")

    def _show_tree(self):
        lines = self.kernel.fs.tree()
        self._log("\n=== File System Tree ===")
        for line in lines:
            self._log(line)

    def _log(self, msg):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")


class IPCTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        mq_frame = tk.LabelFrame(f, text="Message Queue", bg="#313244", fg="#cba6f7", padx=6, pady=6)
        mq_frame.pack(fill="x", padx=10, pady=6)

        tk.Label(mq_frame, text="From:", bg="#313244", fg="#cdd6f4").grid(row=0, column=0)
        self.sender_var = tk.StringVar(value="P1")
        tk.Entry(mq_frame, textvariable=self.sender_var, width=8).grid(row=0, column=1, padx=4)
        tk.Label(mq_frame, text="To:", bg="#313244", fg="#cdd6f4").grid(row=0, column=2)
        self.recv_var = tk.StringVar(value="P2")
        tk.Entry(mq_frame, textvariable=self.recv_var, width=8).grid(row=0, column=3, padx=4)
        tk.Label(mq_frame, text="Msg:", bg="#313244", fg="#cdd6f4").grid(row=0, column=4)
        self.msg_var = tk.StringVar(value="Hello")
        tk.Entry(mq_frame, textvariable=self.msg_var, width=16).grid(row=0, column=5, padx=4)
        tk.Button(mq_frame, text="Send", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._send_msg).grid(row=0, column=6, padx=4)
        tk.Button(mq_frame, text="Receive", bg="#fab387", fg="#1e1e2e",
                  command=self._recv_msg).grid(row=0, column=7, padx=4)

        pipe_frame = tk.LabelFrame(f, text="Pipes", bg="#313244", fg="#89b4fa", padx=6, pady=6)
        pipe_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(pipe_frame, text="Pipe Name:", bg="#313244", fg="#cdd6f4").grid(row=0, column=0)
        self.pipe_name_var = tk.StringVar(value="my_pipe")
        tk.Entry(pipe_frame, textvariable=self.pipe_name_var, width=10).grid(row=0, column=1, padx=4)
        tk.Label(pipe_frame, text="Data:", bg="#313244", fg="#cdd6f4").grid(row=0, column=2)
        self.pipe_data_var = tk.StringVar(value="data_block")
        tk.Entry(pipe_frame, textvariable=self.pipe_data_var, width=16).grid(row=0, column=3, padx=4)
        tk.Button(pipe_frame, text="Create Pipe", bg="#89b4fa", fg="#1e1e2e",
                  command=self._create_pipe).grid(row=0, column=4, padx=3)
        tk.Button(pipe_frame, text="Write", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._pipe_write).grid(row=0, column=5, padx=3)
        tk.Button(pipe_frame, text="Read", bg="#fab387", fg="#1e1e2e",
                  command=self._pipe_read).grid(row=0, column=6, padx=3)

        shm_frame = tk.LabelFrame(f, text="Shared Memory", bg="#313244", fg="#f9e2af", padx=6, pady=6)
        shm_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(shm_frame, text="Region:", bg="#313244", fg="#cdd6f4").grid(row=0, column=0)
        self.shm_name_var = tk.StringVar(value="sys_shm")
        tk.Entry(shm_frame, textvariable=self.shm_name_var, width=10).grid(row=0, column=1, padx=4)
        tk.Label(shm_frame, text="Key:", bg="#313244", fg="#cdd6f4").grid(row=0, column=2)
        self.shm_key_var = tk.StringVar(value="counter")
        tk.Entry(shm_frame, textvariable=self.shm_key_var, width=10).grid(row=0, column=3, padx=4)
        tk.Label(shm_frame, text="Value:", bg="#313244", fg="#cdd6f4").grid(row=0, column=4)
        self.shm_val_var = tk.StringVar(value="42")
        tk.Entry(shm_frame, textvariable=self.shm_val_var, width=10).grid(row=0, column=5, padx=4)
        tk.Button(shm_frame, text="Create SHM", bg="#f9e2af", fg="#1e1e2e",
                  command=self._create_shm).grid(row=0, column=6, padx=3)
        tk.Button(shm_frame, text="Write", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._shm_write).grid(row=0, column=7, padx=3)
        tk.Button(shm_frame, text="Read", bg="#fab387", fg="#1e1e2e",
                  command=self._shm_read).grid(row=0, column=8, padx=3)

        tk.Button(f, text="Show IPC Status", bg="#cba6f7", fg="#1e1e2e",
                  command=self._show_status).pack(pady=6)

        self.log_text = scrolledtext.ScrolledText(f, height=12, bg="#1e1e2e", fg="#89dceb",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=4)

    def _log(self, msg):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")

    def _send_msg(self):
        self.kernel.ipc.send(self.msg_var.get(), self.sender_var.get(), self.recv_var.get())
        self._log(f"MSG sent: {self.sender_var.get()} → {self.recv_var.get()}: '{self.msg_var.get()}'")
        self.kernel.logger.info(f"IPC msg: {self.msg_var.get()}", module="ipc")

    def _recv_msg(self):
        msg = self.kernel.ipc.receive(self.recv_var.get())
        self._log(f"MSG received: {msg}" if msg else "No messages")

    def _create_pipe(self):
        ok, msg = self.kernel.ipc.create_pipe(self.pipe_name_var.get())
        self._log(msg)

    def _pipe_write(self):
        ok, msg = self.kernel.ipc.pipe_write(self.pipe_name_var.get(), self.pipe_data_var.get())
        self._log(msg)

    def _pipe_read(self):
        data = self.kernel.ipc.pipe_read(self.pipe_name_var.get())
        self._log(f"Read from pipe: {data}" if data else "Pipe empty")

    def _create_shm(self):
        ok, msg = self.kernel.ipc.create_shared_memory(self.shm_name_var.get())
        self._log(msg)

    def _shm_write(self):
        ok, msg = self.kernel.ipc.shm_write(
            self.shm_name_var.get(), self.shm_key_var.get(), self.shm_val_var.get()
        )
        self._log(f"SHM[{self.shm_name_var.get()}][{self.shm_key_var.get()}] = '{self.shm_val_var.get()}'")

    def _shm_read(self):
        val = self.kernel.ipc.shm_read(self.shm_name_var.get(), self.shm_key_var.get())
        self._log(f"SHM[{self.shm_name_var.get()}][{self.shm_key_var.get()}] = {val}")

    def _show_status(self):
        s = self.kernel.ipc.status()
        self._log(f"\n=== IPC Status ===\n{s}\n")


class SecurityTab:
    def __init__(self, parent, kernel, token, username):
        self.kernel = kernel
        self.token = token
        self.username = username
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        tk.Label(f, text=f"Logged in as: {self.username}", font=("Arial", 11, "bold"),
                 fg="#a6e3a1").pack(pady=6)

        reg_frame = tk.LabelFrame(f, text="Register New User", padx=6, pady=6)
        reg_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(reg_frame, text="Username:").grid(row=0, column=0)
        self.reg_user = tk.StringVar()
        tk.Entry(reg_frame, textvariable=self.reg_user, width=12).grid(row=0, column=1, padx=4)
        tk.Label(reg_frame, text="Password:").grid(row=0, column=2)
        self.reg_pass = tk.StringVar()
        tk.Entry(reg_frame, textvariable=self.reg_pass, show="*", width=12).grid(row=0, column=3, padx=4)
        tk.Label(reg_frame, text="Role:").grid(row=0, column=4)
        self.reg_role = tk.StringVar(value="user")
        ttk.Combobox(reg_frame, textvariable=self.reg_role, values=["user", "guest", "admin"],
                     width=8).grid(row=0, column=5, padx=4)
        tk.Button(reg_frame, text="Register", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._register).grid(row=0, column=6, padx=6)

        action_frame = tk.Frame(f)
        action_frame.pack(fill="x", padx=10, pady=4)
        tk.Button(action_frame, text="List Users (Admin)", bg="#89b4fa", fg="#1e1e2e",
                  command=self._list_users).pack(side="left", padx=4)
        tk.Button(action_frame, text="View Audit Log", bg="#cba6f7", fg="#1e1e2e",
                  command=self._audit_log).pack(side="left", padx=4)

        unlock_frame = tk.LabelFrame(f, text="Unlock User (Admin)", padx=6, pady=4)
        unlock_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(unlock_frame, text="Username:").grid(row=0, column=0)
        self.unlock_user = tk.StringVar()
        tk.Entry(unlock_frame, textvariable=self.unlock_user, width=14).grid(row=0, column=1, padx=4)
        tk.Button(unlock_frame, text="Unlock", bg="#fab387", fg="#1e1e2e",
                  command=self._unlock).grid(row=0, column=2, padx=6)

        self.log_text = scrolledtext.ScrolledText(f, height=14, bg="#1e1e2e", fg="#f9e2af",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=4)

    def _log(self, msg):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")

    def _register(self):
        ok, msg = self.kernel.security.register(
            self.reg_user.get(), self.reg_pass.get(), self.reg_role.get()
        )
        self._log(msg)

    def _list_users(self):
        ok, result = self.kernel.security.list_users(self.token)
        if not ok:
            self._log(result)
            return
        self._log("\n=== Users ===")
        for u in result:
            self._log(f"  {u['username']:<12} role={u['role']:<8} locked={u['locked']} last_login={u['last_login']}")

    def _audit_log(self):
        ok, log = self.kernel.security.get_audit_log(self.token)
        if not ok:
            self._log(log)
            return
        self._log("\n=== Audit Log ===")
        for entry in log:
            self._log(f"  [{entry['time']}] {entry['event']}")

    def _unlock(self):
        ok, msg = self.kernel.security.unlock_user(self.token, self.unlock_user.get())
        self._log(msg)


class LoggerTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        ctrl = tk.Frame(f, bg="#313244")
        ctrl.pack(fill="x", padx=10, pady=6)

        tk.Label(ctrl, text="Level Filter:", bg="#313244", fg="#cdd6f4").pack(side="left", padx=4)
        self.level_var = tk.StringVar(value="ALL")
        ttk.Combobox(ctrl, textvariable=self.level_var,
                     values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                     width=10).pack(side="left")
        tk.Label(ctrl, text="Module:", bg="#313244", fg="#cdd6f4").pack(side="left", padx=8)
        self.mod_var = tk.StringVar()
        tk.Entry(ctrl, textvariable=self.mod_var, width=12).pack(side="left")
        tk.Button(ctrl, text="Refresh", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._refresh).pack(side="left", padx=8)
        tk.Button(ctrl, text="Clear Log", bg="#f38ba8", fg="#1e1e2e",
                  command=self._clear).pack(side="left")

        add_frame = tk.LabelFrame(f, text="Add Log Entry", padx=6, pady=4)
        add_frame.pack(fill="x", padx=10, pady=4)
        self.log_level_var = tk.StringVar(value="INFO")
        ttk.Combobox(add_frame, textvariable=self.log_level_var,
                     values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                     width=10).grid(row=0, column=0, padx=4)
        self.log_msg_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=self.log_msg_var, width=40).grid(row=0, column=1, padx=4)
        self.log_mod_var = tk.StringVar(value="user")
        tk.Entry(add_frame, textvariable=self.log_mod_var, width=10).grid(row=0, column=2, padx=4)
        tk.Button(add_frame, text="Log", bg="#89b4fa", fg="#1e1e2e",
                  command=self._add_log).grid(row=0, column=3, padx=4)

        summ_frame = tk.Frame(f)
        summ_frame.pack(fill="x", padx=10, pady=2)
        self.summ_label = tk.Label(summ_frame, text="", font=("Courier", 9), fg="#89dceb")
        self.summ_label.pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(f, height=16, bg="#1e1e2e", fg="#cdd6f4",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=4)

        self._refresh()

    def _refresh(self):
        level = self.level_var.get() if self.level_var.get() != "ALL" else None
        mod = self.mod_var.get().strip() or None
        entries = self.kernel.logger.get_entries(level=level, module=mod, limit=200)
        self.log_text.delete("1.0", "end")
        colors = {
            "DEBUG": "#6c7086", "INFO": "#a6e3a1", "WARNING": "#f9e2af",
            "ERROR": "#f38ba8", "CRITICAL": "#ff5555",
        }
        for e in entries:
            line = f"[{e['timestamp']}] [{e['level']:<8}] [{e['module']:<12}] {e['msg']}\n"
            self.log_text.insert("end", line)
        self.log_text.see("end")
        summ = self.kernel.logger.summary()
        self.summ_label.config(
            text="  ".join(f"{k}:{v}" for k, v in summ.items() if v > 0)
        )

    def _clear(self):
        self.kernel.logger.clear()
        self._refresh()

    def _add_log(self):
        lvl = self.log_level_var.get().lower()
        msg = self.log_msg_var.get()
        mod = self.log_mod_var.get()
        getattr(self.kernel.logger, lvl)(msg, module=mod)
        self._refresh()


class DevicesTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        kb_frame = tk.LabelFrame(f, text="Keyboard", padx=6, pady=4)
        kb_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(kb_frame, text="Key/Data:").grid(row=0, column=0)
        self.kb_var = tk.StringVar(value="A")
        tk.Entry(kb_frame, textvariable=self.kb_var, width=12).grid(row=0, column=1, padx=4)
        tk.Button(kb_frame, text="Press Key", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._press_key).grid(row=0, column=2, padx=4)
        tk.Button(kb_frame, text="Read Buffer", bg="#fab387", fg="#1e1e2e",
                  command=self._read_kb).grid(row=0, column=3, padx=4)

        disp_frame = tk.LabelFrame(f, text="Display", padx=6, pady=4)
        disp_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(disp_frame, text="Output:").grid(row=0, column=0)
        self.disp_var = tk.StringVar(value="Hello OS!")
        tk.Entry(disp_frame, textvariable=self.disp_var, width=30).grid(row=0, column=1, padx=4)
        tk.Button(disp_frame, text="Print to Display", bg="#89b4fa", fg="#1e1e2e",
                  command=self._print_display).grid(row=0, column=2, padx=4)
        tk.Button(disp_frame, text="Show Screen", bg="#cba6f7", fg="#1e1e2e",
                  command=self._show_screen).grid(row=0, column=3)

        disk_frame = tk.LabelFrame(f, text="Disk (sda)", padx=6, pady=4)
        disk_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(disk_frame, text="Sector:").grid(row=0, column=0)
        self.sector_var = tk.StringVar(value="0")
        tk.Entry(disk_frame, textvariable=self.sector_var, width=6).grid(row=0, column=1, padx=4)
        tk.Label(disk_frame, text="Data:").grid(row=0, column=2)
        self.disk_data_var = tk.StringVar(value="block_data")
        tk.Entry(disk_frame, textvariable=self.disk_data_var, width=16).grid(row=0, column=3, padx=4)
        tk.Button(disk_frame, text="Write Block", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._disk_write).grid(row=0, column=4, padx=4)
        tk.Button(disk_frame, text="Read Block", bg="#fab387", fg="#1e1e2e",
                  command=self._disk_read).grid(row=0, column=5)

        net_frame = tk.LabelFrame(f, text="Network (eth0)", padx=6, pady=4)
        net_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(net_frame, text="Dest IP:").grid(row=0, column=0)
        self.net_dest = tk.StringVar(value="192.168.1.2")
        tk.Entry(net_frame, textvariable=self.net_dest, width=14).grid(row=0, column=1, padx=4)
        tk.Label(net_frame, text="Payload:").grid(row=0, column=2)
        self.net_payload = tk.StringVar(value="PING")
        tk.Entry(net_frame, textvariable=self.net_payload, width=14).grid(row=0, column=3, padx=4)
        tk.Button(net_frame, text="Connect", bg="#89b4fa", fg="#1e1e2e",
                  command=self._net_connect).grid(row=0, column=4, padx=3)
        tk.Button(net_frame, text="Send Packet", bg="#a6e3a1", fg="#1e1e2e",
                  command=self._net_send).grid(row=0, column=5, padx=3)

        tk.Button(f, text="All Device Status", bg="#f9e2af", fg="#1e1e2e",
                  font=("Arial", 10), command=self._all_status).pack(pady=6)

        self.log_text = scrolledtext.ScrolledText(f, height=12, bg="#1e1e2e", fg="#89dceb",
                                                  font=("Courier", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=4)

    def _log(self, msg):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")

    def _press_key(self):
        event = self.kernel.driver.keyboard.press_key(self.kb_var.get())
        self._log(f"Key pressed: {event}")

    def _read_kb(self):
        data = self.kernel.driver.keyboard.read()
        self._log(f"Keyboard buffer: {data}" if data else "Buffer empty")

    def _print_display(self):
        line = self.kernel.driver.output(self.disp_var.get())
        self._log(f"Display: {line}")

    def _show_screen(self):
        lines = self.kernel.driver.display.screen()
        self._log("\n=== Display Screen ===")
        for l in lines[-20:]:
            self._log(l)

    def _disk_write(self):
        try:
            sector = int(self.sector_var.get())
        except ValueError:
            self._log("Invalid sector")
            return
        self.kernel.driver.disk.write_block(sector, self.disk_data_var.get())
        self._log(f"Disk sector {sector} written: {self.disk_data_var.get()}")

    def _disk_read(self):
        try:
            sector = int(self.sector_var.get())
        except ValueError:
            return
        data = self.kernel.driver.disk.read_block(sector)
        self._log(f"Disk sector {sector}: {data}")

    def _net_connect(self):
        self.kernel.driver.network.connect()
        self._log("Network connected")

    def _net_send(self):
        ok, msg = self.kernel.driver.network.send_packet(self.net_dest.get(), self.net_payload.get())
        self._log(msg)

    def _all_status(self):
        status = self.kernel.driver.all_status()
        self._log("\n=== Device Status ===")
        for dev, info in status.items():
            self._log(f"  {dev}: {info}")


class SystemTab:
    def __init__(self, parent, kernel):
        self.kernel = kernel
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        f = self.frame

        tk.Button(f, text="Refresh System Status", bg="#cba6f7", fg="#1e1e2e",
                  font=("Arial", 11), command=self._refresh).pack(pady=10)

        self.text = scrolledtext.ScrolledText(f, height=24, bg="#1e1e2e", fg="#cdd6f4",
                                              font=("Courier", 9))
        self.text.pack(fill="both", expand=True, padx=10, pady=4)
        self._refresh()

    def _refresh(self):
        status = self.kernel.system_status()
        self.text.delete("1.0", "end")

        def pr(line=""):
            self.text.insert("end", str(line) + "\n")

        pr("=" * 55)
        pr(f"  {status['os']}  v{status['version']}")
        pr(f"  Boot time : {status['boot_time']}")
        pr(f"  Running   : {status['running']}")
        pr("=" * 55)

        mem = status["memory"]
        pr(f"\n[MEMORY]")
        pr(f"  Total: {mem['total']} | Used: {mem['used']} ({mem['used_pct']}%) | Free: {mem['free']}")
        for pid, blk in mem["allocations"].items():
            pr(f"  PID {pid}: start={blk['start']}, size={blk['size']}")

        ipc = status["ipc"]
        pr(f"\n[IPC]")
        pr(f"  MQ size: {ipc['message_queue_size']}")
        pr(f"  Pipes  : {list(ipc['pipes'].keys())}")
        pr(f"  SHM    : {list(ipc['shared_memories'].keys())}")

        devs = status["devices"]
        pr(f"\n[DEVICES]")
        for dev, info in devs.items():
            pr(f"  {dev}: connected={info.get('connected', '?')}")

        logs = status["log_summary"]
        pr(f"\n[LOG SUMMARY]")
        for lvl, count in logs.items():
            if count:
                pr(f"  {lvl}: {count}")


class OSApp:
    def __init__(self, kernel):
        self.kernel = kernel
        self.token = None
        self.username = None

        self.root = tk.Tk()
        self.root.title("Jack OS — Mini Operating System Simulator")
        self.root.geometry("900x680")
        self.root.configure(bg="#1e1e2e")
        self.root.withdraw()

    def _build_main(self):
        self.root.deiconify()

        # Header
        header = tk.Frame(self.root, bg="#181825", pady=6)
        header.pack(fill="x")
        tk.Label(header, text="Jack OS", font=("Courier", 20, "bold"),
                 bg="#181825", fg="#cba6f7").pack(side="left", padx=16)
        tk.Label(header, text="24CS070 | 24CS062 | 24CS028",
                 font=("Arial", 9), bg="#181825", fg="#6c7086").pack(side="left", padx=10)
        tk.Label(header, text=f"User: {self.username}", font=("Arial", 10, "bold"),
                 bg="#181825", fg="#a6e3a1").pack(side="right", padx=16)

        # Notebook tabs
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4",
                        padding=[12, 4])
        style.map("TNotebook.Tab", background=[("selected", "#cba6f7")],
                  foreground=[("selected", "#1e1e2e")])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        tabs = [
            ("Terminal",   TerminalTab(nb, self.kernel).frame),
            ("Scheduler",  SchedulerTab(nb, self.kernel).frame),
            ("Memory",     MemoryTab(nb, self.kernel).frame),
            ("FileSystem", FileSystemTab(nb, self.kernel).frame),
            ("IPC",        IPCTab(nb, self.kernel).frame),
            ("Security",   SecurityTab(nb, self.kernel, self.token, self.username).frame),
            ("Logger",     LoggerTab(nb, self.kernel).frame),
            ("Devices",    DevicesTab(nb, self.kernel).frame),
            ("System",     SystemTab(nb, self.kernel).frame),
        ]
        for name, frame in tabs:
            nb.add(frame, text=name)

        # Status bar
        status_bar = tk.Frame(self.root, bg="#181825", height=22)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar, text="Jack OS v1.0 | Mini OS Simulation | CEP Project",
                 bg="#181825", fg="#6c7086", font=("Arial", 8)).pack(side="left", padx=8)

    def run(self):
        def on_login_success(token, username):
            self.token = token
            self.username = username
            self._build_main()

        LoginWindow(self.kernel, on_login_success)
        self.root.mainloop()
