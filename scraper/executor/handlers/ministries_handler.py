"""
This module contains the ministries handler for
executing scheduled tasks related to the ministries
scope of the scraping process.
"""

import asyncio
import logging
from pathlib import Path

import pandas as pd

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.insights.core import render_insights_report
from scraper.processing.recipes.ministries import (
	ministry_departments_agencies_processing_recipe,
	ministry_overview_processing_recipe,
	ministry_service_processing_recipe,
)
from scraper.processing.recipes.ministries_list import (
	ministries_list_processing_recipe,
)
from scraper.processing.utils.ministries import (
	build_ministry_services_identifier,
	build_services_processed_identifier,
)
from scraper.schemas.departments import DepartmentEntry
from scraper.schemas.ministries import (
	MinistryEntry,
	MinistryPageAgencyData,
	MinistryPageData,
	MinistryPageOverviewData,
	MinistryPageProcessingResult,
)
from scraper.schemas.scheduler_task import (
	MinistryIdentifiers,
	MinistryServicesIdentifier,
	MinistryServicesIdentifiersList,
	MinistryTaskListPayload,
	SchedulerTask,
	ServicesProcessedIdentifier,
	ServicesScrapedIdentifier,
	ServiceTaskListPayload,
	ServiceTaskPayload,
)
from scraper.schemas.services import ServiceEntry
from scraper.scraping.recipes.ministries import (
	ministries_list_page_recipe,
	ministry_page_recipe,
	ministry_services_page_recipe,
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


class MinistriesHandler:
	"""
	Handler for executing scheduled tasks
	related to the ministries scope.
	"""

	def __init__(self) -> None:
		# Handler configuration
		self.handler_name = 'MINISTRIES HANDLER'
		self.seed_url = SeedUrls.MINISTRIES_LIST_URL
		self.file = (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ 'ministries_list.html'
		)
		self.state_file = (
			Paths.TEMP_DIR / 'ministries_handler_state.json'
		)

		# Processed file locations
		self.processed_data_dir = (
			Paths.PROCESSED_DATA_DIR / 'ministries'
		)

		self.processed_data_json = (
			self.processed_data_dir / 'ministries.json'
		)
		self.processed_data_csv = (
			self.processed_data_dir / 'ministries.csv'
		)

		# Insights file location
		self.insights_file = (
			Paths.INSIGHTS_DIR / 'ministries.md'
		)

		# Entity state
		self.ministry_entries: dict[str, MinistryEntry] = (
			self._load_state()
		)

	def save_state(self) -> None:
		"""
		Method to save the handler state to a file.
		"""
		state_str = state_to_str(self.ministry_entries)
		write_file(
			path=self.state_file,
			content=state_str,
		)

	def _load_state(self) -> dict[str, MinistryEntry]:
		"""
		Method to load the handler state from a file.
		"""
		if not does_file_exist(self.state_file):
			logger.info(
				f'[{self.handler_name}]\n'
				f'State file not found at, '
				f'{self.state_file!r} starting with '
				'empty state.',
			)
			return {}

		state_str = read_file(self.state_file)
		return str_to_state(state_str, MinistryEntry)

	# File builder methods for constructing file paths for
	# ministries data based on ministry identifiers
	@staticmethod
	def _build_ministry_overview_file_path(
		ministry_id: str,
	) -> Path:
		return (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ ministry_id
			/ 'overview.html'
		)

	@staticmethod
	def _build_ministry_departments_agencies_file_path(
		ministry_id: str,
	) -> Path:
		return (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ ministry_id
			/ 'departments_agencies.html'
		)

	@staticmethod
	def _build_ministry_services_file_path(
		ministry_id: str,
		department_id: str,
		agency_id: str,
	) -> Path:
		return (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ ministry_id
			/ department_id
			/ agency_id
			/ 'services.html'
		)

	# --- Scraping methods ---

	async def scrape_ministries_list_page(
		self,
		task_log: str,
		scrape_client: ScrapeClient,
	) -> str:
		"""
		Method to scrape the ministries list page content.
		"""
		# If file already exists, read and return content
		if does_file_exist(self.file):
			logger.info(
				f'[{self.handler_name}]\n'
				f'Ministries list file already exists at '
				f'{self.file!r}, reading content.',
				extra={'task': task_log},
			)
			return read_file(self.file)

		ministries_list_html = await scrape_client.run(
			url=self.seed_url,
			task_log=task_log,
			recipe=ministries_list_page_recipe,
		)
		# Save scraped content to file
		write_file(
			path=self.file,
			content=ministries_list_html,
		)
		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministries list page scraped and '
			f'saved to {self.file!r}.',
			extra={'task': task_log},
		)
		return ministries_list_html

	async def scrape_ministry_page(
		self,
		ministry_id: str,
		task_log: str,
		task: SchedulerTask,
		scrape_client: ScrapeClient,
	) -> MinistryPageData:
		"""
		Method to scrape an individual
		ministry page content.
		"""
		ministry_overview_file = (
			self._build_ministry_overview_file_path(
				ministry_id
			)
		)

		ministry_departments_agencies_file = (  # noqa: E501
			self._build_ministry_departments_agencies_file_path(
				ministry_id
			)
		)
		# If both files already exist,
		# read and return content
		if does_file_exist(
			ministry_overview_file
		) and does_file_exist(
			ministry_departments_agencies_file
		):
			logger.info(
				f'[{self.handler_name}]\n'
				f'Ministry page files already exist for '
				f'{ministry_id} at {ministry_overview_file!r} '  # noqa: E501
				f'and {ministry_departments_agencies_file!r}, '  # noqa: E501
				f'reading content.',
				extra={'task': task_log},
			)
			overview_html = read_file(
				ministry_overview_file
			)
			departments_agencies_html = read_file(
				ministry_departments_agencies_file
			)
			return MinistryPageData(
				ministry_id=ministry_id,
				overview=overview_html,
				departments_and_agencies=departments_agencies_html,
			)

		# Retrieve ministry URL from handler state
		ministry_entry = self.ministry_entries.get(
			ministry_id
		)
		if not ministry_entry:
			logger.error(
				f'[{self.handler_name}]\n'
				f'Ministry entry not found in handler '
				f'state for ministry_id {ministry_id} '
				f' when scraping ministry page.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message=f'Ministry entry not found in '
				f' handler state for ministry_id'
				f' {ministry_id} when scraping '
				f'ministry page.',
				task_log=task_log,
				task=task,
			)
		ministry_url = ministry_entry.ministry_url

		ministry_page_data = await scrape_client.run(
			url=ministry_url,
			task_log=task_log,
			recipe=ministry_page_recipe,
		)
		ministry_page_data.ministry_id = ministry_id

		# Save scraped content to files
		write_file(
			path=ministry_overview_file,
			content=ministry_page_data.overview,
		)
		write_file(
			path=ministry_departments_agencies_file,
			content=ministry_page_data.departments_and_agencies,
		)
		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministry page scraped for {ministry_id} and '
			f'saved to {ministry_overview_file!r} and '
			f'{ministry_departments_agencies_file!r}.',
			extra={'task': task_log},
		)
		return ministry_page_data

	async def scrape_ministry_services_page(
		self,
		ministry_id: str,
		department_id: str,
		agency_id: str,
		ministry_departments_agencies_url: str,
		task_log: str,
		scrape_client: ScrapeClient,
	) -> str:
		"""
		Method to scrape the services listed on
		ministries page under a specific department
		and agency.
		"""
		services_file = (
			self._build_ministry_services_file_path(
				ministry_id,
				department_id,
				agency_id,
			)
		)

		# If file already exists,
		# read and return content
		if does_file_exist(services_file):
			logger.info(
				f'[{self.handler_name}]\n'
				f'Ministry services file already exists '
				f'for {ministry_id} under department '
				f'{department_id} and agency {agency_id} '
				f'at {services_file!r}, reading content.',
				extra={'task': task_log},
			)
			return read_file(services_file)

		services_html = await scrape_client.run(
			url=ministry_departments_agencies_url,
			task_log=task_log,
			recipe=ministry_services_page_recipe,
		)

		write_file(
			path=services_file,
			content=services_html,
		)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministry services page scraped for '
			f'{ministry_id} under department {department_id} '  # noqa: E501
			f'and agency {agency_id}, saved to {services_file!r}.',  # noqa: E501
			extra={'task': task_log},
		)
		return services_html

	# --- Scrape and process methods ---

	async def scrape_and_package_ministry_services_data(
		self,
		service_task: ServiceTaskPayload,
		task_log: str,
		scrape_client: ScrapeClient,
	) -> ServicesScrapedIdentifier:
		"""
		Method to scrape the services listed on a ministry
		page under a specific department and agency, and
		return the data packaged in a structured format.
		"""
		await self.scrape_ministry_services_page(
			ministry_id=service_task.ministry_id,
			department_id=service_task.department_id,
			agency_id=service_task.agency_id,
			ministry_departments_agencies_url=(
				service_task.ministry_departments_agencies_url
			),
			task_log=task_log,
			scrape_client=scrape_client,
		)

		return ServicesScrapedIdentifier(
			ministry_id=service_task.ministry_id,
			department_id=service_task.department_id,
			agency_id=service_task.agency_id,
		)

	# --- Processing methods ---

	def process_ministries_list_data(
		self,
		task_log: str,
		task: SchedulerTask,
	) -> MinistryIdentifiers:
		"""
		Method to process the raw HTML content of the
		ministries list page into structured MinistryEntry
		data.
		"""
		if not does_file_exist(self.file):
			logger.error(
				f'[{self.handler_name}]\n'
				f'Ministries list file does not exist at '
				f'{self.file!r}, cannot process data.',
				extra={'task': task_log},
			)

			raise ExecutorProcessingFailure(
				message=f'Ministries list file does not '
				f'exist at{self.file!r}, cannot process '
				'data.',
				task_log=task_log,
				task=task,
			)

		html_content = read_file(self.file)

		ministry_entries = (
			ministries_list_processing_recipe(
				html=html_content,
				task_log=task_log,
				task=task,
			)
		)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministries list data processed for '
			f'{len(ministry_entries)} ministries.',
			extra={'task': task_log},
		)

		self.ministry_entries = ministry_entries
		return MinistryIdentifiers(
			ministry_ids=list(ministry_entries.keys()),
		)

	async def _process_ministry_page_data(
		self,
		ministry_id: str,
		task_log: str,
		task: SchedulerTask,
	) -> tuple[
		MinistryPageProcessingResult,
		MinistryPageOverviewData,
	]:
		"""
		Method to process the raw HTML content of a
		ministry page into structured data and update
		handler state with observed data.
		"""

		# Check if scraped ministry page data exists in
		# file, if not raise error as processing cannot be
		# performed
		ministry_overview_file = (
			self._build_ministry_overview_file_path(
				ministry_id
			)
		)

		ministry_departments_agencies_file = (  # noqa: E501
			self._build_ministry_departments_agencies_file_path(
				ministry_id
			)
		)

		if not does_file_exist(
			ministry_overview_file
		) or not does_file_exist(
			ministry_departments_agencies_file
		):
			logger.error(
				f'[{self.handler_name}]\n'
				f'Ministry page files do not exist for '
				f'{ministry_id} at {ministry_overview_file!r} '  # noqa: E501
				f'and {ministry_departments_agencies_file!r}, '  # noqa: E501
				f'cannot process data.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message=f'Ministry page files do not exist '
				f'for {ministry_id} at {ministry_overview_file!r} '  # noqa: E501
				f'and {ministry_departments_agencies_file!r}, '  # noqa: E501
				f'cannot process data.',
				task_log=task_log,
				task=task,
			)

		# With data, read content from files and process
		# data into structured format
		ministry_url = self.ministry_entries[
			ministry_id
		].ministry_url

		# Overview data
		overview_html = read_file(ministry_overview_file)
		ministry_overview_processed_data = (
			ministry_overview_processing_recipe(
				html=overview_html, ministry_id=ministry_id
			)
		)

		# Departments and agencies data
		departments_agencies_html = read_file(
			ministry_departments_agencies_file
		)
		ministry_departments_agencies_processed_data = (  # noqa: E501
			ministry_departments_agencies_processing_recipe(
				html=departments_agencies_html,
				ministry_id=ministry_id,
				ministry_url=ministry_url,
			)
		)
		department_entries, ministry_page_agency_data = (
			ministry_departments_agencies_processed_data
		)

		# Package data into response type for
		# return and update
		ministry_services_identifier = (
			build_ministry_services_identifier(
				ministry_id=ministry_id,
				departments=department_entries,
				agencies=ministry_page_agency_data,
			)
		)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministry page data processed for ministry '
			f'{ministry_id}.',
			extra={'task': task_log},
		)
		ministry_page_processing_result = MinistryPageProcessingResult(  # noqa: E501
			ministry_id=ministry_id,
			ministry_services_identifier=ministry_services_identifier,
			department_entries=department_entries,
			ministry_page_agency_data=ministry_page_agency_data,
		)
		return (
			ministry_page_processing_result,
			ministry_overview_processed_data,
		)

	async def process_ministries_pages_data(
		self,
		ministry_task_list: MinistryTaskListPayload,
		task_log: str,
		task: SchedulerTask,
	) -> tuple[
		MinistryServicesIdentifiersList,
		list[DepartmentEntry],
		list[MinistryPageAgencyData],
	]:
		"""
		Method to process the raw HTML content of all
		ministry pages into structured data and update
		handler state with observed data.
		"""
		# Check which ministries have been scheduled
		# for processing from request
		ministry_tasks = [
			ministry_task.ministry_id
			for ministry_task in ministry_task_list.ministry_ids  # noqa: E501
		]

		# Process each ministry page data in parallel and
		# gather results.
		tasks = [
			asyncio.create_task(
				self._process_ministry_page_data(
					ministry_id=ministry_id,
					task_log=task_log,
					task=task,
				)
			)
			for ministry_id in ministry_tasks
		]

		results_pure: list[
			tuple[
				MinistryPageProcessingResult,
				MinistryPageOverviewData,
			]
			| BaseException
		] = await asyncio.gather(
			*tasks, return_exceptions=True
		)
		results: list[
			tuple[
				MinistryPageProcessingResult,
				MinistryPageOverviewData,
			]
		] = []

		# Raise error if any of the tasks resulted in an
		# exception, use this to filter out successful
		# results from failed ones
		for result in results_pure:
			if isinstance(result, BaseException):
				logger.error(
					f'[{self.handler_name}]\n'
					f'Error processing ministry page data: '
					f'{result!r}',
					extra={'task': task_log},
				)
				raise ExecutorProcessingFailure(
					message=f'Error processing ministry '
					f'page data: {result!r}',
					task_log=task_log,
					task=task,
				)
			else:
				results.append(result)

		# Batch apply observed data from
		# processing each ministry page to handler state
		ministry_page_overview_data_list = [
			result[1] for result in results
		]
		self._apply_ministry_page_overview_data_batch(
			ministry_page_overview_data_list,
			task_log,
			task,
		)

		# Extract data from results to pass
		# to other handlers and update scheduler state
		ministry_page_processing_results = [
			result[0] for result in results
		]

		# Flatten data for return
		ministry_services_identifiers: list[
			MinistryServicesIdentifier
		] = []
		department_entries: list[DepartmentEntry] = []
		ministry_page_agency_data: list[
			MinistryPageAgencyData
		] = []
		for (
			ministry_page_processing_result
		) in ministry_page_processing_results:
			ministry_services_identifiers.append(
				ministry_page_processing_result.ministry_services_identifier
			)
			department_entries.extend(
				ministry_page_processing_result.department_entries.values()
			)
			ministry_page_agency_data.extend(
				ministry_page_processing_result.ministry_page_agency_data.values()
			)

		ministry_services_identifiers_list = (  # noqa: E501
			MinistryServicesIdentifiersList(
				ministry_services_identifiers=ministry_services_identifiers
			)
		)
		return (
			ministry_services_identifiers_list,
			department_entries,
			ministry_page_agency_data,
		)

	async def _process_ministry_page_services_data(
		self,
		service_task: ServiceTaskPayload,
		task_log: str,
		task: SchedulerTask,
	) -> list[ServiceEntry]:
		"""
		Method to process the raw HTML content of a
		ministry services page into structured service
		data.
		"""
		services_file = (
			self._build_ministry_services_file_path(
				service_task.ministry_id,
				service_task.department_id,
				service_task.agency_id,
			)
		)

		if not does_file_exist(services_file):
			logger.error(
				f'[{self.handler_name}]\n'
				f'Ministry services file does not exist '
				f'for {service_task.ministry_id} under '
				f'department {service_task.department_id} '
				f'and agency {service_task.agency_id} at '
				f'{services_file!r}, cannot process data.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message=f'Ministry services file does not '
				f'exist for {service_task.ministry_id} '
				f'under department {service_task.department_id} '  # noqa: E501
				f'and agency {service_task.agency_id} at '
				f'{services_file!r}, cannot process data.',
				task_log=task_log,
				task=task,
			)

		services_html = read_file(services_file)
		service_entries = (
			ministry_service_processing_recipe(
				html=services_html,
				ministry_id=service_task.ministry_id,
				department_id=service_task.department_id,
				agency_id=service_task.agency_id,
			)
		)
		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministry services data processed for '
			f'{len(service_entries)} services under '
			f'ministry {service_task.ministry_id}, '
			f'department {service_task.department_id} and '
			f'agency {service_task.agency_id}.',
			extra={'task': task_log},
		)
		return list(service_entries.values())

	async def process_service_task_list(
		self,
		service_task_list: ServiceTaskListPayload,
		task_log: str,
		task: SchedulerTask,
	) -> tuple[
		ServicesProcessedIdentifier, list[ServiceEntry]
	]:
		"""
		Method to process a list of service tasks for a
		specific ministry, department and agency, and
		return a structured identifier for the processed
		services.

		Note: all services in the list should belong to the
		same ministry for the scheduler to maintain order of
		operations.
		"""
		# Make sure all tasks in the list belong to the
		# same ministry
		ministry_ids = set(
			task.ministry_id
			for task in service_task_list.service_tasks
		)
		if len(ministry_ids) != 1:
			logger.error(
				f'[{self.handler_name}]\n'
				'Service task list contains tasks for '
				f'multiple ministries: {ministry_ids}. '
				'All tasks in a service task list should '
				'belong to the same ministry.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message='Service task list contains tasks '
				'for multiple ministries. All tasks in a '
				'service task list should belong to the '
				'same ministry.',
				task_log=task_log,
				task=task,
			)

		task_ministry_id = ministry_ids.pop()

		# Process each service task in the list
		tasks = [
			asyncio.create_task(
				self._process_ministry_page_services_data(
					service_task=service_task,
					task_log=task_log,
					task=task,
				)
			)
			for service_task in service_task_list.service_tasks  # noqa: E501
		]
		raw_results: list[
			list[ServiceEntry] | BaseException
		] = await asyncio.gather(
			*tasks, return_exceptions=True
		)

		# Check for exceptions in results
		for result in raw_results:
			if isinstance(result, BaseException):
				logger.error(
					f'[{self.handler_name}]\n'
					f'Error processing service task list: '
					f'{result!r}',
					extra={'task': task_log},
				)
				raise ExecutorProcessingFailure(
					message=f'Error processing service '
					f'task list: {result!r}',
					task_log=task_log,
					task=task,
				)

		# Flatten list of service entries
		service_entries: list[ServiceEntry] = [
			service_entry
			for sublist in raw_results
			for service_entry in sublist  # type: ignore
		]

		# Make sure each service belongs
		# to the same ministry
		ministry_ids = set(
			service_entry.ministry_id
			for service_entry in service_entries
		)
		if len(ministry_ids) != 1:
			logger.error(
				f'[{self.handler_name}]\n'
				'Processed service entries belong to '
				f'multiple ministries: {ministry_ids}. All '
				'services processed in a batch should '
				'belong to the same ministry.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message='Processed service entries belong '
				'to multiple ministries. All services '
				'processed in a batch should belong to the '
				'same ministry.',
				task_log=task_log,
				task=task,
			)

		processing_ministry_id = ministry_ids.pop()

		if processing_ministry_id != task_ministry_id:
			logger.error(
				f'[{self.handler_name}]\n'
				f'Mismatch between ministry_id of service '
				f'tasks ({task_ministry_id}) and '
				f'ministry_id of processed service entries '
				f'({processing_ministry_id}).',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message='Mismatch between ministry_id of '
				'service tasks and ministry_id of '
				'processed service entries.',
				task_log=task_log,
				task=task,
			)

		# Build services processed identifier for the
		# ministry based on observed data from processing
		# the ministry services pages
		services_processed_identifier = (
			build_services_processed_identifier(
				ministry_id=processing_ministry_id,
				services=service_entries,
			)
		)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Service task list processed for ministry '
			f'{processing_ministry_id} '
			f'with {len(service_entries)} services. '
			f'Generated services processed identifier: '
			f'{services_processed_identifier}.',
			extra={'task': task_log},
		)

		return (
			services_processed_identifier,
			service_entries,
		)

	# --- Data retrieval methods --- #

	def get_ministry_identifiers(
		self, task_log: str, task: SchedulerTask
	) -> MinistryIdentifiers:
		"""
		Method to retrieve the identifiers of the
		ministries observed during processing.
		"""
		if not self.ministry_entries:
			logger.warning(
				f'[{self.handler_name}]\n'
				f'No ministry entries found in handler '
				f'state when retrieving ministry '
				f'identifiers.',
				extra={'handler': self.handler_name},
			)
			raise ExecutorProcessingFailure(
				message='No ministry entries found in '
				'handler state when retrieving ministry '
				'identifiers.',
				task_log=task_log,
				task=task,
			)
		return MinistryIdentifiers(
			ministry_ids=list(self.ministry_entries.keys()),
		)

	# --- Ministry state update methods --- #

	def _apply_ministry_page_overview_data(
		self,
		ministry_id: str,
		overview_data: MinistryPageOverviewData,
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to update the handler state for a specific
		ministry with the data observed from processing
		the ministry page.
		"""
		ministry_entry = self.ministry_entries.get(
			ministry_id
		)
		if not ministry_entry:
			logger.error(
				f'[{self.handler_name}]\n'
				f'Ministry entry not found in handler '
				f'state for ministry_id {ministry_id} when '
				f'applying ministry page processed data.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message=f'Ministry entry not found in '
				f'handler state for ministry_id '
				f'{ministry_id} when applying ministry '
				f'page processed data.',
				task_log=task_log,
				task=task,
			)

		# Update ministry entry with observed data
		ministry_entry.ministry_description = (
			overview_data.ministry_description
		)
		ministry_entry.reported_agency_count = (
			overview_data.reported_agency_count
		)
		ministry_entry.reported_service_count = (
			overview_data.reported_service_count
		)

	def _apply_ministry_page_overview_data_batch(
		self,
		ministry_page_overview_results: list[
			MinistryPageOverviewData
		],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to update the handler state for a batch of
		ministries with the data observed from processing
		the ministry overview pages.
		"""
		for overview_data in ministry_page_overview_results:
			self._apply_ministry_page_overview_data(
				ministry_id=overview_data.ministry_id,
				overview_data=overview_data,
				task_log=task_log,
				task=task,
			)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Batch applied ministry page overview data '
			f'for {len(ministry_page_overview_results)} '
			f'ministries.',
			extra={'task': task_log},
		)

	def apply_agency_count_by_ministry(
		self,
		agency_count_by_ministry: dict[str, int],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the ministries state
		using a dictionary of agency count by ministry.
		"""
		for (
			ministry_id,
			agency_count,
		) in agency_count_by_ministry.items():
			if ministry_id in self.ministry_entries:
				ministry_entry = self.ministry_entries[
					ministry_id
				]
				ministry_entry.observed_agency_count = (
					agency_count
				)
				self.ministry_entries[ministry_id] = (
					ministry_entry
				)

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to ministries '
			f'state with agency count for '
			f'{len(agency_count_by_ministry)} '
			f'ministries.',
			extra={'task': task_log},
		)

	def apply_service_count_by_ministry(
		self,
		service_count_by_ministry: dict[str, int],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the ministries state
		using a dictionary of service count by ministry.
		"""
		for (
			ministry_id,
			service_count,
		) in service_count_by_ministry.items():
			if ministry_id in self.ministry_entries:
				ministry_entry = self.ministry_entries[
					ministry_id
				]
				ministry_entry.observed_service_count = (
					service_count
				)
				self.ministry_entries[ministry_id] = (
					ministry_entry
				)

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to ministries '
			f'state with service count for '
			f'{len(service_count_by_ministry)} '
			f'ministries.',
			extra={'task': task_log},
		)

	def apply_department_count_by_ministry(
		self,
		department_count_by_ministry: dict[str, int],
		task_log: str,
		task: SchedulerTask,
	) -> None:
		"""
		Method to apply updates to the ministries state
		using a dictionary of department count by ministry.
		"""
		for (
			ministry_id,
			department_count,
		) in department_count_by_ministry.items():
			if ministry_id in self.ministry_entries:
				ministry_entry = self.ministry_entries[
					ministry_id
				]
				ministry_entry.observed_department_count = (
					department_count
				)
				self.ministry_entries[ministry_id] = (
					ministry_entry
				)

		logger.info(
			f'[{self.handler_name}]\n'
			f'[TASK INFO]: Applied update to ministries '
			f'state with department count for '
			f'{len(department_count_by_ministry)} '
			f'ministries.',
			extra={'task': task_log},
		)

	# --- Finalisation and analytics methods --- #

	def ministries_insights(
		self, ministry_df: pd.DataFrame
	) -> None:
		"""
		Use the insights engine to render a report
		based on the ministry data.
		"""

		insights = render_insights_report(
			df=ministry_df,
			id_col='ministry_id',
			state=self.ministry_entries,
			title='Ministry Insights',
		)
		write_file(
			path=self.insights_file,
			content=insights,
		)

	def finalise(self) -> None:
		"""
		Method to finalise the Ministry handler by saving
		the processed data to files and performing analysis.
		"""
		# Convert state to DataFrame for analysis
		ministry_df = state_to_df(
			self.ministry_entries, MinistryEntry
		)

		# Save final state
		self.save_state()

		# Save processed data to files
		save_df(
			df=ministry_df,
			csv_path=self.processed_data_csv,
			json_path=self.processed_data_json,
		)

		# Produce insights
		self.ministries_insights(ministry_df)

		logger.info(
			f'[{self.handler_name}]\n'
			f'Ministry handler finalised. Processed data '
			f'saved to {self.processed_data_dir!r} and '
			f'insights saved to {self.insights_file!r}.',
		)
