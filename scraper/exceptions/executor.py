from scraper.schemas.scheduler_task import SchedulerTask


class ExecutorProcessFailure(Exception):
	"""
	Exception raised when a task execution fails.
	"""

	def __init__(
		self,
		message: str,
		task_log: str,
		task: SchedulerTask,
	) -> None:
		super().__init__(message)
		self.task_log = task_log
		self.message = message
		self.task = task

	def __str__(self) -> str:
		return super().__str__() + (
			f'\nTask Log:\n{self.task_log}\n'
			f'Task:\n{self.task.model_dump_json(indent=2)}'
		)

	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}('
			f'message={self.message!r}, '
			f'task_log={self.task_log!r}, '
			f'task={self.task!r})'
		)


class ExecutorProcessingFailure(ExecutorProcessFailure):
	"""
	Exception raised when a specific processing step
	fails during task execution.
	"""
