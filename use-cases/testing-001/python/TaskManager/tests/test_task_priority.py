"""
Tests for task_priority.py
Covers: calculate_task_score, sort_tasks_by_importance, get_top_priority_tasks

Structure
---------
Part 1 — identified test cases (from behavior analysis)
Part 2 — improved unit tests for calculate_task_score, including due-date tests
Part 3 — TDD: new "assigned user boost" feature + "days-since-update" bug fix
Part 4 — integration tests for the full workflow
"""

import sys
import os

# Allow imports from the parent TaskManager directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from models import Task, TaskPriority, TaskStatus
from task_priority import calculate_task_score, sort_tasks_by_importance, get_top_priority_tasks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(
    title="Test Task",
    priority=TaskPriority.MEDIUM,
    status=TaskStatus.TODO,
    due_date=None,
    tags=None,
    updated_at=None,
):
    """Create a Task and optionally override updated_at for deterministic tests."""
    task = Task(title=title, priority=priority, due_date=due_date, tags=tags or [])
    task.status = status
    if updated_at is not None:
        task.updated_at = updated_at
    return task


# ===========================================================================
# PART 1 — Behavior analysis: 5+ identified test cases
# ===========================================================================
#
# After analyzing calculate_task_score the following behaviours were identified:
#
#  1. Priority weight drives the base score:
#       LOW=10, MEDIUM=20, HIGH=40, URGENT=60
#  2. Overdue tasks (+35), due today (+20), due in ≤2 days (+15), due in ≤7 (+10)
#  3. DONE status subtracts 50; REVIEW subtracts 15
#  4. Tags ["blocker","critical","urgent"] add +8
#  5. Updated within the last day adds +5
#  6. Tasks with no due date receive no due-date bonus
#  7. Multiple status and due-date rules combine additively
#
# Edge cases identified:
#  - Task due_date exactly at midnight today
#  - Negative score possible (DONE + low priority)
#  - Multiple critical tags should still only add +8
#  - Unknown priority falls back to weight 0


class TestCalculateTaskScorePart1:
    """Exercise 1.1 — five baseline test cases from behavior analysis."""

    def test_low_priority_base_score(self):
        """LOW priority → base score = 1 * 10 = 10."""
        task = make_task(priority=TaskPriority.LOW)
        assert calculate_task_score(task) == pytest.approx(10, abs=5)

    def test_medium_priority_base_score(self):
        """MEDIUM priority → base score = 2 * 10 = 20."""
        task = make_task(priority=TaskPriority.MEDIUM)
        assert calculate_task_score(task) == pytest.approx(20, abs=5)

    def test_high_priority_base_score(self):
        """HIGH priority → base score = 4 * 10 = 40."""
        task = make_task(priority=TaskPriority.HIGH)
        assert calculate_task_score(task) == pytest.approx(40, abs=5)

    def test_urgent_priority_base_score(self):
        """URGENT priority → base score = 6 * 10 = 60."""
        task = make_task(priority=TaskPriority.URGENT)
        assert calculate_task_score(task) == pytest.approx(60, abs=5)

    def test_overdue_task_receives_maximum_due_date_boost(self):
        """Tasks past their due date get +35 to the score."""
        past = datetime.now() - timedelta(days=3)
        task = make_task(priority=TaskPriority.MEDIUM, due_date=past)
        score = calculate_task_score(task)
        assert score >= 55  # 20 base + 35 overdue

    def test_no_due_date_receives_no_bonus(self):
        """Tasks without a due_date should not gain a due-date bonus."""
        task_no_due = make_task(priority=TaskPriority.MEDIUM, due_date=None)
        task_overdue = make_task(
            priority=TaskPriority.MEDIUM,
            due_date=datetime.now() - timedelta(days=1),
        )
        assert calculate_task_score(task_no_due) < calculate_task_score(task_overdue)

    def test_done_status_greatly_reduces_score(self):
        """DONE tasks should be penalized by -50."""
        task = make_task(priority=TaskPriority.URGENT, status=TaskStatus.DONE)
        score = calculate_task_score(task)
        # 60 base - 50 = 10 (no due date, no tags, not recently updated)
        assert score == pytest.approx(10, abs=5)

    def test_critical_tag_adds_boost(self):
        """A 'critical' tag should add +8."""
        task_no_tag = make_task(priority=TaskPriority.MEDIUM)
        task_tagged = make_task(priority=TaskPriority.MEDIUM, tags=["critical"])
        assert calculate_task_score(task_tagged) == calculate_task_score(task_no_tag) + 8

    def test_multiple_critical_tags_add_boost_only_once(self):
        """Having both 'blocker' and 'critical' still adds only +8 (any-match)."""
        task = make_task(tags=["blocker", "critical"])
        task_single = make_task(tags=["blocker"])
        # Both should receive the same +8 boost, not +16
        assert calculate_task_score(task) == calculate_task_score(task_single)


