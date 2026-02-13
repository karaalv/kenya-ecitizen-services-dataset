"""
This module contains the ministries handler for
executing scheduled tasks related to the ministries
scope of the scraping process.
"""

import logging

from scraper.schemas.ministries import MinistryPageData
from scraper.schemas.scheduler_task import (
	MinistryServicesIdentifier,
	ServicesScrapedIdentifier,
	ServiceTaskPayload,
)
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
		self.handler_name = 'MinistriesHandler'
		self.seed_url = SeedUrls.MINISTRIES_LIST_URL
		self.file = (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ 'ministries_list.html'
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
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ ministry_id
			/ 'overview.html'
		)

		ministry_departments_agencies_file = (
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ ministry_id
			/ 'departments_agencies.html'
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
			Paths.RAW_DATA_DIR
			/ 'ministries'
			/ ministry_id
			/ department_id
			/ agency_id
			/ 'services.html'
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

	# --- Processing methods ---

	async def scrape_and_package_ministry_page_data(
		self,
		ministry_id: str,
		task_log: str,
		scrape_client: ScrapeClient,
	) -> MinistryServicesIdentifier:
		"""
		Method to scrape an individual ministry page and
		return the data packaged in a structured format.
		"""
		# TODO: Use internal logic to
		# resolve ministry URL from ID
		_ministry_page_data = (
			await self.scrape_ministry_page(
				ministry_id=ministry_id,
				ministry_url='',  # Placeholder
				task_log=task_log,
				scrape_client=scrape_client,
			)
		)
		# TODO: Add logic to package this data into
		# MinistryServicesIdentifier for the scheduler
		return MinistryServicesIdentifier(
			ministry_id=ministry_id,
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
		_service_page_html = await self.scrape_ministry_services_page(  # noqa: E501
			ministry_id=service_task.ministry_id,
			department_id=service_task.department_id,
			agency_id=service_task.agency_id,
			ministry_departments_agencies_url=service_task.ministry_departments_agencies_url,
			task_log=task_log,
			scrape_client=scrape_client,
		)
		# TODO: any processing needed for
		# this crap goes here
		return ServicesScrapedIdentifier(
			ministry_id=service_task.ministry_id,
			department_id=service_task.department_id,
			agency_id=service_task.agency_id,
		)
