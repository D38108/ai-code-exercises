# Excercise Codebase Challenge

# Part 1
## Journal Entry: TaskManager Codebase (Task create/update path)

### 1. Main components involved in task creation/updates

- cli.py
  - Parses CLI args (`create`, `update-status`, `update-priority`, `update-due-date`, etc.)
  - Calls `TaskManager` methods.

- task_manager.py
  - `TaskManager` class is business layer:
    - `create_task(...)`
    - `update_task_status(task_id, new_status)`
    - `update_task_priority(task_id, new_priority)`
    - `update_task_due_date(task_id, due_date_str)`
  - Uses `TaskStorage` for persistence.

- `models.py`
  - `Task` data model (fields id/title/description/status/priority/dates/tags).
  - `TaskStatus` enum.
  - `TaskPriority` enum.

- storage.py
  - `TaskStorage` class:
    - `load()`, `save()`
    - `add_task(task)`
    - `get_task(task_id)`
    - `get_all_tasks`, `get_tasks_by_status`, etc.
    - `update_task(...)`, `delete_task(...)`.
  - `TaskEncoder` / `TaskDecoder` for JSON <-> Task object conversion.

---

### 2. Execution flow when a task is created

1. CLI:
   - User runs e.g. `python cli.py create "title" --description "..." --priority 2 --due "2024-12-31"`.
   - cli.py parses input and calls `TaskManager.create_task(...)`.

2. TaskManager:
   - Converts priority int to `TaskPriority`.
   - Parses due date string to `datetime`.
   - Creates `Task(...)`.
   - Calls `TaskStorage.add_task(task)`.
   - Returns task id.

3. Storage:
   - `TaskStorage.add_task(task)` adds in-memory to `self.tasks`.
   - Calls `save()`:
     - Opens tasks.json in write mode.
     - Uses `json.dump()` with `TaskEncoder` to store tasks list.
   - Data persisted as JSON.

---

### 3. Execution flow when updating a task

1. CLI:
   - e.g. `python cli.py update-status <id> done`.
   - cli.py invokes `TaskManager.update_task_status(<id>, "done")`.

2. TaskManager:
   - Converts status to `TaskStatus` enum.
   - If `DONE`: gets task (`TaskStorage.get_task`), runs `task.mark_as_done()` (sets status/date).
   - For other updates, calls `TaskStorage.update_task(...)` directly.

3. Storage:
   - `TaskStorage.update_task(task_id, ...)` applies values to task object.
   - Calls `save()` to persist updated tasks.json.

---

### 4. Data storage/retrieval

- Persistent file: tasks.json (ignored by git via .gitignore)
- In-memory store: `TaskStorage.tasks` (dict keyed by task_id)
- Load path:
  - `TaskStorage.__init__` loads existing JSON (if present).
  - `TaskDecoder` builds `Task` objects, mapping enums/dates.
- Save path:
  - `json.dump(list(self.tasks.values()), f, cls=TaskEncoder, indent=2)`
  - `TaskEncoder` converts `Task` to primitives (`status.value`, `priority.value`, ISO datetime).

---

### 5. Interesting design patterns

- **Layered separation**:
  - CLI layer (cli.py) → service layer (`TaskManager`) → data layer (`TaskStorage`) → model layer (`Task`).
- **Encapsulation**:
  - `Task` owns its own state change logic (`mark_as_done()` likely sets `completed_at` and status), not just field mutation.
- **Serialization adapter**:
  - `TaskEncoder` / `TaskDecoder` are explicit JSON adapters for persisting rich objects (enums/datetime).
- **Filter methods**:
  - Storage provides query-like methods (`get_tasks_by_status`, `get_tasks_by_priority`, `get_overdue_tasks`) used by manager/list operations.

---

### Takeaway
The project is a classic small CLI CRUD app:
- creation/update flow is clear,
- JSON persistence is easy to inspect,
- the rule is: CLI calls manager, manager uses storage, storage saves to file.

# Part 2

## Initial understanding vs. discovery

