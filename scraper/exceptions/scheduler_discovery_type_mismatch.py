from scraper.schemas.scheduler_task import TaskResult


class SchedulerDiscoveryTypeMismatch(Exception):
	"""
	Exception raised when there is a mismatch between
	the expected type of discovered data and the actual
	type returned by a task.
	"""

	def __init__(
		self,
		message: str,
		target_type: str,
		observed_type: str,
		task_log: str,
		task_result: TaskResult,
	) -> None:
		super().__init__(message)
		self.target_type = target_type
		self.observed_type = observed_type
		self.task_log = task_log
		self.task_result = task_result

	def __str__(self) -> str:
		return super().__str__() + (
			f'\nExpected Type: {self.target_type}\n'
			f'Observed Type: {self.observed_type}\n'
			f'Task Log:\n{self.task_log}\n'
			f'Task Result:\n{
				self.task_result.model_dump_json(indent=2)
			}'
		)