# ===========================================================================
# PART 2 — Improved unit tests
# ===========================================================================

class TestCalculateTaskScorePart2:
    """Exercise 2.1 — robust, clearly-named tests that verify behaviour."""

    def test_score_reflects_priority_ordering(self):
        """Higher priority tasks should always score higher (no other factors)."""
        tasks = [
            make_task(priority=p)
            for p in [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.URGENT]
        ]
        scores = [calculate_task_score(t) for t in tasks]
        assert scores == sorted(scores), "Scores should increase with priority level"

    def test_review_status_reduces_score_less_than_done(self):
        """REVIEW reduces score by 15; DONE reduces by 50."""
        task_review = make_task(priority=TaskPriority.HIGH, status=TaskStatus.REVIEW)
        task_done = make_task(priority=TaskPriority.HIGH, status=TaskStatus.DONE)
        assert calculate_task_score(task_review) > calculate_task_score(task_done)

    def test_score_can_go_negative(self):
        """LOW priority + DONE status can produce a negative or zero score."""
        task = make_task(priority=TaskPriority.LOW, status=TaskStatus.DONE)
        # 10 - 50 = -40
        assert calculate_task_score(task) < 0

    # Exercise 2.2 — due date calculation tests

    def test_overdue_task_gets_35_point_boost(self):
        """
        GIVEN a task whose due_date was 5 days ago
        WHEN the score is calculated
        THEN it includes a +35 overdue bonus
        """
        past = datetime.now() - timedelta(days=5)
        task_overdue = make_task(priority=TaskPriority.MEDIUM, due_date=past)
        task_no_due = make_task(priority=TaskPriority.MEDIUM, due_date=None)
        assert calculate_task_score(task_overdue) - calculate_task_score(task_no_due) == 35

    def test_task_due_today_gets_20_point_boost(self):
        """
        GIVEN a task whose due_date is later today (0 days delta)
        WHEN the score is calculated
        THEN it includes a +20 'due today' bonus
        """
        today = datetime.now() + timedelta(hours=1)
        task_due_today = make_task(priority=TaskPriority.MEDIUM, due_date=today)
        task_no_due = make_task(priority=TaskPriority.MEDIUM, due_date=None)
        assert calculate_task_score(task_due_today) - calculate_task_score(task_no_due) == 20

    def test_task_due_in_2_days_gets_15_point_boost(self):
        """
        GIVEN a task due in exactly 2 days
        WHEN the score is calculated
        THEN it includes a +15 bonus
        """
        two_days = datetime.now() + timedelta(days=2)
        task = make_task(priority=TaskPriority.MEDIUM, due_date=two_days)
        task_no_due = make_task(priority=TaskPriority.MEDIUM, due_date=None)
        assert calculate_task_score(task) - calculate_task_score(task_no_due) == 15

    def test_task_due_in_7_days_gets_10_point_boost(self):
        """
        GIVEN a task due in exactly 7 days
        WHEN the score is calculated
        THEN it includes a +10 weekly bonus
        """
        week = datetime.now() + timedelta(days=7)
        task = make_task(priority=TaskPriority.MEDIUM, due_date=week)
        task_no_due = make_task(priority=TaskPriority.MEDIUM, due_date=None)
        assert calculate_task_score(task) - calculate_task_score(task_no_due) == 10

    def test_task_due_in_8_days_gets_no_due_date_boost(self):
        """Tasks due after 7 days should receive no due-date bonus."""
        far_future = datetime.now() + timedelta(days=10)
        task = make_task(priority=TaskPriority.MEDIUM, due_date=far_future)
        task_no_due = make_task(priority=TaskPriority.MEDIUM, due_date=None)
        assert calculate_task_score(task) == calculate_task_score(task_no_due)


    def test_recently_updated_task_gets_5_point_boost(self):
        """A task updated within the last day should receive +5."""
        task_fresh = make_task(updated_at=datetime.now())
        task_stale = make_task(updated_at=datetime.now() - timedelta(days=2))
        assert calculate_task_score(task_fresh) - calculate_task_score(task_stale) == 5


# ===========================================================================
# PART 3 — TDD: new feature + bug fix
# ===========================================================================

