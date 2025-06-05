import time
from src.Tasks.task import Task
from src.Enums import TaskType, TaskStatus
from src.Singletons.config import Config


class DummyTask(Task):
    def run(self):
        for _ in range(3):
            time.sleep(0.05)
            self.set_progress()
        self.result = "done"


def test_task_lifecycle():
    config = Config()
    task = DummyTask(config=config, task_type=TaskType.EXPORTER)

    assert task.status == TaskStatus.PENDING

    task.start()
    task.join()

    assert task.status == TaskStatus.COMPLETED
    assert task.result == "done"
    assert task.progress == 100.0
    assert task.duration > 0
