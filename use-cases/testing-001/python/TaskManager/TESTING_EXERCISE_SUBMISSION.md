# Testing Exercise Submission
**Language:** Python  
**File under test:** `task_priority.py`  
**Test file:** `tests/test_task_priority.py`  
**Result:** 34 / 34 tests passing

---

## Part 1 — Test Plan

### Exercise 1.1 — Behavior Analysis of `calculate_task_score`

**What the function does**  
Given a `Task` object, `calculate_task_score` builds a numeric score from four independent signals, then adds them together:

| Signal | Rule | Points |
|---|---|---|
| Priority weight | LOW=10, MEDIUM=20, HIGH=40, URGENT=60 | base |
| Due date | overdue: +35 · today: +20 · ≤2 days: +15 · ≤7 days: +10 | bonus |
| Status | DONE: −50 · REVIEW: −15 | penalty |
| Tags | any of `blocker`, `critical`, `urgent`: +8 | bonus |
| Recent update | updated within last day: +5 | bonus |

**Test cases identified (at least 5)**

| # | Description | Type |
|---|---|---|
| 1 | Each priority level produces the correct base score | happy path |
| 2 | Overdue task gets the maximum +35 due-date bonus | happy path |
| 3 | DONE task loses 50 points | state |
| 4 | REVIEW task loses 15 points, less than DONE | state |
| 5 | A `critical` tag adds exactly +8 | tag boost |
| 6 | Multiple critical tags only add +8 once (any-match logic) | edge case |
| 7 | A task with no due date receives zero due-date bonus | edge case |
| 8 | LOW + DONE can produce a negative score | edge case |
| 9 | Recently updated task (+5) stacks with other bonuses | combination |

### Exercise 1.2 — Structured Test Plan for All Three Functions

**Priority of test cases**

| Priority | Function | Description |
|---|---|---|
| P1 (unit, first) | `calculate_task_score` | Priority base scores for all four levels |
| P1 | `calculate_task_score` | Every due-date bracket (+35/+20/+15/+10/0) |
| P1 | `calculate_task_score` | Status penalties (DONE, REVIEW) |
| P2 (unit) | `calculate_task_score` | Tag boost; edge: multiple critical tags |
| P2 | `calculate_task_score` | Recent-update boost |
| P2 | `sort_tasks_by_importance` | Returns tasks highest-score-first |
| P2 | `sort_tasks_by_importance` | Preserves all tasks (no drops/duplicates) |
| P3 (integration) | all three | DONE tasks sink to the bottom after sorting |
| P3 | all three | Urgent + overdue + critical tag is always #1 |
| P3 | `get_top_priority_tasks` | Returns exactly N, or all if N > len(tasks) |
| P3 | `get_top_priority_tasks` | Empty input returns empty list |
| P3 | all three | Top-N == first N of full sorted list |

**Types:** All of P1/P2 are **unit tests**; P3 are **integration tests**.  
**Dependencies:** P3 integration tests depend on `calculate_task_score` and `sort_tasks_by_importance` being correct first.

---

## Part 2 — Improved Unit Tests

### Exercise 2.1 — Robust `calculate_task_score` Tests
Key improvements over the naive "just call the function and check a number":

- Tests are named after the **behaviour**, not the implementation (`test_score_reflects_priority_ordering` not `test_score_is_40`).
- Each test uses **delta assertions** (`score_a - score_b == expected_bonus`) so the exact base value does not have to be hard-coded.
- Edge case `test_score_can_go_negative` verifies an important boundary (LOW + DONE = −40).

### Exercise 2.2 — Due Date Calculation Tests
All five due-date brackets have dedicated tests using the delta approach:

```python
# Example
def test_overdue_task_gets_35_point_boost(self):
    past = datetime.now() - timedelta(days=5)
    task_overdue = make_task(priority=TaskPriority.MEDIUM, due_date=past)
    task_no_due  = make_task(priority=TaskPriority.MEDIUM, due_date=None)
    assert calculate_task_score(task_overdue) - calculate_task_score(task_no_due) == 35
```

A **boundary lesson**: when using `timedelta(days=N)` in tests, two separate `datetime.now()` calls can differ by microseconds. Using `+10 days` rather than `+8 days` for the "beyond 7-day window" test makes the boundary unambiguous.

---

## Part 3 — TDD

### Exercise 3.1 — New Feature: Assigned-User Boost (+12)

**TDD cycle followed:**

1. **Red** — wrote `test_task_assigned_to_current_user_gets_12_point_boost`. It imported `calculate_task_score_with_user` which did not exist → `ImportError`.
2. **Green** — added `calculate_task_score_with_user(task, current_user)` to `task_priority.py`:

```python
def calculate_task_score_with_user(task, current_user=None):
    score = calculate_task_score(task)
    if current_user and getattr(task, "assigned_to", None) == current_user:
        score += 12
    return score
```

3. **Refactor / more tests** — added three regression tests:
   - Other user → no boost
   - `assigned_to=None` → no boost
   - Boost stacks with other bonuses

### Exercise 3.2 — Bug Fix: Days-Since-Update Calculation

**Bug description:** The exercise notes suggest implementations can mistakenly divide by 86,400,000 (milliseconds) instead of using `.days` on a `timedelta`. This would always yield a very large value, breaking the `< 1` guard and never awarding the +5 bonus.

**Test that demonstrates the bug:**

```python
def test_days_since_update_uses_timedelta_days_attribute(self):
    import inspect, task_priority as tp
    source = inspect.getsource(tp.calculate_task_score)
    assert "86400000" not in source   # must NOT divide by ms
    assert ".days" in source           # must use .days
```

**Boundary regression tests added:**
- Task updated 30 minutes ago → +5 ✓
- Task updated 23 hours ago → +5 ✓
- Task updated 2 days ago → no boost ✓

---

## Part 4 — Integration Tests

`TestFullWorkflowIntegration` creates a realistic set of 5 tasks covering every scoring branch (urgent+overdue+critical, high+due-today, medium+next-week, low+no-due, urgent+DONE) and verifies:

| Test | What it checks |
|---|---|
| sort returns highest first | scores are descending after sort |
| DONE tasks sink to bottom | no done task appears before an active task |
| urgent+overdue+critical is #1 | exact top position |
| get_top returns correct count | `limit=3` → 3 tasks |
| limit exceeds list | returns all tasks without error |
| empty input | returns `[]` without exception |
| sort preserves all tasks | no drops or duplicates; IDs match |
| top-N == first-N of sorted | `get_top_priority_tasks` is consistent with `sort_tasks_by_importance` |

---

## Reflection

**What I learned about testing from this exercise:**

1. **Name tests after behaviour, not values.** `test_overdue_task_gets_35_point_boost` tells you exactly what broke; `test_score_equals_55` does not.

2. **Delta assertions are safer than absolute values.** Rather than asserting `score == 55`, asserting `scored_task - base_task == 35` means the test never breaks if an unrelated component of the score changes.

3. **TDD forces you to think before you code.** Writing the test for `calculate_task_score_with_user` before the function existed made the expected API (`task.assigned_to`, `current_user` parameter) crystal-clear before a single line of production code was written.

4. **Boundary conditions are where bugs hide.** The `timedelta.days` test and the 8-day window test both revealed that "obviously correct" code can misbehave at exact boundaries. The microsecond-drift issue with two `datetime.now()` calls in the same test was a real, reproducible bug.

5. **Integration tests catch wiring bugs.** Even with all unit tests passing, the integration test `test_top_tasks_are_subset_of_full_sorted_list` is the only test that verifies the three functions actually compose correctly end-to-end.
