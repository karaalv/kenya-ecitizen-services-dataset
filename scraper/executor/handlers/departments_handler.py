"""
This module contains the handler for
executing scheduled tasks related to the
departments scope of the scraping process.
(Note: Given the nature of the data, the departments
handler is strictly comprised of processing the data scraped
from the ministries pages related to the departments.)
"""

import logging

from scraper.insights.core import render_insights_report
from scraper.schemas.departments import DepartmentEntry
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.static.paths import Paths
from scraper.utils.files import (
	does_file_exist,
	read_file,
	write_file,
)
from scraper.utils.handlers import (
	save_df,
	state_to_df,
	state_to_str,
	str_to_state,
)

logger = logging.getLogger(__name__)


class DepartmentsHandler:
	"""
	Handler for executing scheduled tasks
	related to the departments scope.
	"""

	def __init__(self) -> None:
		# Handler configuration
		self.handler_name = 'DEPARTMENTS HANDLER'
		self.state_file = (
			Paths.TEMP_DIR
			/ 'departments_handler_state.json'
		)

		# Processed file locations
		self.processed_data_dir = (
			Paths.PROCESSED_DATA_DIR / 'departments'
		)

		self.processed_data_json = (
			self.processed_data_dir / 'departments.json'
		)
		self.processed_data_csv = (
			self.processed_data_dir / 'departments.csv'
		)

		# Insights file location
		self.insights_file = (
			Paths.INSIGHTS_DIR / 'departments.md'
		)

		# Entity state
		self.department_entries: dict[
			str, DepartmentEntry
		] = self._load_state()

	def save_state(self) -> None:
		"""
		Method to save the handler state to a file.
		"""
		state_str = state_to_str(self.department_entries)
		write_file(
			path=self.state_file,
			content=state_str,
		)

	def _load_state(self) -> dict[str, DepartmentEntry]:
		"""
		Method to load the handler state from a file.
		"""
		if not does_file_exist(self.state_file):
			logger.debug(
				f'[{self.handler_name}]\n'
				f'State file not found at '
				f'{self.state_file!r}, starting with empty '
				f'state.',
			)
			return {}

		state_str = read_file(self.state_file)
		return str_to_state(state_str, DepartmentEntry)

	# --- Processing methods --- #

	# --- Departments state update methods --- #

	def apply_department_entry_list(
		self,
		department_entry_list: list[DepartmentEntry],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the departments state
		using a list of department entries.
		"""
		for department_entry in department_entry_list:
			self.department_entries[
				department_entry.department_id
			] = department_entry

		logger.debug(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to departments '
			f'state with {len(department_entry_list)} '
			f'department entries.',
			extra={'task': task_log},
		)

	def apply_agency_count_by_department(
		self,
		agency_count_by_department: dict[str, int],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the departments state
		using a dictionary of agency count by department.
		"""
		for (
			department_id,
			agency_count,
		) in agency_count_by_department.items():
			if department_id in self.department_entries:
				department_entry = self.department_entries[
					department_id
				]
				department_entry.observed_agency_count = (
					agency_count
				)
				self.department_entries[department_id] = (
					department_entry
				)

		logger.debug(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to departments '
			f'state with agency count for '
			f'{len(agency_count_by_department)} '
			f'departments.',
			extra={'task': task_log},
		)

	def apply_service_count_by_department(
		self,
		service_count_by_department: dict[str, int],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the departments state
		using a dictionary of service count by department.
		"""
		for (
			department_id,
			service_count,
		) in service_count_by_department.items():
			if department_id in self.department_entries:
				department_entry = self.department_entries[
					department_id
				]
				department_entry.observed_service_count = (
					service_count  # noqa: E501
				)
				self.department_entries[department_id] = (
					department_entry
				)

		logger.debug(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to departments '
			f'state with service count for '
			f'{len(service_count_by_department)} '
			f'departments.',
			extra={'task': task_log},
		)

	# --- Data aggregation for external handlers --- #

	def get_department_count_by_ministry(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> dict[str, int]:
		"""
		Method to get the count of departments by ministry.
		Returns a dictionary mapping ministry IDs to the
		count of departments under them.
		"""
		department_count_by_ministry: dict[str, int] = {}

		for (
			department_entry
		) in self.department_entries.values():
			ministry_id = department_entry.ministry_id
			if (
				ministry_id
				not in department_count_by_ministry
			):
				department_count_by_ministry[
					ministry_id
				] = 0
			department_count_by_ministry[ministry_id] += 1

		logger.debug(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Computed department count by '
			f'ministry for  '
			f'{len(department_count_by_ministry)} '
			f'ministries.',
			extra={'task': task_log},
		)

		return department_count_by_ministry

	# --- Finalisation and analytics methods --- #

	def departments_insights(self, department_df) -> None:
		"""
		Method to produce insights based on the
		departments data using the insights engine.
		"""
		insights = render_insights_report(
			df=department_df,
			state=self.department_entries,
			id_col='department_id',
			title='Departments Data Insights',
		)
		write_file(
			path=self.insights_file,
			content=insights,
		)

	def finalise(self) -> None:
		"""
		Method to finalise the departments handler by
		saving processed data and insights.
		"""
		# Convert state to dataframe
		department_df = state_to_df(
			self.department_entries, DepartmentEntry
		)

		# Save final state
		self.save_state()

		# Save processed data
		save_df(
			df=department_df,
			json_path=self.processed_data_json,
			csv_path=self.processed_data_csv,
		)

		# Produce insights
		self.departments_insights(department_df)

		logger.debug(
			f'[{self.handler_name}]\n'
			f'Departments handler finalised. Processed '
			f'data saved to {self.processed_data_dir!r} '
			f'and insights saved to '
			f'{self.insights_file!r}.',
		)
