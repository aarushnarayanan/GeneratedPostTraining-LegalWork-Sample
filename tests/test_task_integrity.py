"""Offline checks: every task obeys the format and the real-documents rule."""
import pytest

from bench_core.tasks import discover
from bench_core.validate import check_task

TASKS = discover()


def test_tasks_exist():
    assert TASKS


@pytest.mark.parametrize("task_id,task_dir", TASKS, ids=[t[0] for t in TASKS])
def test_task_is_valid(task_id, task_dir):
    assert check_task(task_id, task_dir) == []
