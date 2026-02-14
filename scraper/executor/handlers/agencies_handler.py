"""
This module contains the agencies handler for
executing scheduled tasks related to the agencies
scope of the scraping process.
"""

import logging

import pandas as pd

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.insights.core import render_insights_report
from scraper.processing.recipes.agencies_list import (
	agencies_list_processing_recipe,
)
from scraper.schemas.agencies import AgencyEntry
from scraper.schemas.ministries import (
	MinistryPageAgencyData,
)
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.scraping.recipes.agencies_list import (
	agencies_list_page_recipe,
)
from scraper.scraping.scrape_client import ScrapeClient
from scraper.static.paths import Paths
from scraper.static.seed_urls import SeedUrls
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


class AgenciesHandler:
	"""
	Handler for executing scheduled tasks
	related to the agencies scope.
	"""

	def __init__(self) -> None:
		# Handler configuration
		self.handler_name = 'AGENCIES HANDLER'
		self.seed_url = SeedUrls.AGENCIES_LIST_URL
		self.file = (
			Paths.RAW_DATA_DIR
			/ 'agencies'
			/ 'agencies_list.html'
		)
		self.state_file = (
			Paths.TEMP_DIR / 'agencies_handler_state.json'
		)
		self.metadata_state_file = (
			Paths.TEMP_DIR
			/ 'agencies_handler_metadata_state.json'
		)

		# Processed file locations
		self.processed_data_dir = (
			Paths.PROCESSED_DATA_DIR / 'agencies'
		)

		self.processed_data_json = (
			self.processed_data_dir / 'agencies.json'
		)
		self.processed_data_csv = (
			self.processed_data_dir / 'agencies.csv'
		)

		# Insights file location
		self.insights_file = (
			Paths.INSIGHTS_DIR / 'agencies.md'
		)

		# Entity state
		# Used to store metadata keyed by agency name hash
		self.agency_entries_metadata: dict[
			str, AgencyEntry
		] = self._load_metadata_state()
		# Used to store final structured data keyed
		# by agency ID
		self.agency_entries: dict[str, AgencyEntry] = (
			self._load_state()
		)

	def _save_handlers_state(self) -> None:
		"""
		Method to save the handler state to a file.
		"""
		state_str = state_to_str(self.agency_entries)
		write_file(
			path=self.state_file,
			content=state_str,
		)

	def _save_metadata_state(self) -> None:
		"""
		Method to save the handler metadata state to a file.
		"""
		state_str = state_to_str(
			self.agency_entries_metadata
		)
		write_file(
			path=self.metadata_state_file,
			content=state_str,
		)

	def save_state(self) -> None:
		"""
		Method to save the handler state to a file.
		"""
		self._save_handlers_state()
		self._save_metadata_state()

	def _load_state(self) -> dict[str, AgencyEntry]:
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
		return str_to_state(state_str, AgencyEntry)

	def _load_metadata_state(
		self,
	) -> dict[str, AgencyEntry]:
		"""
		Method to load the handler metadata state
		from a file.
		"""
		if not does_file_exist(self.metadata_state_file):
			logger.info(
				f'[{self.handler_name}]\n'
				f'Metadata state file not found at '
				f'{self.metadata_state_file!r}, starting '
				f'with empty metadata state.',
			)
			return {}

		state_str = read_file(self.metadata_state_file)
		return str_to_state(state_str, AgencyEntry)

	# --- Scraping methods --- #

	async def scrape_agencies_list_page(
		self,
		task_log: str,
		scrape_client: ScrapeClient,
	) -> str:
		"""
		Method to scrape the agencies list page content.
		"""
		# If file already exists, read and return content
		if does_file_exist(self.file):
			logger.info(
				f'[{self.handler_name}]\n'
				f'Agencies list file already exists at '
				f'{self.file!r}, reading content.',
				extra={'task': task_log},
			)
			return read_file(self.file)

		agencies_list_html = await scrape_client.run(
			url=self.seed_url,
			task_log=task_log,
			recipe=agencies_list_page_recipe,
		)

		# Save scraped content to file
		write_file(
			path=self.file,
			content=agencies_list_html,
		)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Agencies list page scraped and '
			f'saved to {self.file!r}.',
			extra={'task': task_log},
		)

		return agencies_list_html

	# --- Processing methods --- #

	def process_agencies_list_data(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to process the raw HTML content of the
		agencies list page into structured AgencyEntry
		data. Note agencies are initially keyed by
		agency name hash.
		"""
		if not does_file_exist(self.file):
			logger.error(
				f'[{self.handler_name}]\n'
				f'Agencies list file does not exist at '
				f'{self.file!r}, cannot process data.',
				extra={'task': task_log},
			)

			raise ExecutorProcessingFailure(
				message=f'Agencies list file does not '
				f'exist at {self.file!r}, cannot process '
				'data.',
				task_log=task_log,
				task=task,
			)

		html_content = read_file(self.file)

		# Process HTML content into structured data
		agency_entries = agencies_list_processing_recipe(
			html=html_content,
			task_log=task_log,
			task=task,
		)

		logger.info(
			f'[{self.handler_name}]\n'
			'Agencies list page processed into structured '
			'AgencyEntry data.',
			extra={'task': task_log},
		)

		self.agency_entries_metadata = agency_entries

	# --- State update methods --- #

	def apply_ministry_page_agency_data_list(
		self,
		ministry_page_agency_data_list: list[
			MinistryPageAgencyData
		],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the agencies state
		using a list of MinistryPageAgencyData observed on
		a ministry page.
		"""
		for agency_entry in ministry_page_agency_data_list:
			# Destructure agency entry metadata
			agency_metadata = (
				self.agency_entries_metadata.get(
					agency_entry.agency_name_hash,
				)
			)
			m_agency_url = (
				agency_metadata.agency_url
				if agency_metadata
				else ''
			)
			m_logo_url = (
				agency_metadata.logo_url
				if agency_metadata
				else ''
			)
			m_agency_description = (
				agency_metadata.agency_description
				if agency_metadata
				else ''
			)
			self.agency_entries[agency_entry.agency_id] = (
				AgencyEntry(
					agency_id=agency_entry.agency_id,
					agency_name_hash=agency_entry.agency_name_hash,
					ministry_id=agency_entry.ministry_id,
					department_id=agency_entry.department_id,
					agency_name=agency_entry.agency_name,
					agency_description=m_agency_description,
					logo_url=m_logo_url,
					agency_url=m_agency_url,
					observed_service_count=None,
					ministry_departments_agencies_url=(  # noqa: E501
						agency_entry.ministry_departments_agencies_url
					),
				)
			)

		count = len(ministry_page_agency_data_list)
		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to agencies '
			f'state with {count} '
			f'agency entries.',
			extra={'task': task_log},
		)

	def apply_service_count_by_agency(
		self,
		service_count_by_agency: dict[str, int],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the agencies state
		using a dictionary mapping agency IDs to observed
		service counts.
		"""
		for (
			agency_id,
			service_count,
		) in service_count_by_agency.items():
			if agency_id in self.agency_entries:
				entry = self.agency_entries[agency_id]
				entry.observed_service_count = service_count
				self.agency_entries[agency_id] = entry

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to agencies '
			f'state with service count by agency data for '
			f'{len(service_count_by_agency)} agencies.',
			extra={'task': task_log},
		)

	# --- Data aggregation for external handlers --- #

	def get_agency_count_by_ministry(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> dict[str, int]:
		"""
		Method to get the count of agencies by ministry.
		Returns a dictionary mapping ministry IDs to
		the count of agencies they oversee.
		"""
		agency_count_by_ministry: dict[str, int] = {}

		for agency_entry in self.agency_entries.values():
			ministry_id = agency_entry.ministry_id
			if ministry_id not in agency_count_by_ministry:
				agency_count_by_ministry[ministry_id] = 0
			agency_count_by_ministry[ministry_id] += 1

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Computed agency count by '
			f'ministry for {len(agency_count_by_ministry)} '
			f'ministries.',
			extra={'task': task_log},
		)

		return agency_count_by_ministry

	def get_agency_count_by_department(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> dict[str, int]:
		"""
		Method to get the count of agencies by department.
		Returns a dictionary mapping department IDs to
		the count of agencies they oversee.
		"""
		agency_count_by_department: dict[str, int] = {}

		for agency_entry in self.agency_entries.values():
			department_id = agency_entry.department_id
			if (
				department_id
				not in agency_count_by_department
			):
				agency_count_by_department[
					department_id
				] = 0
			agency_count_by_department[department_id] += 1

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Computed agency count by '
			f'department for  '
			f'{len(agency_count_by_department)} '
			f'departments.',
			extra={'task': task_log},
		)

		return agency_count_by_department

	# --- Finalisation and analytics methods --- #

	def agencies_insights(
		self, agency_df: pd.DataFrame
	) -> None:
		"""
		Use the insights engine to render a report
		based on the agencies data.
		"""
		insights = render_insights_report(
			df=agency_df,
			state=self.agency_entries,
			id_col='agency_id',
			title='Agencies Data Insights',
		)
		write_file(
			path=self.insights_file,
			content=insights,
		)

	def finalise(self) -> None:
		"""
		Method to finalise the agencies handler by
		saving processed data and insights.
		"""
		# Convert state to DataFrame for analysis
		agency_df = state_to_df(
			self.agency_entries, AgencyEntry
		)

		# Save final state
		self.save_state()

		# Save processed data to files
		save_df(
			df=agency_df,
			csv_path=self.processed_data_csv,
			json_path=self.processed_data_json,
		)

		# Produce insights
		self.agencies_insights(agency_df)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Agencies handler finalised. Processed data '
			f'saved to {self.processed_data_dir!r} and '
			f'insights saved to {self.insights_file!r}.',
		)
