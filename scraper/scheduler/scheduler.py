"""
Scheduler class to manage the scraping process,
including task scheduling and state management.
"""

import logging
from collections import deque

from scraper.exceptions.scheduler import (
	SchedulerDiscoveryTypeMismatch,
	SchedulerPhaseFailure,
	SchedulerProcessFailure,
)
from scraper.scheduler.scheduler_state import (
	SchedulerStateManager,
)
from scraper.schemas.scheduler_state import (
	MinistryState,
	SchedulerState,
)
from scraper.schemas.scheduler_task import (
	# Task payload schemas
	EmptyPayload,
	EmptyTask,
	MinistryIdentifiers,
	MinistryListTask,
	MinistryServicesIdentifier,
	# Task schemas
	MinistryTask,
	MinistryTaskListPayload,
	MinistryTaskPayload,
	SchedulerTask,
	ScrapingPhase,
	ServiceListTask,
	ServicesProcessedIdentifier,
	ServicesScrapedIdentifier,
	ServiceTask,
	ServiceTaskListPayload,
	ServiceTaskPayload,
	TaskOperation,
	TaskResult,
)
from scraper.utils.logging import get_task_log

# logger instance for the scheduler module
logger = logging.getLogger(__name__)


class Scheduler:
	"""
	Scheduler class to manage the scraping process,
	including task scheduling and state management.
	"""

	def __init__(
		self, state_file_name: str = 'scheduler_state.json'
	):
		logger.info('Initializing Scheduler')
		# State manager
		self._state_manager = SchedulerStateManager(
			state_file_name=state_file_name
		)
		# Scheduler state
		self.current_task: SchedulerTask | None = None
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

	# --- Logging and error handling methods ---

	def _phase_failure(
		self, message: str, task_result: TaskResult
	) -> None:
		task_log = get_task_log(task_result.task)
		logger.error(
			message,
			extra={'task': task_log},
		)
		if task_result.error_message:
			message += (
				f' Error details: '
				f'{task_result.error_message}'
			)
		raise SchedulerPhaseFailure(
			message=message,
			task_log=task_log,
			task_result=task_result,
		)

	def _process_failure(
		self, message: str, task: SchedulerTask
	) -> None:
		task_log = get_task_log(task)
		logger.error(
			message,
			extra={'task': task_log},
		)
		raise SchedulerProcessFailure(
			message=message,
			task_log=task_log,
			task=task,
		)

	def _discovery_type_mismatch(
		self,
		message: str,
		target_type: str,
		observed_type: str,
		task_result: TaskResult,
	) -> None:
		task_log = get_task_log(task_result.task)
		logger.error(
			message
			+ f' Expected type: {target_type}, '
			+ f'Observed type: {observed_type}',
			extra={'task': task_log},
		)
		if task_result.error_message:
			message += (
				f' Error details: '
				f'{task_result.error_message}'
			)
		raise SchedulerDiscoveryTypeMismatch(
			message=message,
			target_type=target_type,
			observed_type=observed_type,
			task_log=task_log,
			task_result=task_result,
		)

	# --- Queue initialization methods ---

	def _initialize_ministries_page_scrape_queue(
		self, state: SchedulerState
	) -> deque[MinistryState]:
		"""
		Initialize the queue of ministries pages
		to be scraped based on the current state.
		"""
		ministries = [
			m
			for m in state.ministries_detail.values()
			if not m.complete and not m.page.scraped
		]
		return deque(ministries)

	def _initialise_ministries_services_queue(
		self, state: SchedulerState
	) -> deque[tuple[str, deque[ServiceTaskPayload]]]:
		"""
		Initialize the queue of ministries services
		to be scraped based on the current state.
		"""
		ministries = [
			m
			for m in state.ministries_detail.values()
			if not m.complete
			and (
				not m.services.scraped
				or not m.services.processed
			)
		]
		ministry_services_queue_registry: deque[
			tuple[str, deque[ServiceTaskPayload]]
		] = deque()
		for m in ministries:
			ministry_services_scrape_queue = deque()
			for d in m.departments.values():
				for a in d.agencies.values():
					if not a.state.scraped:
						ministry_services_scrape_queue.append(
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
				(
					m.ministry_id,
					ministry_services_scrape_queue,
				)
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

	# --- State update methods for scheduler ---

	def set_and_return_task(
		self, task: SchedulerTask
	) -> SchedulerTask:
		"""
		Set the current task being sent for execution
		and return the task.
		"""
		self.current_task = task
		return task

	# --- State update methods for task results ---

	def _apply_ministries_list_to_scrape_queue(
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

	def _apply_ministry_services_to_scrape_queue(
		self,
	) -> None:
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
		ministries = [
			m
			for m in state.ministries_detail.values()
			if not m.complete
			and (not m.page.processed and m.page.scraped)
		]
		return MinistryTaskListPayload(
			ministry_ids=[
				MinistryTaskPayload(
					ministry_id=m.ministry_id
				)
				for m in ministries
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
		ministry_state = state.ministries_detail.get(
			ministry_id
		)

		if not ministry_state:
			if not self.current_task:
				self._process_failure(
					message=(
						f'Ministry with ID {ministry_id} '
						'not found in state, and no current'
						' task context available for error '
						'logging.'
					),
					task=ServiceListTask(
						scope=ScrapingPhase.MINISTRIES_SERVICES,
						operation=TaskOperation.MINISTRIES_SERVICES_PROCESS,
						payload=ServiceTaskListPayload(
							service_tasks=[]
						),
					),
				)
			else:
				self._process_failure(
					message=(
						f'Ministry with ID {ministry_id} '
						'not found in state'
					),
					task=self.current_task,
				)
			# Used to satisfy type checker,
			# but in practice the above lines
			# will always raise an exception
			raise Exception()

		service_tasks: list[ServiceTaskPayload] = []
		for d in ministry_state.departments.values():
			for a in d.agencies.values():
				if (
					not a.state.processed
					and a.state.scraped
				):
					service_tasks.append(
						ServiceTaskPayload(
							ministry_id=ministry_id,
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
	) -> MinistryTask | None:
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
		return MinistryTask(
			scope=ScrapingPhase.MINISTRIES_PAGES,
			operation=TaskOperation.MINISTRIES_PAGE_SCRAPE,
			payload=MinistryTaskPayload(
				ministry_id=next_ministry.ministry_id,
			),
		)

	def _next_ministry_service_task(
		self,
	) -> ServiceTask | ServiceListTask | None:
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
			return ServiceListTask(
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
			return ServiceTask(
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
			return EmptyTask(
				scope=ScrapingPhase.FAQ,
				operation=TaskOperation.FAQ_SCRAPE,
				payload=EmptyPayload(),
			)

		if not state.faq.processed:
			return EmptyTask(
				scope=ScrapingPhase.FAQ,
				operation=TaskOperation.FAQ_PROCESS,
				payload=EmptyPayload(),
			)

		# Agencies list phase
		if not state.agencies_list.scraped:
			return EmptyTask(
				scope=ScrapingPhase.AGENCIES_LIST,
				operation=TaskOperation.AGENCIES_LIST_SCRAPE,
				payload=EmptyPayload(),
			)

		if not state.agencies_list.processed:
			return EmptyTask(
				scope=ScrapingPhase.AGENCIES_LIST,
				operation=TaskOperation.AGENCIES_LIST_PROCESS,
				payload=EmptyPayload(),
			)

		# Ministries list phase
		if not state.ministries_list.scraped:
			return EmptyTask(
				scope=ScrapingPhase.MINISTRIES_LIST,
				operation=TaskOperation.MINISTRIES_LIST_SCRAPE,
				payload=EmptyPayload(),
			)

		if not state.ministries_list.processed:
			return EmptyTask(
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
				return MinistryListTask(
					scope=ScrapingPhase.MINISTRIES_PAGES,
					operation=TaskOperation.MINISTRIES_PAGE_PROCESS,
					payload=self._get_ministry_pages_to_process(
						state
					),
				)

		# Double check if there are any remaining ministry
		# pages to process
		if not state.ministry_pages.processed:
			return MinistryListTask(
				scope=ScrapingPhase.MINISTRIES_PAGES,
				operation=TaskOperation.MINISTRIES_PAGE_PROCESS,
				payload=self._get_ministry_pages_to_process(
					state
				),
			)

		# Ministries services phase
		if (
			not state.ministry_services.scraped
			or not state.ministry_services.processed
		):
			task = self._next_ministry_service_task()
			if task:
				return task
			else:
				# If no more ministry services to scrape,
				# move to finalisation phase
				return EmptyTask(
					scope=ScrapingPhase.FINALISATION,
					operation=TaskOperation.FINALISATION_CHECKS,
					payload=EmptyPayload(),
				)

		# Double check all finalisation checks
		# are done before exiting the scheduler
		if not state.finalisation_checks:
			return EmptyTask(
				scope=ScrapingPhase.FINALISATION,
				operation=TaskOperation.FINALISATION_CHECKS,
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
				self._phase_failure(
					message='FAQ scraping task failed',
					task_result=result,
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
				self._phase_failure(
					message='FAQ processing task failed',
					task_result=result,
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
				self._phase_failure(
					message='Agencies list scraping '
					'task failed',
					task_result=result,
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
				self._phase_failure(
					message='Agencies list processing '
					'task failed',
					task_result=result,
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
				self._phase_failure(
					message='Ministries list scraping '
					'task failed',
					task_result=result,
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
					self._apply_ministries_list_to_scrape_queue(
						ministry_identifiers=ministry_identifiers
					)
				else:
					self._discovery_type_mismatch(
						message=(
							'Ministries list processing '
							'task returned unexpected type '
							'of discovered data.'
						),
						target_type='MinistryIdentifiers',
						observed_type=type(
							result.discovered_data
						).__name__,
						task_result=result,
					)
			else:
				self._phase_failure(
					message='Ministries list processing '
					'task failed',
					task_result=result,
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
					self._state_manager.apply_ministry_services_identifier(
						ministry_identifier=ministry_identifier
					)

					# Remove the ministry from the
					# scrape queue
					self._pop_page_scrape_queue(ministry_id)

					# If all pages scraped update global
					# flag in state
					q = self._ministries_page_scrape_queue
					if not q:
						self._state_manager.check_global_ministries_page_scraped_state()

				else:
					self._discovery_type_mismatch(
						message=(
							'Ministry page scraping task '
							'returned unexpected type of '
							'discovered data.'
						),
						target_type='MinistryServicesIdentifier',
						observed_type=type(
							result.discovered_data
						).__name__,
						task_result=result,
					)
			else:
				self._phase_failure(
					message='Ministry page scraping task '
					'failed',
					task_result=result,
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
					# Check if all pages are processed, if
					# so update the ministries services
					# scrape queue with the discovered
					# ministry services identifiers
					self._state_manager.check_global_ministries_page_processed_state()

					state = self._state_manager.get_state()
					if state.ministry_pages.processed:
						self._apply_ministry_services_to_scrape_queue()

				else:
					self._discovery_type_mismatch(
						message=(
							'Ministries page processing '
							'task returned unexpected type '
							'of discovered data.'
						),
						target_type='MinistryIdentifiers',
						observed_type=type(
							result.discovered_data
						).__name__,
						task_result=result,
					)
			else:
				self._phase_failure(
					message='Ministry page processing task '
					'failed',
					task_result=result,
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
					self._discovery_type_mismatch(
						message=(
							'Ministry service scraping task'
							'task returned unexpected type '
							'of discovered data.'
						),
						target_type='ServicesScrapedIdentifier',
						observed_type=type(
							result.discovered_data
						).__name__,
						task_result=result,
					)
			else:
				self._phase_failure(
					message='Ministry service scraping '
					'task failed',
					task_result=result,
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

					# After each bach of ministry services
					# is processed, check if all ministries
					# are scraped for global flag update
					# note this is done here so the check is
					# done after each batch of services is
					# processed, as opposed after when each
					# service is scraped to avoid
					# unnecessary checks
					self._state_manager.check_global_ministry_services_scraped_state()

					# When queue is empty, check if all
					# ministries have their services
					# processed for global flag update
					if not self._ministries_services_queue:
						self._state_manager.check_global_ministry_services_processed_state()
				else:
					self._discovery_type_mismatch(
						message=(
							'Ministry services processing '
							'task returned unexpected type '
							'of discovered data.'
						),
						target_type='ServicesProcessedIdentifier',
						observed_type=type(
							result.discovered_data
						).__name__,
						task_result=result,
					)
			else:
				self._phase_failure(
					message='Ministry services processing '
					'task failed',
					task_result=result,
				)

	def _r_finalisation(self, result: TaskResult) -> None:
		"""
		Reducer to handle the result of finalisation tasks
		and update the state accordingly.
		"""
		if (
			result.task.operation
			== TaskOperation.FINALISATION_CHECKS
		):
			if result.success:
				self._state_manager.update_finalisation_state(
					completed=True
				)
			else:
				self._phase_failure(
					message='Finalisation task failed',
					task_result=result,
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
			self._process_failure(
				message=(
					f'No reducer found for task scope: '
					f'{result.task.scope}'
				),
				task=result.task,
			)

		# Save state after applying the task result
		self._state_manager.save_state()