### What I thought at first
- It’s a CLI task manager in Python.
- Likely JSON-driven data storage.
- Task update/create probably in task_manager.py; CLI in cli.py.
- Task “priority” exists but exact flow wasn’t clear.

### What was confirmed/discovered
- Confirmed: exact app flow is CLI → `TaskManager` → `TaskStorage` → tasks.json.
- `models.py` has `TaskPriority` values and `TaskStatus` enum.
- `task_manager.py.update_task_priority` is the direct update path.
- cli.py has both `update-priority` and `list --priority` support.
- storage.py does final persistence via custom JSON encoder/decoder.

---

## Key insights from guided questions

- **Component boundaries**: clearly separated by responsibility (UI, logic, persistence, model).
- **Task lifecycle**:
  - create: parse inputs, build `Task`, add to storage, save.
  - update: find task, mutate, save.
- **Data format**: tasks.json (except ignored by git), with enums as values and timestamps ISO.
- **Design pattern**:
  - “Convert/encode/decode” (TaskEncoder/Decoder) for model persistence.
  - “filter & lookup” methods in storage for list by priority/status/overdue.
- **Strategy for missing feature**:
  - no export yet, so design placement was inferred (TaskManager + cli.py + tests).

---

## Misconceptions clarified

- Not all “priority” work was in cli.py; actual mutation and persist are in `TaskManager` + `storage`.
- tasks.json is not a config file but runtime state; .gitignore exists to not store local state history.
- `create/update` success is implicitly persisted; no DB behind it, just JSON.
- `update-status` command is implemented as `status` in reality, not `update-status` (docs mismatch).
- No third-party libs. This is plain Python standard lib.

# Part 3

[User CLI] --args--> [cli.py command]
      |
      v
[TaskManager] ---------------+
  / create_task              |  (uses models)
  / update...                v
[models.Task] < (TaskPriority, TaskStatus)
      |
      v
[TaskStorage]  <-- load/save -->
      |
      v
  tasks.json file
      |
      v
[cli.py] prints formatted output

## Task completion state flow (with status DONE)

Great question—this is one of the most important flows.  
You’re already on the right path.

### 1. State changes during task completion

Entry: `python cli.py status <task_id> done`

- cli.py:
  - Parses command and args.
  - Calls `task_manager.update_task_status(task_id, "done")`.

- `task_manager.py.update_task_status`:
  - `new_status = TaskStatus(new_status_value)` → `TaskStatus.DONE`.
  - Since done branch is special:
    - `task = self.storage.get_task(task_id)`
    - If task exists:
      - `task.mark_as_done()` (model-level state mutation)
      - `self.storage.save()` (persist to file)
      - returns `True`
    - If task missing:
      - returns `False`.

- `models.py.Task.mark_as_done`:
  - sets `task.status = TaskStatus.DONE`
  - sets `task.completed_at = datetime.now()`
  - sets `task.updated_at = completed_at`

So completed state is:
- status = DONE
- completed_at timestamp set
- updated_at updated

---

### 2. Potential points of failure

1. **Invalid task ID**:
   - `get_task(task_id)` returns `None`.
   - `task.mark_as_done()` is not called; CLI prints failure.

2. **TaskStatus conversion error** (non-CLI callers):
   - `TaskStatus("x")` would raise `ValueError`. CLI prevents with argument choices but direct API calls may fail.

3. **Storage load/write failures**:
   - tasks.json corrupted or unreadable at start.
   - `save()` may fail if disk full/permissions.
   - storage.py catches exceptions around file I/O and prints error (but may not recover).

4. **Race conditions** (unlikely in single-process CLI):
   - Two simultaneous CLI commands could conflict on tasks.json.

---

### 3. How changes are persisted

- `TaskStorage` is in-memory dict:
  - `self.tasks = {task_id: Task, ...}`.
- On every write operation (`add/update/delete`), `TaskStorage.save()` is called:
  - opens tasks.json `w`
  - `json.dump(list(self.tasks.values()), f, cls=TaskEncoder, indent=2)`
  - `TaskEncoder` serializes:
    - `TaskPriority` → numeric value
    - `TaskStatus` → status string
    - `datetime` fields (`created_at`, `updated_at`, `due_date`, `completed_at`) → ISO string

