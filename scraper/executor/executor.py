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
	MinistryIdentifier,
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
			await self.faq_handler.scrape_faq_page(
				task_log=task_log,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
			)
		elif task.operation == TaskOperation.FAQ_PROCESS:
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting FAQ page process '
				'task.',
				extra={'task': task_log},
			)
			self.faq_handler.process_faq_page(
				task_log=task_log,
				task=task,
			)
			return TaskResult(
				task=task,
				success=True,
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
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting agencies list '
				'process task.',
				extra={'task': task_log},
			)
			self.agencies_handler.process_agencies_list_data(
				task_log=task_log,
				task=task,
			)
			return TaskResult(
				task=task,
				success=True,
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
			await self.ministries_handler.scrape_ministries_list_page(  # noqa: E501
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
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting ministries list '
				'process task.',
				extra={'task': task_log},
			)
			ministry_identifiers = self.ministries_handler.process_ministries_list_data(  # noqa: E501
				task_log=task_log,
				task=task,
			)
			return TaskResult(
				task=task,
				success=True,
				discovered_data=ministry_identifiers,
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
			page_data = await self.ministries_handler.scrape_ministry_page(  # noqa: E501
				ministry_id=task.payload.ministry_id,
				task_log=task_log,
				task=task,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
				discovered_data=MinistryIdentifier(
					ministry_id=page_data.ministry_id
				),
			)
		elif (
			task.operation
			== TaskOperation.MINISTRIES_PAGE_PROCESS
		):
			"""
			Note that the main processing for each ministry
			page happens as the data is scraped, as we apply
			the processing recipes to extract and structure
			the data to inform the next steps of the
			scheduler. This step assures that all page data
			is processed into structured data in state
			before we proceed to the next steps.
			"""
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting ministries page '
				'process task.',
				extra={'task': task_log},
			)
			# Batch processing of all ministries page data
			# to ensure all data is processed before moving
			# to next step in scheduler. This is because
			# the processing step is where we extract the
			# structured data needed to inform the next
			# steps of the scheduler.
			(
				ministry_services_identifiers_list,
				department_entry_list,
				ministry_page_agency_data_list,
			) = await self.ministries_handler.process_ministries_pages_data(  # noqa: E501
				ministry_task_list=task.payload,
				task_log=task_log,
				task=task,
			)
			# TODO: Push department_entries to departments
			# handler for processing
			# TODO: Push ministry_page_agency_data to
			# agencies handler for processing
			return TaskResult(
				task=task,
				success=True,
				discovered_data=ministry_services_identifiers_list,
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
			services_scraped_identifier = await self.ministries_handler.scrape_and_package_ministry_services_data(  # noqa: E501
				service_task=task.payload,
				task_log=task_log,
				scrape_client=self.scrape_client,
			)
			return TaskResult(
				task=task,
				success=True,
				discovered_data=services_scraped_identifier,
			)
		elif (
			task.operation
			== TaskOperation.MINISTRIES_SERVICES_PROCESS
		):
			logger.info(
				'[EXECUTOR]\n'
				'[TASK INFO]: Starting ministries services '
				'process task.',
				extra={'task': task_log},
			)
			(
				services_processed_identifier,
				service_entries_list,
			) = await self.ministries_handler.process_service_task_list(  # noqa: E501
				service_task_list=task.payload,
				task_log=task_log,
				task=task,
			)

			# TODO: Push processed service data to services
			# handler for further processing and structuring
			return TaskResult(
				task=task,
				success=True,
				discovered_data=services_processed_identifier,
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
