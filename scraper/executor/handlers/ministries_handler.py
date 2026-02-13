"""
This module contains the ministries handler for
executing scheduled tasks related to the ministries
scope of the scraping process.
"""

import asyncio
import logging
from pathlib import Path

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.processing.recipes.ministries import (
	ministries_departments_agencies_processing_recipe,
	ministries_overview_processing_recipe,
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
	MinistryPageProcessedData,
)
from scraper.schemas.scheduler_task import (
	MinistryIdentifiers,
	MinistryServicesIdentifier,
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

logger = logging.getLogger(__name__)


class MinistriesHandler:
	"""
	Handler for executing scheduled tasks
	related to the ministries scope.
	"""

	def __init__(self) -> None:
		# Handler configuration
		self.handler_name = 'MinistriesHandler'
		self.seed_url = SeedUrls.MINISTRIES_LIST_URL
		self.file = (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ 'ministries_list.html'
		)

		# Entity state
		self.ministry_entries: dict[str, MinistryEntry] = {}

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
			f'Ministries list page scraped and '
			f'saved to {self.file!r}.',
			extra={'task': task_log},
		)
		return ministries_list_html

	async def scrape_ministry_page(
		self,
		ministry_id: str,
		ministry_url: str,
		task_log: str,
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

		ministry_departments_agencies_file = self._build_ministry_departments_agencies_file_path(  # noqa: E501
			ministry_id
		)

		# If both files already exist,
		# read and return content
		if does_file_exist(
			ministry_overview_file
		) and does_file_exist(
			ministry_departments_agencies_file
		):
			logger.info(
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
				overview=overview_html,
				departments_and_agencies=departments_agencies_html,
			)

		ministry_page_data = await scrape_client.run(
			url=ministry_url,
			task_log=task_log,
			recipe=ministry_page_recipe,
		)

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
				'Ministry services file already exists for '
				f'{ministry_id} under department '
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
			'Ministry services page scraped for '
			f'{ministry_id} under department {department_id} '  # noqa: E501
			f'and agency {agency_id}, saved to {services_file!r}.',  # noqa: E501
			extra={'task': task_log},
		)
		return services_html

	# --- Scrape and process methods ---

	async def scrape_and_package_ministry_page_data(
		self,
		ministry_id: str,
		task_log: str,
		task: SchedulerTask,
		scrape_client: ScrapeClient,
	) -> tuple[
		MinistryServicesIdentifier,
		dict[str, DepartmentEntry],
		dict[str, MinistryPageAgencyData],
	]:
		"""
		Method to scrape an individual ministry page and
		return the data packaged in a structured format.
		"""
		# Retrieve ministry URL from handler state
		ministry_entry = self.ministry_entries.get(
			ministry_id
		)
		if not ministry_entry:
			logger.error(
				f'Ministry entry not found in handler '
				f'state for ministry_id {ministry_id} '
				f' when scraping and  packaging ministry '
				f'page data.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message=f'Ministry entry not found in '
				f' handler state for ministry_id'
				f' {ministry_id} when scraping and  '
				f'packaging ministry page data.',
				task_log=task_log,
				task=task,
			)
		ministry_url = ministry_entry.ministry_url

		# Perform scraping of ministry page data
		ministry_page_data = (
			await self.scrape_ministry_page(
				ministry_id=ministry_id,
				ministry_url=ministry_url,
				task_log=task_log,
				scrape_client=scrape_client,
			)
		)
		# Process ministry overview and departments/agencies
		# page data
		ministry_overview_processed_data = (
			ministries_overview_processing_recipe(
				html=ministry_page_data.overview,
			)
		)
		ministry_departments_agencies_processed_data = (  # noqa: E501
			ministries_departments_agencies_processing_recipe(
				html=ministry_page_data.departments_and_agencies,
				ministry_id=ministry_id,
				ministry_url=ministry_url,
			)
		)

		# Update handler state with observed data from
		# processing ministry page data
		self._apply_ministry_page_processed_data(
			ministry_id=ministry_id,
			processed_data=ministry_overview_processed_data,
			task_log=task_log,
			task=task,
		)

		# Build services identifier for the ministry based
		# on observed data from processing the ministry page
		department_entries, ministry_page_agency_data = (
			ministry_departments_agencies_processed_data
		)
		ministry_services_identifier = (
			build_ministry_services_identifier(
				ministry_id=ministry_id,
				departments=department_entries,
				agencies=ministry_page_agency_data,
			)
		)

		return (
			ministry_services_identifier,
			department_entries,
			ministry_page_agency_data,
		)

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
	) -> None:
		"""
		Method to process the raw HTML content of the
		ministries list page into structured MinistryEntry
		data.
		"""
		if not does_file_exist(self.file):
			logger.error(
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
			f'Ministries list data processed for '
			f'{len(ministry_entries)} ministries.',
			extra={'task': task_log},
		)

		self.ministry_entries = ministry_entries

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
				'Mismatch between ministry_id of service '
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
				'No ministry entries found in handler '
				'state when retrieving ministry '
				'identifiers.',
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

	def _apply_ministry_page_processed_data(
		self,
		ministry_id: str,
		processed_data: MinistryPageProcessedData,
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
			processed_data.ministry_description
		)
		ministry_entry.reported_agency_count = (
			processed_data.reported_agency_count
		)
		ministry_entry.reported_service_count = (
			processed_data.reported_service_count
		)
