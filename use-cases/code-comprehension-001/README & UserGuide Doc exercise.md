# Task Manager System

A command-line application for arranging, storing, and managing tasks. Tasks are persisted locally as JSON, and the system supports multi-level sorting, priority tracking, status workflows, tagging, and due-date management.

---

## Table of Contents

1. [Features Overview](#1-features-overview)
2. [Code Structure](#2-code-structure)
3. [Installation](#3-installation)
4. [Configuration Options](#4-configuration-options)
5. [Basic Usage](#5-basic-usage)
6. [Troubleshooting](#6-troubleshooting)
7. [Contributing Guidelines](#7-contributing-guidelines)
8. [License](#8-license)

---

## 1. Features Overview

| Feature | Description |
|---|---|
| **Multi-level sorting** | Filter and list tasks by status, priority, or overdue state |
| **Task storage** | Tasks are automatically persisted to a local JSON file (`tasks.json`) after every change |
| **Create tasks** | Add tasks with a title, description, priority, due date, and tags |
| **Edit tasks** | Update status, priority, due date, and tags on any existing task |
| **Status workflow** | Four-stage workflow: `todo` → `in_progress` → `review` → `done` |
| **Priority levels** | Four levels: `LOW (1)`, `MEDIUM (2)`, `HIGH (3)`, `URGENT (4)` |
| **Tag management** | Add and remove arbitrary tags to organise tasks |
| **Overdue detection** | Automatically identifies tasks whose due date has passed and are not yet done |
| **Statistics** | Summarise tasks by status, priority, and completion rate |

---

## 2. Code Structure

```
TaskManager/
├── cli.py            # Command-line interface — parses arguments and delegates to TaskManager
├── task_manager.py   # Core business logic — creates, updates, deletes, and queries tasks
├── models.py         # Data models — Task class, TaskStatus enum, TaskPriority enum
├── storage.py        # Persistence layer — reads/writes tasks.json via custom JSON encoder/decoder
├── tests/
│   ├── __init__.py
│   └── test_task_manager.py   # Unit tests for TaskManager
└── tasks.json        # Auto-generated task data file (created on first run)
```

### Module Responsibilities

- **`models.py`** — Defines the `Task` dataclass and the `TaskStatus` / `TaskPriority` enumerations. Tasks are assigned a UUID automatically on creation.
- **`storage.py`** — `TaskStorage` manages in-memory task state and flushes changes to `tasks.json` using a custom `TaskEncoder` / `TaskDecoder` pair that serialises enums and `datetime` objects.
- **`task_manager.py`** — `TaskManager` is the service layer; it validates input and coordinates between `Task` models and `TaskStorage`.
- **`cli.py`** — Thin CLI wrapper that uses `argparse` to expose every `TaskManager` method as a sub-command.

---

## 3. Installation

### Prerequisites

- Python **3.11** or higher
- No third-party packages are required — the project uses the Python standard library only (`json`, `uuid`, `argparse`, `datetime`).

### Steps

1. **Clone or download the repository:**

   ```bash
   git clone <repository-url>
   cd TaskManager
   ```

2. **Verify your Python version:**

   ```bash
   python --version
   # Expected: Python 3.11.x or higher
   ```

3. **Run the application:**

   ```bash
   python cli.py --help
   ```

   No installation step or virtual environment is required, though using one is recommended for isolation:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

4. **Run the tests:**

   ```bash
   python -m pytest tests/
   ```

---

## 4. Configuration Options

The only configurable option is the **storage file path**. By default, tasks are saved to `tasks.json` in the working directory.

To use a different file, instantiate `TaskManager` with a custom path in code:

```python
from task_manager import TaskManager

tm = TaskManager(storage_path="/path/to/my_tasks.json")
```

There are no environment variables or external configuration files required.

---

## 5. Basic Usage

All commands are run from the project directory as:

```bash
python cli.py <command> [options]
```

### Create a task

```bash
# Minimal
python cli.py create "Write unit tests"

# With all options
python cli.py create "Write unit tests" \
  -d "Cover all edge cases in storage module" \
  -p 3 \
  -u 2026-04-01 \
  -t "testing,backend"
```

**Priority values:** `1` = LOW, `2` = MEDIUM (default), `3` = HIGH, `4` = URGENT

### List tasks

```bash
# All tasks
python cli.py list

# Filter by status
python cli.py list --status in_progress

# Filter by priority
python cli.py list --priority 4

# Show only overdue tasks
python cli.py list --overdue
```

### Show a single task

```bash
python cli.py show <task_id>
```

The `task_id` is the full UUID printed when the task is created. You may also use the first 8 characters for display purposes.

### Update a task

```bash
# Change status
python cli.py status <task_id> done

# Change priority
python cli.py priority <task_id> 4

# Change due date
python cli.py due <task_id> 2026-05-15
```

**Valid status values:** `todo`, `in_progress`, `review`, `done`

### Manage tags

```bash
# Add a tag
python cli.py tag <task_id> urgent

# Remove a tag
python cli.py untag <task_id> urgent
```

### Delete a task

```bash
python cli.py delete <task_id>
```

### View statistics

```bash
python cli.py stats
```

Output example:

```
Total tasks: 12
By status:
  todo: 4
  in_progress: 3
  review: 2
  done: 3
By priority:
  LOW: 1
  MEDIUM: 5
  HIGH: 4
  URGENT: 2
Overdue tasks: 1
Completed in last 7 days: 2
```

---

## 6. Troubleshooting

### `ModuleNotFoundError: No module named 'models'`

Ensure you are running the CLI from the `TaskManager/` directory, not from a parent folder:

```bash
cd path/to/TaskManager
python cli.py list
```

### `Python version is below 3.11`

Check your version with `python --version`. If you have multiple Python versions installed, try `python3 cli.py` or specify the full path to the Python 3.11+ executable.

### `Error loading tasks: ...` on startup

The `tasks.json` file may be malformed (e.g., edited manually). To reset:

```bash
# Back up the corrupted file first
mv tasks.json tasks.json.bak

# Then run any command to create a fresh tasks.json
python cli.py list
```

### `Failed to update task status. Task not found.`

The task ID provided does not match any stored task. Run `python cli.py list` to see all task IDs, then copy the full UUID.

### `Invalid date format. Use YYYY-MM-DD`

Due dates must follow the format `YYYY-MM-DD`, e.g., `2026-04-30`. Month and day must be zero-padded.

---

## 7. Contributing Guidelines

Contributions are welcome. Please follow the steps below.

### Workflow

1. **Fork** the repository and create a feature branch:

   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes.** Keep commits small and focused.

3. **Write or update tests** in `tests/test_task_manager.py` for any new behaviour.

4. **Run the test suite** and confirm all tests pass:

   ```bash
   python -m pytest tests/ -v
   ```

5. **Open a pull request** against the `main` branch with a clear description of what was changed and why.

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Use descriptive variable and function names.
- Do not introduce third-party dependencies without prior discussion.

### Reporting Issues

Please open an issue with:
- A clear description of the problem.
- Steps to reproduce.
- The Python version and OS in use.
- Any relevant error messages or stack traces.

---

## 8. License

This project is released under the **MIT License**.

---

---

# User Guide: How to Add a Task

**Audience:** Beginners  
**Application:** Task Manager System (command-line)

---

## Prerequisites

Before you can add a task, make sure the following are in place:

- **Python 3.11 or higher** is installed on your machine.
  Verify this by opening a terminal and running:

  ```bash
  python --version
  ```

  You should see output like `Python 3.11.x`. If you see a lower version or an error, install Python from [python.org](https://www.python.org/downloads/).

- **You are in the correct directory.** All commands must be run from inside the `TaskManager/` folder. Navigate there first:

  ```bash
  cd path/to/TaskManager
  ```

  > **Tip:** If you are unsure where the folder is, search for `cli.py` on your computer — the folder containing it is the right one.

- **The application files are present.** You should see the following files in the folder:

  ```
  cli.py
  task_manager.py
  models.py
  storage.py
  ```

  If any files are missing, re-download or restore the project.

---

## Step-by-Step: Adding a Task

### Step 1 — Open a terminal

Open a terminal (Command Prompt, PowerShell, or a terminal in your code editor) and navigate to the `TaskManager/` directory:

```bash
cd path/to/TaskManager
```

**[Screenshot placeholder: Terminal window open at the TaskManager directory]**

---

### Step 2 — Understand the create command

The command used to add a task is `create`. Its full syntax is:

```bash
python cli.py create "<title>" [options]
```

The parts in `[options]` are all **optional** — only the title is required. Here is what each option does:

| Option | Short form | What it sets | Example value |
|---|---|---|---|
| `--description` | `-d` | A longer explanation of the task | `"Fix login bug"` |
| `--priority` | `-p` | Urgency level from 1 (Low) to 4 (Urgent) | `3` |
| `--due` | `-u` | Deadline date in `YYYY-MM-DD` format | `2026-04-30` |
| `--tags` | `-t` | One or more labels, separated by commas | `"backend,urgent"` |

> **Note:** Quotation marks around values containing spaces are required on most systems.

---

### Step 3 — Create a basic task (title only)

The simplest way to add a task is to provide only a title. Run:

```bash
python cli.py create "Buy groceries"
```

**Expected output:**

```
Created task with ID: 3f6a1c2d-89b4-4e1a-bc34-1234567890ab
```

The long string of letters and numbers is the **task ID**. Save it — you will need it to update or delete this task later.

**[Screenshot placeholder: Terminal showing the "Created task with ID:" confirmation message]**

---

### Step 4 — Create a task with a description

Use the `-d` flag to add more detail to a task:

```bash
python cli.py create "Buy groceries" -d "Milk, eggs, bread, and coffee"
```

**Expected output:**

```
Created task with ID: 3f6a1c2d-89b4-4e1a-bc34-1234567890ab
```

> **Common mistake:** Forgetting to wrap the description in quotes when it contains spaces. The following will cause an error:
>
> ```bash
> # WRONG — missing quotes
> python cli.py create "Buy groceries" -d Milk eggs bread
> ```

---

### Step 5 — Set a priority level

Use the `-p` flag with a number from 1 to 4:

| Value | Priority |
|---|---|
| `1` | LOW |
| `2` | MEDIUM *(default if not specified)* |
| `3` | HIGH |
| `4` | URGENT |

```bash
python cli.py create "Fix login bug" -p 3
```

**[Screenshot placeholder: Terminal command with priority flag and resulting output]**

> **Common mistake:** Using a word instead of a number for priority. The following will fail:
>
> ```bash
> # WRONG — use a number, not a word
> python cli.py create "Fix login bug" -p high
> ```

---

### Step 6 — Add a due date

Use the `-u` flag with a date in **YYYY-MM-DD** format (year-month-day):

```bash
python cli.py create "Submit report" -u 2026-04-30
```

> **Common mistake:** Using a different date format. The following will produce an error:
>
> ```bash
> # WRONG — incorrect formats
> python cli.py create "Submit report" -u 30/04/2026
> python cli.py create "Submit report" -u April 30
> ```
>
> Always use `YYYY-MM-DD`, e.g., `2026-04-30`.

---

### Step 7 — Add tags

Tags help you group and find related tasks. Use the `-t` flag with a comma-separated list (no spaces around commas):

```bash
python cli.py create "Fix login bug" -t "backend,security"
```

To add a single tag:

```bash
python cli.py create "Design homepage" -t "frontend"
```

> **Common mistake:** Including spaces around commas. Use `"backend,security"` not `"backend, security"` — spaces become part of the tag name.

---

### Step 8 — Create a fully detailed task

Combine all options in a single command:

```bash
python cli.py create "Fix login bug" \
  -d "Users cannot log in with special characters in password" \
  -p 4 \
  -u 2026-04-01 \
  -t "backend,security,urgent"
```

On Windows (Command Prompt or PowerShell), write it on one line instead:

```bash
python cli.py create "Fix login bug" -d "Users cannot log in with special characters in password" -p 4 -u 2026-04-01 -t "backend,security,urgent"
```

**Expected output:**

```
Created task with ID: 7b3e9f01-12cd-4abc-def0-9876543210ff
```

**[Screenshot placeholder: Full command with all flags entered in the terminal, followed by success output]**

---

### Step 9 — Verify the task was created

Confirm the task appears in the task list:

```bash
python cli.py list
```

You should see your new task printed with its status, priority, description, due date, and tags:

```
[ ] 7b3e9f01 - !!!! Fix login bug
  Users cannot log in with special characters in password
  Due: 2026-04-01 | Tags: backend, security, urgent
  Created: 2026-03-26 14:00
--------------------------------------------------
```

**Status symbols:** `[ ]` = todo, `[>]` = in progress, `[?]` = review, `[✓]` = done  
**Priority symbols:** `!` = LOW, `!!` = MEDIUM, `!!!` = HIGH, `!!!!` = URGENT

**[Screenshot placeholder: Terminal output of the list command showing the newly created task]**

---

## Common Mistakes at a Glance

| Mistake | Example | Fix |
|---|---|---|
| Running from the wrong directory | `python cli.py create` gives "No such file or directory" | `cd` into the `TaskManager/` folder first |
| No quotes around multi-word title | `python cli.py create Buy groceries` | `python cli.py create "Buy groceries"` |
| Wrong priority format | `-p high` | `-p 3` (use a number 1–4) |
| Wrong date format | `-u 30/04/2026` | `-u 2026-04-30` |
| Spaces in tag list | `-t "backend, security"` | `-t "backend,security"` |
| Forgetting to save the task ID | Output dismissed immediately | Copy the ID from the terminal or run `python cli.py list` to retrieve it |

---

## Troubleshooting

### "No such file or directory: cli.py"

You are not in the right folder. Run:

```bash
cd path/to/TaskManager
python cli.py create "My task"
```

### "python: command not found" or "python is not recognised"

Try using `python3` instead of `python`:

```bash
python3 cli.py create "My task"
```

If that also fails, Python is not installed or not added to your system PATH. Download it from [python.org](https://www.python.org/downloads/) and re-install, making sure to check **"Add Python to PATH"** during setup.

### "error: argument -p/--priority: invalid choice"

You passed an invalid priority value. Only `1`, `2`, `3`, or `4` are accepted:

```bash
# Correct
python cli.py create "My task" -p 2
```

### "Invalid date format. Use YYYY-MM-DD"

Your date is not in the correct format. Use four-digit year, two-digit month, two-digit day:

```bash
# Correct
python cli.py create "My task" -u 2026-04-30
```

### "Error loading tasks" on startup

Your `tasks.json` file may be corrupted. Rename it to back it up and let the application create a fresh one:

```bash
# Windows
rename tasks.json tasks.json.bak

# macOS / Linux
mv tasks.json tasks.json.bak
```

Then run your `create` command again.

### Task created but cannot find it in the list

You may be running `python cli.py list` from a different directory, causing a different `tasks.json` to be read. Always run all commands from the same `TaskManager/` directory.

---

*End of guide. For further help, refer to the [Troubleshooting](#6-troubleshooting) section of the main README above, or open an issue in the project repository.*

---

## 8. License

This project is released under the **MIT License**.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

# FAQ: Task Manager System

This FAQ is intended for both **users** and **developers** who need quick answers about how the Task Manager System works, how to use its common features, and how to resolve common issues.

---

## 1. Getting Started

### Q1. What is the Task Manager System?

The Task Manager System is a command-line application for creating, storing, organizing, and updating tasks. It stores task data locally in a `tasks.json` file and supports priorities, due dates, tags, status tracking, and summary statistics.

### Q2. Who is this system for?

It is designed for:

- **Users** who want a simple local task manager.
- **Developers** who want a small Python-based task management project that is easy to read, extend, and test.

### Q3. What do I need before I can use it?

You need:

- Python 3.11 or higher installed.
- Access to the project files, including `cli.py`, `task_manager.py`, `models.py`, and `storage.py`.
- A terminal opened in the `TaskManager/` project directory.

### Q4. How do I start the application?

Open a terminal in the project folder and run:

```bash
python cli.py --help
```

This displays all available commands and confirms that the application is accessible from your current working directory.

### Q5. How do I use the system for the first time?

The simplest way to begin is to create a task and then list all tasks:

```bash
python cli.py create "My first task"
python cli.py list
```

This creates a new task and shows it in the task list.

### Q6. How do I know if the system is working correctly?

If the system is working correctly:

- commands run without Python import errors,
- task creation prints a task ID,
- running `python cli.py list` shows your saved tasks,
- a `tasks.json` file appears in the project directory after the first change.

---

## 2. Common Features and Functionality

### Q7. How do I add a task?

Use the `create` command and provide a title:

```bash
python cli.py create "Buy groceries"
```

You can also include optional fields such as description, priority, due date, and tags.

### Q8. How do I add more details to a task when creating it?

Use the optional flags:

```bash
python cli.py create "Write report" -d "Quarterly performance summary" -p 3 -u 2026-04-30 -t "work,reporting"
```

Meaning of the options:

- `-d` or `--description`: adds a longer explanation.
- `-p` or `--priority`: sets priority from `1` to `4`.
- `-u` or `--due`: sets a due date in `YYYY-MM-DD` format.
- `-t` or `--tags`: adds comma-separated tags.

### Q9. How do I view all tasks?

Run:

```bash
python cli.py list
```

This displays every stored task, including its status, priority, description, due date, and tags.

### Q10. Can I filter tasks?

Yes. You can filter tasks by status, priority, or overdue state.

Examples:

```bash
python cli.py list --status in_progress
python cli.py list --priority 4
python cli.py list --overdue
```

### Q11. How do I change a task's status?

Use the `status` command with the task ID and the new status:

```bash
python cli.py status <task_id> done
```

Valid status values are:

- `todo`
- `in_progress`
- `review`
- `done`

### Q12. How do I change a task's priority?

Use:

```bash
python cli.py priority <task_id> 4
```

Priority values are:

- `1` = LOW
- `2` = MEDIUM
- `3` = HIGH
- `4` = URGENT

### Q13. How do I update a due date?

Use:

```bash
python cli.py due <task_id> 2026-05-15
```

The due date must be in `YYYY-MM-DD` format.

### Q14. How do tags work?

Tags are short labels that help categorize tasks. You can add or remove them later.

Examples:

```bash
python cli.py tag <task_id> urgent
python cli.py untag <task_id> urgent
```

### Q15. How do I see details for one task only?

Use:

```bash
python cli.py show <task_id>
```

This prints one task in a readable format.

### Q16. How do I delete a task?

Use:

```bash
python cli.py delete <task_id>
```

This permanently removes the task from storage.

### Q17. Does the system save tasks automatically?

Yes. Tasks are saved automatically to `tasks.json` after create, update, tag, untag, and delete operations. You do not need to run a separate save command.

### Q18. What do the status symbols mean in the task list?

The CLI uses short symbols to show status:

- `[ ]` = `todo`
- `[>]` = `in_progress`
- `[?]` = `review`
- `[✓]` = `done`

### Q19. What do the priority symbols mean?

Priority is shown with exclamation marks:

- `!` = LOW
- `!!` = MEDIUM
- `!!!` = HIGH
- `!!!!` = URGENT

### Q20. How do I use the system effectively as a beginner?

Start with this basic workflow:

1. Create a task.
2. Run `list` to confirm it was saved.
3. Add tags or a due date if needed.
4. Update the status as work progresses.
5. Use `stats` to review your task summary.

This is the easiest answer to the common question, "How do I use the system?"

---

## 3. Troubleshooting Common Issues

### Q21. Why do I get "No such file or directory: cli.py"?

You are likely running the command from the wrong folder. Move into the `TaskManager/` directory first:

```bash
cd path/to/TaskManager
python cli.py list
```

### Q22. Why does the system say `python` is not recognised?

Python may not be installed correctly, or it may not be available in your system `PATH`. Try:

```bash
python3 --version
```

If that works, use `python3` instead of `python`. Otherwise, install Python 3.11+ and enable the option to add it to your `PATH`.

### Q23. Why did my task creation fail with `Invalid date format. Use YYYY-MM-DD`?

The date was entered in the wrong format. Use a four-digit year, two-digit month, and two-digit day.

Correct example:

```bash
python cli.py create "Submit report" -u 2026-04-30
```

### Q24. Why am I seeing `error: argument -p/--priority: invalid choice`?

The priority must be a number from `1` to `4`. Text values such as `high` or `urgent` are not accepted by the CLI.

### Q25. Why is my task missing when I run `list`?

The most common reasons are:

- you are running commands from a different directory,
- you created the task in another copy of the project,
- `tasks.json` was deleted or replaced,
- the task was already deleted.

Make sure you always run commands from the same project directory.

### Q26. What does `Error loading tasks` mean?

It usually means the `tasks.json` file is malformed or unreadable. This can happen if it was edited manually and the JSON syntax became invalid.

To recover:

```bash
rename tasks.json tasks.json.bak
python cli.py list
```

This creates a fresh task file the next time the application saves data.

### Q27. Why can I not update or delete a task?

The task ID may be incorrect, incomplete, or no longer present in storage. Run:

```bash
python cli.py list
```

Then copy the correct task ID and retry the command.

### Q28. Why do my tags look wrong?

If you create tags with spaces after commas, the spaces may become part of the tag text. Prefer this format:

```bash
python cli.py create "Fix login bug" -t "backend,security,urgent"
```

instead of:

```bash
python cli.py create "Fix login bug" -t "backend, security, urgent"
```

### Q29. What should I do if the system behaves unexpectedly after editing files manually?

Check whether:

- `tasks.json` still contains valid JSON,
- the Python source files were modified incorrectly,
- you are using the intended Python version,
- the working directory still points to the correct project.

If needed, restore the project files from version control and re-test with `python cli.py --help`.

---

## 4. Developer and Storage Questions

### Q30. Where are tasks stored?

Tasks are stored in a local file named `tasks.json` in the working directory. The storage layer loads this file on startup and writes back to it whenever data changes.

### Q31. What format is used to store tasks?

Tasks are stored as JSON objects. Enum values such as status and priority are converted into serializable values, and date fields are stored as ISO-format strings.

### Q32. Which parts of the code handle task storage?

The main modules are:

- `models.py` for the `Task`, `TaskStatus`, and `TaskPriority` definitions,
- `storage.py` for loading and saving JSON,
- `task_manager.py` for the main task operations,
- `cli.py` for parsing terminal commands.

### Q33. Can developers change the storage file location?

Yes. The `TaskManager` class accepts a `storage_path` argument, so developers can point the application to a different JSON file in code.

Example:

```python
from task_manager import TaskManager

manager = TaskManager(storage_path="custom_tasks.json")
```

### Q34. Is this application using a database?

No. It uses a simple JSON file for persistence. This keeps the project lightweight and easy to understand, but it also means it is best suited to local or small-scale usage.

### Q35. Is there built-in authentication or user management?

No. This project is a local task manager and does not include login, roles, permissions, or multi-user account support.

### Q36. How can developers add new features safely?

Developers should:

1. understand the current flow from `cli.py` to `task_manager.py` to `storage.py`,
2. add or update tests in the `tests/` directory,
3. avoid changing saved data formats without planning migration,
4. run the test suite after every change.

### Q37. Why does the application use enums for status and priority?

Enums make task states and priority levels predictable, easier to validate, and less error-prone than free-form strings throughout the codebase.

### Q38. What should developers know before editing `tasks.json` manually?

Manual editing is possible, but risky. If the JSON structure is broken, the application may fail to load tasks correctly. If manual changes are necessary, validate the JSON before running the application.

---

## 5. Quick Reference

### Q39. What are the most useful commands to remember?

```bash
python cli.py create "Task title"
python cli.py list
python cli.py show <task_id>
python cli.py status <task_id> done
python cli.py priority <task_id> 4
python cli.py due <task_id> 2026-05-15
python cli.py tag <task_id> urgent
python cli.py untag <task_id> urgent
python cli.py delete <task_id>
python cli.py stats
```

### Q40. Where should users go if they still need help?

Users should first review the getting started guide and troubleshooting sections in this document. Developers should also inspect the source modules and test files if the issue appears to be code-related.
