"""
This module contains the handler for
executing scheduled tasks related to the
services scope of the scraping process.
(Note: Given the nature of the data, the services
handler is strictly comprised of processing the data scraped
from the ministries pages related to the services.)
"""

import logging

import pandas as pd

from scraper.insights.core import render_insights_report
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.schemas.services import ServiceEntry
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


class ServicesHandler:
	"""
	Handler for executing scheduled tasks
	related to the services scope.
	"""

	def __init__(self) -> None:
		# Handler configuration
		self.handler_name = 'SERVICES HANDLER'
		self.state_file = (
			Paths.TEMP_DIR / 'services_handler_state.json'
		)

		# processed file locations
		self.processed_data_dir = (
			Paths.PROCESSED_DATA_DIR / 'services'
		)

		self.processed_data_json = (
			self.processed_data_dir / 'services.json'
		)
		self.processed_data_csv = (
			self.processed_data_dir / 'services.csv'
		)

		# Insights file location
		self.insights_file = (
			Paths.INSIGHTS_DIR / 'services.md'
		)

		# Entity state
		self.service_entries: dict[str, ServiceEntry] = (
			self._load_state()
		)

	def save_state(self) -> None:
		"""
		Method to save the handler state to a file.
		"""
		state_str = state_to_str(self.service_entries)
		write_file(
			path=self.state_file,
			content=state_str,
		)

	def _load_state(self) -> dict[str, ServiceEntry]:
		"""
		Method to load the handler state from a file.
		"""
		if not does_file_exist(self.state_file):
			logger.info(
				f'[{self.handler_name}]\n'
				f'State file not found at '
				f'{self.state_file!r}, starting with '
				f'empty state.',
			)
			return {}

		state_str = read_file(self.state_file)
		return str_to_state(state_str, ServiceEntry)

	# --- Processing methods --- #

	# --- Services state update methods --- #

	def apply_service_entry_list(
		self,
		service_entry_list: list[ServiceEntry],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the services state
		using a list of service entries.
		"""
		for service_entry in service_entry_list:
			self.service_entries[
				service_entry.service_id
			] = service_entry

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to services '
			f'state with {len(service_entry_list)} '
			f'service entries.',
			extra={'task': task_log},
		)

	# --- Data aggregation for external handlers --- #

	def get_service_count_by_agency(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> dict[str, int]:
		"""
		Method to get the count of services by agency.
		Returns a dictionary mapping agency IDs to
		the count of services they offer.
		"""
		service_count_by_agency: dict[str, int] = {}

		for service_entry in self.service_entries.values():
			agency_id = service_entry.agency_id
			if agency_id not in service_count_by_agency:
				service_count_by_agency[agency_id] = 0
			service_count_by_agency[agency_id] += 1

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Computed service count by '
			f'agency for {len(service_count_by_agency)} '
			f'agencies.',
			extra={'task': task_log},
		)

		return service_count_by_agency

	def get_service_count_by_department(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> dict[str, int]:
		"""
		Method to get the count of services by department.
		Returns a dictionary mapping department IDs to
		the count of services they offer.
		"""
		service_count_by_department: dict[str, int] = {}

		for service_entry in self.service_entries.values():
			department_id = service_entry.department_id
			if (
				department_id
				not in service_count_by_department
			):
				service_count_by_department[
					department_id
				] = 0
			service_count_by_department[department_id] += 1

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Computed service count by '
			f'department for  '
			f'{len(service_count_by_department)} '
			f'departments.',
			extra={'task': task_log},
		)

		return service_count_by_department

	def get_service_count_by_ministry(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> dict[str, int]:
		"""
		Method to get the count of services by ministry.
		Returns a dictionary mapping ministry IDs to
		the count of services they offer.
		"""
		service_count_by_ministry: dict[str, int] = {}

		for service_entry in self.service_entries.values():
			ministry_id = service_entry.ministry_id
			if ministry_id not in service_count_by_ministry:
				service_count_by_ministry[ministry_id] = 0
			service_count_by_ministry[ministry_id] += 1

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Computed service count by '
			f'ministry for '
			f'{len(service_count_by_ministry)} ministries.',
			extra={'task': task_log},
		)

		return service_count_by_ministry

	# --- Finalisation and analytics methods --- #

	def services_insights(
		self, service_df: pd.DataFrame
	) -> None:
		"""
		Use the insights engine to render a report
		based on the services data.
		"""
		insights = render_insights_report(
			df=service_df,
			state=self.service_entries,
			id_col='service_id',
			title='Services Data Insights',
			ignore_cols=[
				'service_description',
				'requirements',
			],
		)

		write_file(
			path=self.insights_file,
			content=insights,
		)

	def finalise(self) -> None:
		"""
		Method to finalise the services handler by saving
		the result of processing to files and rendering
		insights.
		"""
		# Convert state to dataframe
		service_df = state_to_df(
			self.service_entries, ServiceEntry
		)

		# Save final state
		self.save_state()

		# Save processed data to files
		save_df(
			df=service_df,
			csv_path=self.processed_data_csv,
			json_path=self.processed_data_json,
		)

		# Produce insights
		self.services_insights(service_df)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Services handler finalised. Processed data '
			f'saved to {self.processed_data_dir!r} and '
			f'insights saved to {self.insights_file!r}.',
		)
