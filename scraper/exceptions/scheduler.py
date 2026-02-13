from scraper.schemas.scheduler_task import (
	SchedulerTask,
	TaskResult,
)


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

	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}('
			f'message={self.args[0]!r}, '
			f'task_log={self.task_log!r}, '
			f'task={self.task!r})'
		)


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

	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}('
			f'message={self.args[0]!r}, '
			f'task_log={self.task_log!r}, '
			f'task_result={self.task_result!r})'
		)


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

	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}('
			f'message={self.args[0]!r}, '
			f'target_type={self.target_type!r}, '
			f'observed_type={self.observed_type!r}, '
			f'task_log={self.task_log!r}, '
			f'task_result={self.task_result!r})'
		)
