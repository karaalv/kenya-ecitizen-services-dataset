"""
Scheduler state class used to maintain
the state of the scraping and processing
tasks within the Scheduler class.
"""

import logging

from scraper.schemas.scheduler_state import (
	AgencyServicesState,
	DepartmentState,
	MinistryState,
	SchedulerState,
)
from scraper.schemas.scheduler_task import (
	MinistryServicesIdentifier,
)
from scraper.static.paths import Paths
from scraper.utils.files import (
	does_file_exist,
	read_file,
	write_file,
)

# Logger instance for the scheduler state module
logger = logging.getLogger(__name__)


class SchedulerStateManager:
	"""
	Class to manage the state of the scraping and
	processing tasks for the scheduler. This class
	handles loading, updating, and saving the state
	to disk.
	"""

	def __init__(
		self, state_file_name: str = 'scheduler_state.json'
	):
		self.state_file = Paths.TEMP_DIR / state_file_name
		self._state = self._load_state()

	def _load_state(self) -> SchedulerState:
		"""
		Load the scheduler state from disk. If the file
		does not exist, initialize a new state.
		"""
		if does_file_exist(self.state_file):
			logger.info(
				f'Loading existing scheduler state '
				f'from {self.state_file}'
			)
			content = read_file(self.state_file)
			return SchedulerState.model_validate_json(
				content
			)
		else:
			logger.info(
				'No existing scheduler state.'
				'Initializing new state.'
			)
			return SchedulerState()

	def save_state(self) -> None:
		"""
		Save the current scheduler state to disk as JSON.
		"""
		content = self._state.model_dump_json(indent=4)
		write_file(self.state_file, content)
		logger.info(
			f'Scheduler state saved to {self.state_file}'
		)

	def get_state(self) -> SchedulerState:
		"""
		Get the current scheduler state.
		"""
		return self._state

	# --- State set methods ---
	def apply_ministries_list_state(
		self, ministry_ids: list[str]
	) -> None:
		"""
		Set the state for a list of ministries in the
		ministries detail state. If a ministry ID does not
		exist in the current state, it will be added
		with default values.
		"""
		for ministry_id in ministry_ids:
			if (
				ministry_id
				not in self._state.ministries_detail
			):
				self._state.ministries_detail[
					ministry_id
				] = MinistryState(
					ministry_id=ministry_id,
				)

	def apply_ministry_services_identifier(
		self,
		ministry_identifier: MinistryServicesIdentifier,
	) -> None:
		"""
		Set the state for departments and agencies under a
		specific ministry. If a department or agency ID does
		not exist in the current state, it will be added
		with default values.
		"""
		# Extract ministry ID and departments/agencies
		# from the identifier
		ministry_id = ministry_identifier.ministry_id
		ministry_departments = (
			ministry_identifier.departments
		)
		if ministry_id not in self._state.ministries_detail:
			logger.warning(
				f'Ministry ID {ministry_id} not found '
				'in state when setting departments and '
				'agencies.'
			)
			return

		ministry_state = self._state.ministries_detail[
			ministry_id
		]

		for (
			department_id,
			department_identifier,
		) in ministry_departments.items():
			if (
				department_id
				not in ministry_state.departments
			):
				ministry_state.departments[
					department_id
				] = DepartmentState(
					department_id=department_id,
				)
			department_state = ministry_state.departments[
				department_id
			]

			for (
				agency_id,
				agency_identifier,
			) in department_identifier.agencies.items():
				if (
					agency_id
					not in department_state.agencies
				):
					department_state.agencies[agency_id] = (
						AgencyServicesState(
							agency_id=agency_id,
							ministry_departments_agencies_url=(
								agency_identifier.ministry_departments_agencies_url
							),
						)
					)

	# --- State update methods ---

	def update_faq_state(
		self,
		scraped: bool | None = None,
		processed: bool | None = None,
	) -> None:
		"""
		Update the state of the FAQ scraping and
		processing steps.
		"""
		if scraped is not None:
			self._state.faq.scraped = scraped
		if processed is not None:
			self._state.faq.processed = processed

	def update_agencies_list_state(
		self,
		scraped: bool | None = None,
		processed: bool | None = None,
	) -> None:
		"""
		Update the state of the agencies list scraping and
		processing steps.
		"""
		if scraped is not None:
			self._state.agencies_list.scraped = scraped
		if processed is not None:
			self._state.agencies_list.processed = processed

	def update_ministries_list_state(
		self,
		scraped: bool | None = None,
		processed: bool | None = None,
	) -> None:
		"""
		Update the state of the ministries list scraping and
		processing steps.
		"""
		if scraped is not None:
			self._state.ministries_list.scraped = scraped
		if processed is not None:
			self._state.ministries_list.processed = (
				processed
			)

	def update_ministry_page_scraped_state(
		self, ministry_id: str
	) -> None:
		"""
		Update the state of the ministry page scraping step
		for a specific ministry.
		"""
		if ministry_id in self._state.ministries_detail:
			self._state.ministries_detail[
				ministry_id
			].page.scraped = True
		else:
			logger.warning(
				f'Ministry ID {ministry_id} not found in '
				'state when updating page scraped state.'
			)

	def check_global_ministries_page_scraped_state(
		self,
	) -> None:
		"""
		Check if all ministry pages have been scraped.
		If so mark the global ministries page step as
		scraped.
		"""
		# If all ministries scraped then mark ministries
		# pages step scraped as complete
		values = self._state.ministries_detail.values()
		all_scraped = bool(values) and all(
			m.page.scraped for m in values
		)
		if all_scraped:
			self._state.ministry_pages.scraped = True
			logger.info(
				'All ministry pages scraped. '
				'Marking ministries pages step as scraped.'
			)
		else:
			logger.info(
				'Not all ministry pages scraped yet. '
				'Ministries pages step remains not scraped.'
			)

	def update_ministries_page_processed_state(
		self, ministry_ids: list[str]
	) -> None:
		"""
		Batch update the state of the ministry page
		processing step
		"""
		for ministry_id in ministry_ids:
			if ministry_id in self._state.ministries_detail:
				self._state.ministries_detail[
					ministry_id
				].page.processed = True
			else:
				logger.warning(
					f'Ministry ID {ministry_id} not found '
					'in state when updating page processed '
					'state.'
				)

	def check_global_ministries_page_processed_state(
		self,
	) -> None:
		"""
		Check if all ministry pages have been processed.
		If so mark the global ministries page step as
		processed.
		"""
		values = self._state.ministries_detail.values()
		all_processed = bool(values) and all(
			m.page.processed for m in values
		)
		if all_processed:
			self._state.ministry_pages.processed = True
			logger.info(
				'All ministry pages processed. '
				'Marking ministries pages step as '
				'processed.'
			)
		else:
			logger.info(
				'Not all ministry pages processed yet. '
				'Ministries pages step remains not '
				'processed.'
			)

	def update_ministry_services_scraped_state(
		self,
		ministry_id: str,
		department_id: str,
		agency_id: str,
	) -> None:
		"""
		Update the state of the ministry services scraping
		step for a specific ministry.
		"""
		ministry_state = self._state.ministries_detail.get(
			ministry_id
		)

		if ministry_state is None:
			logger.warning(
				'Ministry ID %s not found when updating '
				'services scraped state.',
				ministry_id,
			)
			return

		department_state = ministry_state.departments.get(
			department_id
		)
		if department_state is None:
			logger.warning(
				'Department ID %s not found when updating '
				'services scraped state for ministry %s.',
				department_id,
				ministry_id,
			)
			return

		agency_state = department_state.agencies.get(
			agency_id
		)
		if agency_state is None:
			logger.warning(
				'Agency ID %s not found when updating '
				'services scraped state for ministry %s, '
				'department %s.',
				agency_id,
				ministry_id,
				department_id,
			)
			return

		agency_state.state.scraped = True

		# Check if all services under the ministry
		# have been scraped
		agency_states = [
			a.state
			for d in ministry_state.departments.values()
			for a in d.agencies.values()
		]
		all_services_scraped = bool(agency_states) and all(
			a.scraped for a in agency_states
		)

		if all_services_scraped:
			ministry_state.services.scraped = True

	def check_global_ministry_services_scraped_state(
		self,
	) -> None:
		"""
		Check if all ministry services have been scraped.
		If so mark the global ministry services step as
		scraped.
		"""
		values = self._state.ministries_detail.values()
		all_ministries_services_scraped = bool(
			values
		) and all(m.services.scraped for m in values)

		if all_ministries_services_scraped:
			self._state.ministry_services.scraped = True
			logger.info(
				'All ministry services scraped. '
				'Marking ministry services step as '
				'scraped.'
			)
		else:
			logger.info(
				'Not all ministry services scraped yet. '
				'Ministry services step remains not '
				'scraped.'
			)

	def update_ministry_services_processed_state(
		self,
		ministry_id: str,
		department_agencies: dict[str, list[str]],
	) -> None:
		"""
		Update the state of the ministry services processing
		step for a specific ministry.
		"""
		ministry_state = self._state.ministries_detail.get(
			ministry_id
		)

		if ministry_state is None:
			logger.warning(
				'Ministry ID %s not found when updating '
				'services processed state.',
				ministry_id,
			)
			return

		for (
			department_id,
			agency_ids,
		) in department_agencies.items():
			department_state = (
				ministry_state.departments.get(
					department_id
				)
			)
			if department_state is None:
				logger.warning(
					'Department ID %s not found when '
					'updating services processed state '
					'for ministry %s.',
					department_id,
					ministry_id,
				)
				continue

			for agency_id in agency_ids:
				agency_state = (
					department_state.agencies.get(agency_id)
				)
				if agency_state is None:
					logger.warning(
						'Agency ID %s not found when '
						'updating services processed state '
						'for ministry %s, department %s.',
						agency_id,
						ministry_id,
						department_id,
					)
					continue

				agency_state.state.processed = True

		# Check if all services under the ministry
		# have been processed
		agency_states = [
			a.state
			for d in ministry_state.departments.values()
			for a in d.agencies.values()
		]
		all_services_processed = bool(
			agency_states
		) and all(a.processed for a in agency_states)

		if all_services_processed:
			ministry_state.services.processed = True

		# Mark the ministry as complete if
		# both its page and services are processed
		if (
			ministry_state.page.processed
			and ministry_state.services.processed
		):
			ministry_state.complete = True

			logger.info(
				f'Ministry {ministry_id} '
				'marked as complete.'
			)

	def check_global_ministry_services_processed_state(
		self,
	) -> None:
		"""
		Check if all ministry services have been processed.
		If so mark the global ministry services step as
		processed.
		"""
		values = self._state.ministries_detail.values()
		all_ministries_services_processed = bool(
			values
		) and all(m.services.processed for m in values)

		if all_ministries_services_processed:
			self._state.ministry_services.processed = True
			logger.info(
				'All ministry services processed. '
				'Marking ministry services step as '
				'processed.'
			)
		else:
			logger.info(
				'Not all ministry services processed yet. '
				'Ministry services step remains not '
				'processed.'
			)

	def update_finalisation_state(
		self,
		completed: bool | None = None,
	) -> None:
		"""
		Update the state of the finalisation step.
		"""
		if completed is not None:
			self._state.finalisation_checks = completed
			logger.info(
				'Finalisation checks marked as '
				f'{completed}.'
			)