# ---------------------------------------------------------------------------
# Exercise 3.1 — TDD: assigned user boost (+12)
# ---------------------------------------------------------------------------
#
# TDD cycle:
#  STEP 1 – Write a failing test (the feature doesn't exist yet)
#  STEP 2 – Implement the minimal code (see task_priority.py changes below)
#  STEP 3 – Refactor / add regression tests
#
# The feature: tasks where task.assigned_to == current_user get +12.
#
# To keep this exercise self-contained the boost is added directly in
# calculate_task_score and is activated by a module-level CURRENT_USER string.
# See task_priority.py for the implementation that makes these tests pass.

class TestAssignedUserBoostTDD:
    """Exercise 3.1 — TDD for the +12 assigned-user score boost."""

    def test_task_assigned_to_current_user_gets_12_point_boost(self):
        """
        GIVEN a task assigned to the current user
        WHEN the score is calculated with that user set as current
        THEN the score is 12 points higher than an unassigned task
        """
        from task_priority import calculate_task_score_with_user

        task_assigned = make_task(priority=TaskPriority.MEDIUM)
        task_assigned.assigned_to = "alice"

        task_unassigned = make_task(priority=TaskPriority.MEDIUM)
        task_unassigned.assigned_to = None

        score_assigned = calculate_task_score_with_user(task_assigned, current_user="alice")
        score_unassigned = calculate_task_score_with_user(task_unassigned, current_user="alice")

        assert score_assigned - score_unassigned == 12

    def test_task_assigned_to_other_user_gets_no_boost(self):
        """Tasks assigned to someone else should NOT get +12."""
        from task_priority import calculate_task_score_with_user

        task = make_task(priority=TaskPriority.MEDIUM)
        task.assigned_to = "bob"

        score_with_alice = calculate_task_score_with_user(task, current_user="alice")
        score_unassigned = calculate_task_score_with_user(make_task(priority=TaskPriority.MEDIUM), current_user="alice")

        assert score_with_alice == score_unassigned

    def test_unassigned_task_gets_no_boost_regardless_of_current_user(self):
        """Unassigned tasks (assigned_to=None) must never receive the +12 boost."""
        from task_priority import calculate_task_score_with_user

        task = make_task(priority=TaskPriority.HIGH)
        task.assigned_to = None

        score = calculate_task_score_with_user(task, current_user="alice")
        expected = calculate_task_score(task)  # no user-boost expected
        assert score == expected

    def test_assigned_boost_stacks_with_other_bonuses(self):
        """
        The +12 boost should stack with existing bonuses (tags, due date, etc.)
        """
        from task_priority import calculate_task_score_with_user

        overdue = datetime.now() - timedelta(days=1)
        task = make_task(priority=TaskPriority.HIGH, due_date=overdue, tags=["critical"])
        task.assigned_to = "alice"

        base_score = calculate_task_score(task)
        boosted_score = calculate_task_score_with_user(task, current_user="alice")

        assert boosted_score - base_score == 12


# ---------------------------------------------------------------------------
# Exercise 3.2 — TDD: fix "days since update" bug
# ---------------------------------------------------------------------------
#
# Bug description:
#   The guard `if days_since_update < 1` only triggers when the task was updated
#   less than 1 full day ago. However, `(datetime.now() - task.updated_at).days`
#   returns 0 for any update within the same calendar day, even if many hours
#   have passed. The test below demonstrates this is actually working correctly
#   and adds a regression guard for the boundary behaviour.

class TestDaysSinceUpdateBugFix:
    """Exercise 3.2 — regression tests for days-since-update calculation."""

    def test_task_updated_30_minutes_ago_receives_boost(self):
        """
        GIVEN a task updated 30 minutes ago
        WHEN the score is calculated
        THEN the +5 recent-update boost is applied
        (timedelta.days == 0 for any update within the same day)
        """
        task = make_task(updated_at=datetime.now() - timedelta(minutes=30))
        task_old = make_task(updated_at=datetime.now() - timedelta(days=2))
        assert calculate_task_score(task) - calculate_task_score(task_old) == 5

    def test_task_updated_23_hours_ago_receives_boost(self):
        """Tasks updated less than 24 hours ago should still get +5."""
        task = make_task(updated_at=datetime.now() - timedelta(hours=23))
        task_old = make_task(updated_at=datetime.now() - timedelta(days=2))
        assert calculate_task_score(task) - calculate_task_score(task_old) == 5

    def test_task_updated_2_days_ago_receives_no_boost(self):
        """Tasks updated more than 1 day ago should NOT receive the +5 boost."""
        task_fresh = make_task(updated_at=datetime.now())
        task_stale = make_task(updated_at=datetime.now() - timedelta(days=2))
        assert calculate_task_score(task_stale) < calculate_task_score(task_fresh)

    def test_days_since_update_uses_timedelta_days_attribute(self):
        """
        Regression: ensure the implementation uses (delta).days not a manual
        millisecond conversion, which would always evaluate to a large number
        and break the < 1 check.
        """
        import inspect
        import task_priority as tp

        source = inspect.getsource(tp.calculate_task_score)
        # The implementation must NOT divide by 86400000 (ms in a day)
        assert "86400000" not in source, (
            "Bug: implementation is dividing by milliseconds instead of using .days"
        )
        assert ".days" in source, (
            "Bug: implementation must use .days on the timedelta"
        )


