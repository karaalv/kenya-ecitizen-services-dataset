from scraper.schemas.scheduler_task import TaskResult


class SchedulerPhaseFailure(Exception):
	"""
	Exception raised when a failure occurs
	during a scheduler phase.
	"""

	def __init__(
		self,
		message: str,
		task_log: str,
		task_result: TaskResult,
	) -> None:
		super().__init__(message)
		self.task_log = task_log
		self.task_result = task_result

	def __str__(self) -> str:
		return super().__str__() + (
			f'\nTask Log:\n{self.task_log}\n'
			f'Task Result:\n{
				self.task_result.model_dump_json(indent=2)
			}'
		)
