from scraper.schemas.scheduler_task import SchedulerTask


class SchedulerProcessFailure(Exception):
	"""
	Exception raised when a failure occurs
	during the scheduler process.
	"""

	def __init__(
		self,
		message: str,
		task_log: str,
		task: SchedulerTask,
	) -> None:
		super().__init__(message)
		self.task_log = task_log
		self.task = task

	def __str__(self) -> str:
		return super().__str__() + (
			f'\nTask Log:\n{self.task_log}\n'
			f'Task:\n{self.task.model_dump_json(indent=2)}'
		)