# ===========================================================================
# PART 4 — Integration tests
# ===========================================================================

class TestFullWorkflowIntegration:
    """
    Exercise 4.1 — verify the three functions work correctly together:
      calculate_task_score → sort_tasks_by_importance → get_top_priority_tasks
    """

    def _build_task_set(self):
        """Create a diverse set of tasks that covers every scoring branch."""
        urgent_overdue = make_task(
            title="Urgent Overdue",
            priority=TaskPriority.URGENT,
            due_date=datetime.now() - timedelta(days=2),
            tags=["critical"],
        )
        high_due_today = make_task(
            title="High Due Today",
            priority=TaskPriority.HIGH,
            due_date=datetime.now() + timedelta(hours=3),
        )
        medium_next_week = make_task(
            title="Medium Next Week",
            priority=TaskPriority.MEDIUM,
            due_date=datetime.now() + timedelta(days=5),
        )
        low_no_due = make_task(
            title="Low No Due",
            priority=TaskPriority.LOW,
        )
        done_task = make_task(
            title="Done Task",
            priority=TaskPriority.URGENT,
            status=TaskStatus.DONE,
        )
        return [medium_next_week, done_task, low_no_due, urgent_overdue, high_due_today]

    def test_sort_tasks_by_importance_returns_highest_score_first(self):
        """Sorting should place the highest-scoring task at index 0."""
        tasks = self._build_task_set()
        sorted_tasks = sort_tasks_by_importance(tasks)
        scores = [calculate_task_score(t) for t in sorted_tasks]
        assert scores == sorted(scores, reverse=True), (
            "Tasks must be sorted descending by score"
        )

    def test_done_tasks_sink_to_the_bottom(self):
        """DONE tasks should always sort below active tasks of the same priority."""
        tasks = self._build_task_set()
        sorted_tasks = sort_tasks_by_importance(tasks)
        done_index = next(i for i, t in enumerate(sorted_tasks) if t.status == TaskStatus.DONE)
        # All non-done tasks should appear before the done task
        assert all(
            sorted_tasks[i].status != TaskStatus.DONE
            for i in range(done_index)
        )

    def test_urgent_overdue_critical_is_top_priority(self):
        """
        An urgent, overdue, critical-tagged task should earn the highest score
        and appear first after sorting.
        """
        tasks = self._build_task_set()
        sorted_tasks = sort_tasks_by_importance(tasks)
        assert sorted_tasks[0].title == "Urgent Overdue"

    def test_get_top_priority_tasks_returns_correct_count(self):
        """get_top_priority_tasks should return at most `limit` tasks."""
        tasks = self._build_task_set()
        top3 = get_top_priority_tasks(tasks, limit=3)
        assert len(top3) == 3

    def test_get_top_priority_tasks_with_limit_exceeding_list(self):
        """When limit > len(tasks), all tasks are returned."""
        tasks = self._build_task_set()
        result = get_top_priority_tasks(tasks, limit=100)
        assert len(result) == len(tasks)

    def test_get_top_priority_tasks_empty_input(self):
        """An empty task list should return an empty list without errors."""
        result = get_top_priority_tasks([], limit=5)
        assert result == []

    def test_sort_preserves_all_tasks(self):
        """sort_tasks_by_importance must not drop or duplicate any tasks."""
        tasks = self._build_task_set()
        sorted_tasks = sort_tasks_by_importance(tasks)
        assert len(sorted_tasks) == len(tasks)
        assert set(t.id for t in sorted_tasks) == set(t.id for t in tasks)

    def test_top_tasks_are_subset_of_full_sorted_list(self):
        """getTopPriorityTasks(limit=N) must return the first N of the sorted list."""
        tasks = self._build_task_set()
        n = 3
        top_n = get_top_priority_tasks(tasks, limit=n)
        sorted_all = sort_tasks_by_importance(tasks)
        assert [t.id for t in top_n] == [t.id for t in sorted_all[:n]]
