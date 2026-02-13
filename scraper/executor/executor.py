"""
This module contains the main executor for the scraping
process, which is responsible for executing the scheduled
tasks using the appropriate handlers and managing the
overall scraping workflow.
"""

import logging

from scraper.exceptions.executor import (
	ExecutorProcessFailure,
)
from scraper.executor.handlers.agencies_handler import (
	AgenciesHandler,
)
from scraper.executor.handlers.departments_handler import (
	DepartmentsHandler,
)
from scraper.executor.handlers.faq_handler import FAQHandler
from scraper.executor.handlers.ministries_handler import (
	MinistriesHandler,
)
from scraper.executor.handlers.services_handler import (
	ServicesHandler,
)
from scraper.schemas.scheduler_task import (
	SchedulerTask,
	ScrapingPhase,
	TaskOperation,
	TaskResult,
)
from scraper.scraping.scrape_client import ScrapeClient
from scraper.utils.logging import get_task_log

logger = logging.getLogger(__name__)


class Executor:
	"""
	The main executor class responsible
	for executing scheduled tasks.
	"""

	async def __init__(self) -> None:
		# Scrape client for managing browser
		# interactions
		self.scrape_client = ScrapeClient()
		await self.scrape_client.init_browser()

		# Handlers for different scraping scopes
		self.faq_handler = FAQHandler()
		self.agencies_handler = AgenciesHandler()
		self.ministries_handler = MinistriesHandler()
		self.departments_handler = DepartmentsHandler()
		self.services_handler = ServicesHandler()

		# Scope to handler mapping for routing tasks to the
		self.scope_handler_mapping = {
			ScrapingPhase.FAQ: self._faq_scope,
			ScrapingPhase.AGENCIES_LIST: (
				self._agencies_scope
			),
			ScrapingPhase.MINISTRIES_LIST: (
				self._ministries_list_scope
			),
			ScrapingPhase.MINISTRIES_PAGES: (
				self._ministries_page_scope
			),
			ScrapingPhase.MINISTRIES_SERVICES: (
				self._services_scope
			),
			ScrapingPhase.FINALISATION: (
				self._finalisation_scope
			),
		}

	async def close(self) -> None:
		"""
		Method to close any resources held by the executor,
		such as the scrape client's browser instance.
		"""
		await self.scrape_client.close_browser()

	async def _faq_scope(
		self, task: SchedulerTask
	) -> TaskResult:
		task_log = get_task_log(task)
		if task.operation == TaskOperation.FAQ_SCRAPE:
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting FAQ page scrape '
				'task.',
				extra={'task': task_log},
			)
			_ = await self.faq_handler.scrape_faq_page(
				task_log=task_log,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
			)
		elif task.operation == TaskOperation.FAQ_PROCESS:
			# TODO: Implement FAQ processing logic
			return TaskResult(
				task=task,
				success=False,
			)

		# Raise error if operation is not recognised
		raise ExecutorProcessFailure(
			f'Unrecognized operation {task.operation} for '
			f'FAQ scope.',
			task=task,
			task_log=task_log,
		)

	async def _agencies_scope(
		self, task: SchedulerTask
	) -> TaskResult:
		task_log = get_task_log(task)
		if (
			task.operation
			== TaskOperation.AGENCIES_LIST_SCRAPE
		):
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting agencies list '
				'scrape task.',
				extra={'task': task_log},
			)
			_ = await self.agencies_handler.scrape_agencies_list_page(  # noqa: E501
				task_log=task_log,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
			)
		elif (
			task.operation
			== TaskOperation.AGENCIES_LIST_PROCESS
		):
			# TODO: Implement FAQ processing logic
			return TaskResult(
				task=task,
				success=False,
			)

		# Raise error if operation is not recognised
		raise ExecutorProcessFailure(
			f'Unrecognized operation {task.operation} for '
			f'FAQ scope.',
			task=task,
			task_log=task_log,
		)

	async def _ministries_list_scope(
		self, task: SchedulerTask
	) -> TaskResult:
		task_log = get_task_log(task)
		if (
			task.operation
			== TaskOperation.MINISTRIES_LIST_SCRAPE
		):
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting ministries list '
				'scrape task.',
				extra={'task': task_log},
			)
			_ = await self.ministries_handler.scrape_ministries_list_page(  # noqa: E501
				task_log=task_log,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
			)
		elif (
			task.operation
			== TaskOperation.MINISTRIES_LIST_PROCESS
		):
			# TODO: Implement FAQ processing logic
			return TaskResult(
				task=task,
				success=False,
			)

		# Raise error if operation is not recognised
		raise ExecutorProcessFailure(
			f'Unrecognized operation {task.operation} for '
			f'Ministries list scope.',
			task=task,
			task_log=task_log,
		)

	async def _ministries_page_scope(
		self, task: SchedulerTask
	) -> TaskResult:
		task_log = get_task_log(task)
		if (
			task.operation
			== TaskOperation.MINISTRIES_PAGE_SCRAPE
		):
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting ministries page '
				'scrape task.',
				extra={'task': task_log},
			)
			(
				ministry_services_identifier,
				department_entries,
				ministry_page_agency_data,
			) = await self.ministries_handler.scrape_and_package_ministry_page_data(  # noqa: E501
				ministry_id=task.payload.ministry_id,
				task_log=task_log,
				task=task,
				scrape_client=self.scrape_client,
			)
			# TODO: Push department_entries to departments
			# handler for processing
			# TODO: Push ministry_page_agency_data to
			# agencies handler for processing
			return TaskResult(
				task=task,
				success=True,
				discovered_data=ministry_services_identifier,
			)
		elif (
			task.operation
			== TaskOperation.MINISTRIES_PAGE_PROCESS
		):
			# TODO: Implement processing logic for
			# ministry page data
			return TaskResult(
				task=task,
				success=False,
			)
		# Raise error if operation is not recognised
		raise ExecutorProcessFailure(
			f'Unrecognized operation {task.operation} for '
			f'Ministries page scope.',
			task=task,
			task_log=task_log,
		)

	async def _services_scope(
		self, task: SchedulerTask
	) -> TaskResult:
		task_log = get_task_log(task)
		if (
			task.operation
			== TaskOperation.MINISTRIES_SERVICES_SCRAPE
		):
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting ministries services '
				'scrape task.',
				extra={'task': task_log},
			)
			data = await self.ministries_handler.scrape_and_package_ministry_services_data(  # noqa: E501
				service_task=task.payload,
				task_log=task_log,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
				discovered_data=data,
			)
		elif (
			task.operation
			== TaskOperation.MINISTRIES_SERVICES_PROCESS
		):
			# TODO: Implement processing
			# logic for service page data
			return TaskResult(
				task=task,
				success=False,
			)
		# Raise error if operation is not recognised
		raise ExecutorProcessFailure(
			f'Unrecognized operation {task.operation} for '
			f'Services page scope.',
			task=task,
			task_log=task_log,
		)

	async def _finalisation_scope(
		self, task: SchedulerTask
	) -> TaskResult:
		"""
		Perform finalisation operations after
		all scraping and processing
		"""
		# TODO: Implement any finalisation logic needed
		# such as aggregating results, closing resources
		return TaskResult(
			task=task,
			success=True,
		)

	async def execute_task(
		self,
		task: SchedulerTask,
	) -> TaskResult:
		"""
		Handler for routing and executing
		scheduled tasks based on their
		operation type.
		"""
		try:
			handler = self.scope_handler_mapping.get(
				task.scope,
			)
			if handler is None:
				raise ExecutorProcessFailure(
					f'No handler found for scope '
					f'{task.scope}.',
					task=task,
					task_log=get_task_log(task),
				)
			return await handler(task)
		except Exception as e:
			# Log the error and return a failed TaskResult
			logger.error(
				f'Error executing task: {e!r}',
				extra={'task': get_task_log(task)},
			)
			return TaskResult(
				task=task,
				success=False,
				error_message=str(e),
			)
