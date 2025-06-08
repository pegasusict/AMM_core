import time

# import pytest
from Tasks.taskmanager import TaskManager
from Tasks.task import Task
from Enums import TaskType, TaskStatus
# from Singletons.config import Config


# --- Dummy Task Definitions ---


class FastTask(Task):
    def run(self):
        time.sleep(0.1)
        self.set_progress()
        self.result = "done"


class SlowTask(Task):
    def run(self):
        time.sleep(0.5)
        self.set_progress()
        self.result = "slow_done"


class CancelableTask(Task):
    def run(self):
        for _ in range(10):
            time.sleep(0.1)
            self.set_progress()
        self.result = "cancel_test"


# --- Test Cases ---


def test_task_starts_immediately():
    manager = TaskManager()
    manager.set_exclusive_task_types([])  # reset exclusive list
    task_id = manager.start_task(FastTask, TaskType.EXPORTER, [])

    time.sleep(0.2)
    task = manager.get_task(task_id)

    assert task.status == TaskStatus.COMPLETED  # type: ignore
    assert task.progress == 100.0  # type: ignore
    assert task.result == "done"  # type: ignore


def test_task_queued_when_at_limit():
    manager = TaskManager()
    manager.set_exclusive_task_types([])

    limit = manager.max_concurrent_tasks
    task_ids = []

    for _ in range(limit + 1):
        task_id = manager.start_task(SlowTask, TaskType.IMPORTER, [])
        task_ids.append(task_id)

    time.sleep(0.2)
    running = [t for t in manager.list_tasks() if t["alive"]]

    assert len(running) <= limit
    assert len(task_ids) == limit + 1


def test_exclusive_task_type_limit():
    manager = TaskManager()
    manager.set_exclusive_task_types([TaskType.EXPORTER])

    task1_id = manager.start_task(SlowTask, TaskType.EXPORTER, [])
    task2_id = manager.start_task(SlowTask, TaskType.EXPORTER, [])

    time.sleep(0.1)

    running = [t for t in manager.list_tasks() if t["alive"]]
    assert len(running) == 1
    assert running[0]["task_id"] == task1_id

    time.sleep(1.0)
    task2 = manager.get_task(task2_id)
    assert task2.status == TaskStatus.COMPLETED  # type: ignore


def test_task_status_transitions():
    manager = TaskManager()
    task_id = manager.start_task(FastTask, TaskType.CUSTOM, [])

    time.sleep(0.15)
    task = manager.get_task(task_id)

    assert task.status in [TaskStatus.COMPLETED]  # type: ignore
    assert task.duration > 0  # type: ignore
    assert task.end_time > task.start_time  # type: ignore


def test_task_progress_completion():
    manager = TaskManager()
    task_id = manager.start_task(FastTask, TaskType.CUSTOM, [])
    time.sleep(0.2)
    task = manager.get_task(task_id)

    assert task.progress == 100.0  # type: ignore
    assert task.result == "done"  # type: ignore


def test_task_cancel():
    manager = TaskManager()
    task_id = manager.start_task(CancelableTask, TaskType.CUSTOM, [])

    time.sleep(0.2)
    manager.stop_task(task_id)  # type: ignore
    task = manager.get_task(task_id)

    assert task.status == TaskStatus.CANCELLED  # type: ignore
    assert task.result is False  # type: ignore
    assert "cancelled" in task.error.lower()  # type: ignore


def test_shutdown_terminates_tasks():
    manager = TaskManager()
    task_ids = []

    for _ in range(min(3, manager.max_concurrent_tasks)):
        task_id = manager.start_task(SlowTask, TaskType.CUSTOM, [])
        task_ids.append(task_id)

    time.sleep(0.2)
    manager.shutdown()  # type: ignore

    for tid in task_ids:
        task = manager.get_task(tid)
        assert task.status in [TaskStatus.CANCELLED, TaskStatus.FAILED]  # type: ignore
