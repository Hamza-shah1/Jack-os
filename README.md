# 🚀 Jack OS — Mini Operating System Simulator

## 📌 Overview

**Jack OS** is a modular Operating System Simulation Project developed as part of an academic Complex Engineering Problem. It replicates core operating system functionalities including process management, memory allocation, file systems, inter-process communication, and security mechanisms.

The system is built entirely in **Python** and features both a **Graphical User Interface (GUI)** and a powerful custom command-line shell called **Kafka Shell**.

---

## ✨ Key Features

* 🧠 **Custom Kafka Shell**

  * Command parsing, piping (`|`), redirection (`>`, `>>`, `<`)
  * Background jobs (`&`), job control (`fg`, `bg`, `jobs`)
  * Environment variables (`export`, `unset`, `$VAR`)
  * Command history & auto-completion

* ⚙️ **Process Scheduling**

  * Round Robin (configurable time quantum)
  * First Come First Served (FCFS)
  * Shortest Job First (SJF)

* 💾 **Memory Management**

  * First Fit Allocation
  * Best Fit Allocation
  * Memory Compaction (defragmentation)
  * Visual memory map in GUI

* 📂 **Virtual File System**

  * Hierarchical tree structure
  * File & directory operations (create, delete, move)
  * Permission system (Unix-style)
  * Search and full tree view

* 🔄 **Inter-Process Communication (IPC)**

  * Message Queues
  * Pipes
  * Shared Memory (thread-safe)

* 🔐 **Security System**

  * User authentication (SHA-256 hashing)
  * Role-Based Access Control (Admin/User/Guest)
  * Account lock after failed attempts
  * Audit logging

* 🖥️ **GUI Dashboard (Tkinter)**

  * 9 interactive tabs:

    * Terminal (Kafka Shell)
    * Scheduler
    * Memory
    * File System
    * IPC
    * Security
    * Logger
    * Devices
    * System Overview

* 🔌 **Device Driver Simulation**

  * Keyboard input buffer
  * Display output system
  * Disk sector read/write
  * Network communication simulation

* 📊 **Centralized Logging System**

  * 5 log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  * Persistent log file + in-memory buffer
  * Filtering by module and severity

---

## 🏗️ System Architecture

Jack OS follows a **modular two-layer architecture**:

### 🎨 Presentation Layer

* Tkinter-based GUI dashboard
* Kafka Shell (embedded terminal)

### ⚙️ Core Modules Layer

* Kernel Controller
* Process Scheduler
* Memory Manager
* File System
* IPC Manager
* Security Module
* Device Drivers
* Logger

---


---

## ⚙️ Installation & Setup

### Requirements

* Python 3.8 or higher
* Tkinter (comes with standard Python)

### Steps

```bash
git clone https://github.com/your-username/jack-os.git
cd mini_os
python main.py
```

---

## 🔑 Default Login Credentials

| Username | Password | Role  |
| -------- | -------- | ----- |
| admin    | admin123 | Admin |
| guest    | guest    | Guest |

---

## 🖥️ How to Use

* Open the **Terminal tab** to use Kafka Shell

* Run commands like:

  ```bash
  help
  ls
  spawn process1 10
  ps
  memalloc 1 50
  ```

* Use GUI tabs to interact with:

  * Scheduler
  * Memory
  * File System
  * IPC
  * Security
  * Devices

---

## 📂 Project Structure

```
mini_os/
│
├── kernel.py
├── main.py
├── modules/
│   ├── scheduler.py
│   ├── memory.py
│   ├── filesystem.py
│   ├── ipc.py
│   ├── security.py
│   ├── driver.py
│   └── logger.py
│
├── gui/
│   ├── terminal.py
│   └── (other GUI files)
│
├── screenshots/
│
└── README.md
```

---

## ⭐ What Makes This Project Special

* Modular OS-like architecture with kernel coordination
* Fully functional custom shell with advanced features
* Multiple scheduling and memory algorithms implemented
* Realistic simulation of OS subsystems
* GUI + CLI hybrid interaction model
* Security and logging integrated across system

---

## 🎓 Academic Information

* **University:** Mehran University of Engineering & Technology, Jamshoro
* **Department:** Computer Systems Engineering
* **Course:** Operating Systems (CS-261)
* **Instructor:** Engr. Zoha Memon
* **Semester:** 4th Year, 2nd Semester

---

## 👨‍💻 Team Members

* 24CS070
* 24CS028
* 24CS062

---

## 📌 Conclusion

Jack OS demonstrates the practical implementation of core operating system concepts including scheduling, memory management, file systems, IPC, and security. The integration of a custom shell with a graphical dashboard provides both low-level and high-level interaction with system components.

This project serves as a strong foundation for understanding real-world OS design and architecture.

---

## 📄 License

This project is for educational purposes.