- Task completion event is persisted immediately in same save before returning success.

- Next run, `TaskStorage.__init__` loads tasks.json:
  - `json.load(..., cls=TaskDecoder)` rebuilds `Task` objects with enums and datetimes.

---

### Quick check

After completion:
- `python cli.py show <task_id>` shows status DONE.
- `python -m unittest discover tests` should pass if logic unchanged.
- tasks.json entry for that task includes `"status": "done"` and `completed_at` timestamp.

That is your end-to-end completion state transition.

##  3-5 Minute Presentation: TaskManager CLI App (Team Share)

### 1. High-level architecture (30s)
- **Entry**: cli.py (argparse commands)
- **Domain logic**: task_manager.py (`TaskManager` class)
- **Model**: `models.py` (`Task`, `TaskPriority`, `TaskStatus`)
- **Persistence**: storage.py (`TaskStorage` + JSON `TaskEncoder`/`TaskDecoder`)
- **Tests**: `tests/` for behavior verification
- **Data file**: tasks.json (runtime, gitignored)

> The flow is: CLI input → parsed args → `TaskManager` method → `Task` state → `TaskStorage` save/read → output text.

---

### 2. Key Feature Walkthrough (1.5 min)

#### a) Task creation
- `python cli.py create "Title" -p 2 --due 2025-01-01`
- CLI builds args (`title`, `priority`, `due`, `tags`)
- `TaskManager.create_task()`:
  - converts priority to `TaskPriority`,
  - parses date
  - creates `Task(...)`
  - calls `TaskStorage.add_task(task)` → `save()`
- output: “Created task with ID…”

#### b) Prioritization
- Command: `python cli.py priority <id> 4`
- `TaskManager.update_task_priority`:
  - `TaskPriority(new_priority_value)`
  - calls `TaskStorage.update_task(task_id, priority=...)`
- persistence: `TaskStorage.save()`, writes JSON
- Listing with filter: `python cli.py list --priority 4` uses `list_tasks` -> storage query

#### c) Completion
- Command: `python cli.py status <id> done`
- `TaskManager.update_task_status`:
  - for DONE: load `task`, call `task.mark_as_done()` (status/completed_at/updated_at changes)
  - save
- Completed tasks now show `[✓]` in formatted output

---

### 3. Interesting design pattern (30s)
- **Adapter / Serializer**:
  - `TaskEncoder` and `TaskDecoder` turn rich object state (enums, datetime) into JSON-friendly forms and back.
- **Why useful**: preserves object model while storing to plain file.
- Equivalent to “Repository with serialization adapter”.

---

### 4. Biggest challenge + prompt process (45s)

#### Challenge
- At first, uncertain if “priority flow” was mostly in CLI, manager, or storage;
- needed to understand exact call chain and side effects, and confirm where non-CLI callers might fail.

#### How prompts helped
- Asked concrete code path questions:
  - “Where is priority updated?”
  - “What happens in task completion”
  - “Where are failures possible?”
- Answer path became:
  - `cli` -> `TaskManager` -> `models` + `storage`.
- Smaller "investigate this one step" prompts gave confidence (not just explanation).

---

### 5. Process summary (1 min)

1. **Start with README + folder list** to confirm expected behavior.
2. **Find entrypoint** (cli.py), run commands directly to observe.
3. **Trace each function call**:
   - for each command, follow native code path (`TaskManager`, then `storage`).
4. **Inspect model definitions** (`Task/enum methods`) for state transitions.
5. **Verify with tests + JSON** (`python -m unittest ...`, open tasks.json).
6. **Pin edge cases**: date parse, missing ID, invalid enum.

---

## ✅ Takeaway for the group
- This is a well-structured exercise app.
- The best way to understand is not one big read, but “execute → trace → verify → repeat”.
- Ask directed prompts and validate each layer with a quick offline command; that’s the process I used.
- Next step for team: propose adding “export” endpoint using same pattern (TaskManager + CLI + test + small storage extension).