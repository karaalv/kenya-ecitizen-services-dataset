"""
Scheduler class to manage the scraping process,
including task scheduling and state management.
"""

import logging
from collections import deque

from scraper.classes.scheduler.scheduler_state import (
	SchedulerStateManager,
)
from scraper.schemas.scheduler_state import (
	MinistryState,
	SchedulerState,
	ScrapingPhase,
)
from scraper.schemas.scheduler_task import (
	EmptyPayload,
	MinistryIdentifiers,
	MinistryServicesIdentifier,
	MinistryTaskListPayload,
	MinistryTaskPayload,
	SchedulerTask,
	ServicesProcessedIdentifier,
	ServicesScrapedIdentifier,
	ServiceTaskListPayload,
	ServiceTaskPayload,
	TaskOperation,
	TaskResult,
)

# logger instance for the scheduler module
logger = logging.getLogger(__name__)


class Scheduler:
	"""
	Scheduler class to manage the scraping process,
	including task scheduling and state management.
	"""

	# TODO: Add reducers for managing state updates based on
	# completed tasks and discovered data

	def __init__(self):
		logger.info('Initializing Scheduler')
		# State manager
		self._state_manager = SchedulerStateManager()
		# Queues for ministries page scraping and
		# processing tasks
		self._ministries_page_scrape_queue: deque[
			MinistryState
		] = self._initialize_ministries_page_scrape_queue(
			self._state_manager.get_state()
		)
		self._ministries_services_queue: deque[
			tuple[str, deque[ServiceTaskPayload]]
		] = self._initialise_ministries_services_queue(
			self._state_manager.get_state()
		)
		# Reducers for applying task results to update state
		self._reducers = {
			ScrapingPhase.FAQ: (self._r_faq),
			ScrapingPhase.AGENCIES_LIST: (
				self._r_agencies_list
			),
			ScrapingPhase.MINISTRIES_LIST: (
				self._r_ministries_list
			),
			ScrapingPhase.MINISTRIES_PAGES: (
				self._r_ministries_pages
			),
			ScrapingPhase.MINISTRIES_SERVICES: (
				self._r_ministries_services
			),
			ScrapingPhase.FINALISATION: (
				self._r_finalisation
			),
		}

	# --- Queue initialization methods ---

	def _initialize_ministries_page_scrape_queue(
		self, state: SchedulerState
	) -> deque[MinistryState]:
		"""
		Initialize the queue of ministries pages
		to be scraped based on the current state.
		"""
		incomplete_ministries = [
			m
			for m in state.ministries_detail.values()
			if not m.complete
		]
		ministries = [
			m
			for m in incomplete_ministries
			if not m.page.scraped
		]
		return deque(ministries)

	def _initialise_ministries_services_queue(
		self, state: SchedulerState
	) -> deque[tuple[str, deque[ServiceTaskPayload]]]:
		"""
		Initialize the queue of ministries services
		to be scraped based on the current state.
		"""
		incomplete_ministries = [
			m
			for m in state.ministries_detail.values()
			if not m.complete
		]
		ministries = [
			m
			for m in incomplete_ministries
			if not m.services.scraped
		]
		ministry_services_queue_registry: deque[
			tuple[str, deque[ServiceTaskPayload]]
		] = deque()
		for m in ministries:
			ministry_services_queue = deque()
			for d in m.departments.values():
				for a in d.agencies.values():
					if not a.state.scraped:
						ministry_services_queue.append(
							ServiceTaskPayload(
								ministry_id=m.ministry_id,
								department_id=d.department_id,
								agency_id=a.agency_id,
								ministry_departments_agencies_url=(
									a.ministry_departments_agencies_url
								),
							)
						)
			ministry_services_queue_registry.append(
				(m.ministry_id, ministry_services_queue)
			)

		return ministry_services_queue_registry

	# --- Queue update methods based on task results ---
	def _pop_page_scrape_queue(
		self, ministry_id: str
	) -> None:
		"""
		Pop the ministry with the given ID from the
		ministries page scrape queue, if it is at the
		front of the queue.
		"""
		if (
			self._ministries_page_scrape_queue
			and self._ministries_page_scrape_queue[
				0
			].ministry_id
			== ministry_id
		):
			self._ministries_page_scrape_queue.popleft()

	def _pop_service_scrape_queue(
		self,
		ministry_id: str,
		department_id: str,
		agency_id: str,
	) -> None:
		"""
		Pop the service with the given ministry, department
		and agency IDs from the ministries services scrape
		queue, if it is at the front of the queue for the
		corresponding ministry.
		"""
		if (
			self._ministries_services_queue
			and self._ministries_services_queue[0][0]
			== ministry_id
		):
			services_queue = (
				self._ministries_services_queue[0][1]
			)
			if (
				services_queue
				and services_queue[0].department_id
				== department_id
				and services_queue[0].agency_id == agency_id
			):
				services_queue.popleft()

	def _pop_service_processing_queue(
		self, ministry_id: str
	) -> None:
		"""
		Pop the ministry with the given ID from the
		ministries services processing queue, if it is at
		the front of the queue.
		"""
		if (
			self._ministries_services_queue
			and self._ministries_services_queue[0][0]
			== ministry_id
		):
			self._ministries_services_queue.popleft()

	# --- State update methods for task results ---

	def _apply_ministries_list_processing_result(
		self,
		ministry_identifiers: MinistryIdentifiers,
	) -> None:
		"""
		Update the state with the discovered ministry
		identifiers from the ministries list processing
		task, and update the ministries page scrape
		queue accordingly.
		"""

		ministry_ids = ministry_identifiers.ministry_ids

		# Apply to state
		self._state_manager.apply_ministries_list_state(
			ministry_ids=ministry_ids
		)

		# Apply to scrape queue
		state = self._state_manager.get_state()
		self._ministries_page_scrape_queue = (
			self._initialize_ministries_page_scrape_queue(
				state
			)
		)

	def _apply_ministry_services_identifier(self) -> None:
		"""
		Update the queue for ministries services scraping
		with the discovered ministry services identifier
		from the ministry page scraping task.
		"""
		state = self._state_manager.get_state()
		self._ministries_services_queue = (
			self._initialise_ministries_services_queue(
				state
			)
		)

	# --- Task payload generation methods ---

	def _get_ministry_pages_to_process(
		self, state: SchedulerState
	) -> MinistryTaskListPayload:
		"""
		Get the list of ministries that still need their
		detail pages processed.
		"""
		incomplete_ministries = [
			m
			for m in state.ministries_detail.values()
			if not m.complete
		]
		ministries_to_process = [
			m
			for m in incomplete_ministries
			if not m.page.processed
		]
		return MinistryTaskListPayload(
			ministry_ids=[
				MinistryTaskPayload(
					ministry_id=m.ministry_id
				)
				for m in ministries_to_process
			]
		)

	def _get_ministry_services_to_process(
		self, ministry_id: str
	) -> ServiceTaskListPayload:
		"""
		Get the list of services that still need to be
		processed for the ministry services phase.
		"""
		state = self._state_manager.get_state()

		ministries_with_services_to_process = [
			m
			for m in state.ministries_detail.values()
			if not m.complete
			and not m.services.processed
			and m.ministry_id == ministry_id
		]

		service_tasks: list[ServiceTaskPayload] = []
		for m in ministries_with_services_to_process:
			for d in m.departments.values():
				for a in d.agencies.values():
					if not a.state.processed:
						service_tasks.append(
							ServiceTaskPayload(
								ministry_id=m.ministry_id,
								department_id=d.department_id,
								agency_id=a.agency_id,
								ministry_departments_agencies_url=(
									a.ministry_departments_agencies_url
								),
							)
						)

		return ServiceTaskListPayload(
			service_tasks=service_tasks
		)

	# --- Next task determination methods ---

	def _next_ministry_page_scrape_task(
		self,
	) -> SchedulerTask | None:
		"""
		Determine the next ministry page scrape task
		based on the queue of ministries to be scraped.
		"""
		if not self._ministries_page_scrape_queue:
			return None

		# Peek at the next ministry to scrape without
		# removing it from the queue yet, as we only
		# want to remove it once the task is completed and
		# the state is updated accordingly
		next_ministry = self._ministries_page_scrape_queue[
			0
		]
		return SchedulerTask(
			scope=ScrapingPhase.MINISTRIES_PAGES,
			operation=TaskOperation.MINISTRIES_PAGE_SCRAPE,
			payload=MinistryTaskPayload(
				ministry_id=next_ministry.ministry_id,
			),
		)

	def _next_ministry_service_task(
		self,
	) -> SchedulerTask | None:
		"""
		Determine the next ministry service to scrape and
		process based on the current state and the queue
		of ministries and their services.
		"""
		if not self._ministries_services_queue:
			return None

		next_ministry_id, services_queue = (
			self._ministries_services_queue[0]
		)
		if not services_queue:
			# If there are no services to scrape for this
			# ministry, proceed to processing tasks for
			# the ministry, and remove the ministry from
			# the queue as its scraping tasks are complete
			# (done on task completion and state update)
			return SchedulerTask(
				scope=ScrapingPhase.MINISTRIES_SERVICES,
				operation=TaskOperation.MINISTRIES_SERVICES_PROCESS,
				payload=self._get_ministry_services_to_process(
					next_ministry_id
				),
			)
		else:
			# We peek at the next service to scrape without
			# removing it from the queue yet, we update the
			# queue and state once the task is completed and
			# the service is marked as scraped in the state
			next_service = services_queue[0]
			return SchedulerTask(
				scope=ScrapingPhase.MINISTRIES_SERVICES,
				operation=TaskOperation.MINISTRIES_SERVICES_SCRAPE,
				payload=next_service,
			)

	def next_task(self) -> SchedulerTask | None:
		"""
		Using the current state, determine the
		next task to be executed.
		"""
		state: SchedulerState = (
			self._state_manager.get_state()
		)

		# FAQ phase
		if not state.faq.scraped:
			return SchedulerTask(
				scope=ScrapingPhase.FAQ,
				operation=TaskOperation.FAQ_SCRAPE,
				payload=EmptyPayload(),
			)

		if not state.faq.processed:
			return SchedulerTask(
				scope=ScrapingPhase.FAQ,
				operation=TaskOperation.FAQ_PROCESS,
				payload=EmptyPayload(),
			)

		# Agencies list phase
		if not state.agencies_list.scraped:
			return SchedulerTask(
				scope=ScrapingPhase.AGENCIES_LIST,
				operation=TaskOperation.AGENCIES_LIST_SCRAPE,
				payload=EmptyPayload(),
			)

		if not state.agencies_list.processed:
			return SchedulerTask(
				scope=ScrapingPhase.AGENCIES_LIST,
				operation=TaskOperation.AGENCIES_LIST_PROCESS,
				payload=EmptyPayload(),
			)

		# Ministries list phase
		if not state.ministries_list.scraped:
			return SchedulerTask(
				scope=ScrapingPhase.MINISTRIES_LIST,
				operation=TaskOperation.MINISTRIES_LIST_SCRAPE,
				payload=EmptyPayload(),
			)

		if not state.ministries_list.processed:
			return SchedulerTask(
				scope=ScrapingPhase.MINISTRIES_LIST,
				operation=TaskOperation.MINISTRIES_LIST_PROCESS,
				payload=EmptyPayload(),
			)

		# Ministries page phase
		if not state.ministry_pages.scraped:
			task = self._next_ministry_page_scrape_task()
			if task:
				return task
			else:
				# If no more ministry pages to scrape,
				# move state to ministry page processing
				return SchedulerTask(
					scope=ScrapingPhase.MINISTRIES_PAGES,
					operation=TaskOperation.UPDATE_TO_MINISTRY_PAGE_PROCESSING,
					payload=EmptyPayload(),
				)

		if not state.ministry_pages.processed:
			return SchedulerTask(
				scope=ScrapingPhase.MINISTRIES_PAGES,
				operation=TaskOperation.MINISTRIES_PAGE_PROCESS,
				payload=self._get_ministry_pages_to_process(
					state
				),
			)

		# Ministries services phase
		if not state.ministry_services.scraped:
			task = self._next_ministry_service_task()
			if task:
				return task
			else:
				# If no more ministry services to scrape,
				# move to finalisation phase
				return SchedulerTask(
					scope=ScrapingPhase.MINISTRIES_SERVICES,
					operation=TaskOperation.UPDATE_TO_FINALISATION_PHASE,
					payload=EmptyPayload(),
				)

		# Finalisation phase
		if not state.finalisation_checks:
			return SchedulerTask(
				scope=ScrapingPhase.FINALISATION,
				operation=TaskOperation.FINALISATION_PHASE,
				payload=EmptyPayload(),
			)

		# If all tasks are complete, return None
		return None

	# --- Task result reducer methods ---

	def _r_faq(self, result: TaskResult) -> None:
		"""
		Reducer to handle the result of FAQ scraping
		and processing tasks and update the state
		accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.FAQ_SCRAPE
		):
			if result.success:
				self._state_manager.update_faq_state(
					scraped=True
				)
			else:
				logger.error(
					'FAQ scraping task failed: %s',
					result.error_message,
				)
		elif (
			result.task.operation
			== TaskOperation.FAQ_PROCESS
		):
			if result.success:
				self._state_manager.update_faq_state(
					processed=True
				)
			else:
				logger.error(
					'FAQ processing task failed: %s',
					result.error_message,
				)

	def _r_agencies_list(self, result: TaskResult) -> None:
		"""
		Reducer to handle the result of agencies list
		scraping and processing tasks and update the state
		accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.AGENCIES_LIST_SCRAPE
		):
			if result.success:
				self._state_manager.update_agencies_list_state(
					scraped=True
				)
			else:
				logger.error(
					'Agencies list scraping task '
					'failed: %s',
					result.error_message,
				)
		elif (
			result.task.operation
			== TaskOperation.AGENCIES_LIST_PROCESS
		):
			if result.success:
				self._state_manager.update_agencies_list_state(
					processed=True
				)
			else:
				logger.error(
					'Agencies list processing task '
					'failed: %s',
					result.error_message,
				)

	def _r_ministries_list(
		self, result: TaskResult
	) -> None:
		"""
		Reducer to handle the result of ministries list
		scraping and processing tasks and update the state
		accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.MINISTRIES_LIST_SCRAPE
		):
			if result.success:
				self._state_manager.update_ministries_list_state(
					scraped=True
				)
			else:
				logger.error(
					'Ministries list scraping task '
					'failed: %s',
					result.error_message,
				)
		elif (
			result.task.operation
			== TaskOperation.MINISTRIES_LIST_PROCESS
		):
			if result.success:
				self._state_manager.update_ministries_list_state(
					processed=True
				)
				# Apply discovered ministries to state
				# and update the ministries page scrape
				# queue
				ministry_identifiers = (
					result.discovered_data
				)
				if isinstance(
					ministry_identifiers,
					MinistryIdentifiers,
				):
					self._apply_ministries_list_processing_result(
						ministry_identifiers=ministry_identifiers
					)
				else:
					# TODO: Throw error for unexpected
					# discovered data type
					pass
			else:
				logger.error(
					'Ministries list processing task '
					'failed: %s',
					result.error_message,
				)

	def _r_ministries_pages(
		self, result: TaskResult
	) -> None:
		"""
		Reducer to handle the result of ministries page
		scraping and processing tasks and update the state
		accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.MINISTRIES_PAGE_SCRAPE
		):
			if result.success:
				# Update the state to mark the ministry page
				# as scraped, and update the scrape queue
				# update the ministry service information
				# with the discovered data from scraping,
				# which includes the departments and
				# agencies under the ministry, as well as
				# their identifiers and URLs
				ministry_identifier = result.discovered_data
				if isinstance(
					ministry_identifier,
					MinistryServicesIdentifier,
				):
					ministry_id = (
						ministry_identifier.ministry_id
					)
					self._state_manager.update_ministry_page_scraped_state(
						ministry_id=ministry_id
					)
					self._state_manager._apply_ministry_services_identifier(
						ministry_identifier=ministry_identifier
					)

					# Remove the ministry from the
					# scrape queue
					self._pop_page_scrape_queue(ministry_id)
				else:
					# TODO: Throw error for unexpected
					# payload type
					pass
			else:
				logger.error(
					'Ministry page scraping task '
					'failed: %s',
					result.error_message,
				)
		elif (
			result.task.operation
			== TaskOperation.MINISTRIES_PAGE_PROCESS
		):
			if result.success:
				# Update the state to mark the ministry
				# pages as processed in batch
				ministry_identifiers = (
					result.discovered_data
				)
				if isinstance(
					ministry_identifiers,
					MinistryIdentifiers,
				):
					ministry_ids = (
						ministry_identifiers.ministry_ids
					)

					# Apply the processing result to state
					# and update the ministries service
					# queue accordingly
					self._state_manager.update_ministries_page_processed_state(
						ministry_ids=ministry_ids
					)

				else:
					# TODO: Throw error for unexpected
					# payload type
					pass
			else:
				logger.error(
					'Ministry page processing task '
					'failed: %s',
					result.error_message,
				)

	def _r_ministries_services(
		self, result: TaskResult
	) -> None:
		"""
		Reducer to handle the result of ministries services
		scraping and processing tasks and update the state
		accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.MINISTRIES_SERVICES_SCRAPE
		):
			if result.success:
				# Update the state to mark the ministry
				# services as scraped for the specific
				# ministry, department and agency, and
				# update the ministry service information
				# with the discovered data from scraping.
				service_scraped_identifier = (
					result.discovered_data
				)
				if isinstance(
					service_scraped_identifier,
					ServicesScrapedIdentifier,
				):
					self._state_manager.update_ministry_services_scraped_state(
						ministry_id=service_scraped_identifier.ministry_id,
						department_id=service_scraped_identifier.department_id,
						agency_id=service_scraped_identifier.agency_id,
					)

					# Remove the service from the
					# scrape queue
					self._pop_service_scrape_queue(
						ministry_id=service_scraped_identifier.ministry_id,
						department_id=service_scraped_identifier.department_id,
						agency_id=service_scraped_identifier.agency_id,
					)
				else:
					# TODO: Throw error for unexpected
					# payload type
					pass
			else:
				logger.error(
					'Ministry service scraping task '
					'failed: %s',
					result.error_message,
				)
		elif (
			result.task.operation
			== TaskOperation.MINISTRIES_SERVICES_PROCESS
		):
			if result.success:
				# Update the state to mark the ministry
				# services as processed for the specific
				# ministry, and update the ministry service
				# information with the discovered data from
				# processing, which includes the service IDs
				# that were successfully processed for the
				# ministry.
				services_identifier = result.discovered_data
				if isinstance(
					services_identifier,
					ServicesProcessedIdentifier,
				):
					ministry_id = (
						services_identifier.ministry_id
					)
					self._state_manager.update_ministry_services_processed_state(
						ministry_id=ministry_id,
						department_agencies=services_identifier.department_agencies,
					)

					# Remove the ministry from the
					# processing queue as all its services
					# are now processed
					self._pop_service_processing_queue(
						ministry_id=ministry_id
					)
				else:
					# TODO: Throw error for unexpected
					# payload type
					pass

	def _r_finalisation(self, result: TaskResult) -> None:
		"""
		Reducer to handle the result of finalisation tasks
		and update the state accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.FINALISATION_PHASE
		):
			if result.success:
				self._state_manager.update_finalisation_state(
					completed=True
				)
			else:
				logger.error(
					'Finalisation task failed: %s',
					result.error_message,
				)

	def apply_task_result(self, result: TaskResult) -> None:
		"""
		Apply the result of a completed task
		to update the scheduler state accordingly.
		"""
		# Use the task scope to determine which
		# reducer to use
		reducer = self._reducers.get(result.task.scope)
		if reducer:
			reducer(result)
		else:
			logger.error(
				'No reducer found for task scope: %s',
				result.task.scope,
			)

		# TODO: Deal with errors in task results
