def calculate_task_score(task):
    """
    Calculate a composite priority score for a task based on multiple factors.

    The score is determined by combining the task's priority, due date proximity,
    completion status, critical tags, and recency of updates. Higher scores indicate
    higher importance or urgency. This function is typically used to rank or sort
    tasks for prioritization.

    Parameters
    ----------
    task : Task
        The task object to score. Must have the following attributes:
        - priority (TaskPriority): Enum value indicating task priority.
        - due_date (datetime or None): When the task is due.
        - status (TaskStatus): Enum value indicating current status.
        - tags (list of str): List of tag strings.
        - updated_at (datetime): Last update timestamp.

    Returns
    -------
    int
        The calculated priority score for the task. Higher values indicate higher priority.

    Raises
    ------
    AttributeError
        If the task object is missing required attributes.
    TypeError
        If task attributes are of incorrect types.

    Example
    -------
    >>> task = Task(
    ...     title="Fix bug",
    ...     priority=TaskPriority.HIGH,
    ...     due_date=datetime(2026, 3, 28),
    ...     status=TaskStatus.TODO,
    ...     tags=["critical"],
    ...     updated_at=datetime.now()
    ... )
    >>> score = calculate_task_score(task)
    >>> print(score)
    68

    Notes
    -----
    - Overdue tasks receive a significant score boost.
    - Tasks with status DONE or REVIEW are penalized.
    - Tags like "blocker", "critical", or "urgent" add extra points.
    - Recently updated tasks (within 1 day) get a small boost.
    - If a task is missing a due date, no due-date bonus is applied.
    - Negative scores are possible for completed tasks.
    - The function assumes the Task object uses the expected enums and datetime types.
    """
  
  Here’s a detailed breakdown and documentation for your code:

---

### 1. High-level intent

This code provides a way to **rank and sort tasks by importance** using a custom scoring algorithm.  
It considers priority, due date, status, tags, and recency of updates to compute a numeric score for each task.  
Tasks can then be sorted or filtered to surface the most urgent or important items.

---

### 2. Step-by-step logic

#### `calculate_task_score(task)`
- Assigns a base score based on the task’s priority (LOW=10, MEDIUM=20, HIGH=40, URGENT=60).
- Adds bonus points if the task is due soon or overdue (overdue: +35, today: +20, next 2 days: +15, next week: +10).
- Subtracts points if the task is completed (-50) or in review (-15).
- Adds points if the task has a “blocker”, “critical”, or “urgent” tag (+8).
- Adds a small bonus if the task was updated within the last day (+5).
- Returns the final score.

#### `sort_tasks_by_importance(tasks)`
- Calculates the score for each task.
- Sorts all tasks in descending order of score.
- Returns the sorted list.

#### `get_top_priority_tasks(tasks, limit=5)`
- Sorts tasks by importance.
- Returns the top N tasks (default 5).

---

### 3. Assumptions and edge cases

- Assumes `task.priority`, `task.status`, `task.due_date`, `task.updated_at`, and `task.tags` exist and are valid.
- If `task.due_date` is `None`, no due-date bonus is applied.
- If `task.priority` is not in the weights dict, base score is 0.
- If a task is both overdue and completed, both bonuses/penalties apply (could result in a negative score).
- If `task.updated_at` is in the future, recency bonus still applies (could be a bug).
- Tags are case-sensitive (“Critical” ≠ “critical”).

---

### 4. Suggested inline comments

```python
def calculate_task_score(task):
    """
    Calculate a composite score for a task based on priority, due date, status, tags, and recency.
    Higher score = higher importance.
    """
    # Assign base score from priority
    priority_weights = {
        TaskPriority.LOW: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.HIGH: 4,
        TaskPriority.URGENT: 6
    }
    score = priority_weights.get(task.priority, 0) * 10

    # Add bonus for due date proximity
    if task.due_date:
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due < 0:      # Overdue
            score += 35
        elif days_until_due == 0:   # Due today
            score += 20
        elif days_until_due <= 2:   # Due in next 2 days
            score += 15
        elif days_until_due <= 7:   # Due in next week
            score += 10

    # Subtract for completed or review status
    if task.status == TaskStatus.DONE:
        score -= 50
    elif task.status == TaskStatus.REVIEW:
        score -= 15

    # Add for critical/blocker/urgent tags
    if any(tag in ["blocker", "critical", "urgent"] for tag in task.tags):
        score += 8

    # Add for recent updates (within 1 day)
    days_since_update = (datetime.now() - task.updated_at).days
    if days_since_update < 1:
        score += 5

    return score
```

---

### 5. Potential improvements

- **Cache `datetime.now()`** at the start of the function to avoid multiple calls.
- **Normalize tag matching** (e.g., lower-case all tags for case-insensitive match).
- **Configurable weights**: Move weights and bonuses to a config or parameters for easier tuning.
- **Handle missing/invalid fields**: Add type checks or try/except for robustness.
- **Tie-breaker**: If two tasks have the same score, sort by due date or creation time.

---
