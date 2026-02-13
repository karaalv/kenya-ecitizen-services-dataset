"""
This module contains the agencies handler for
executing scheduled tasks related to the agencies
scope of the scraping process.
"""

import logging

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

logger = logging.getLogger(__name__)


class AgenciesHandler:
	"""
	Handler for executing scheduled tasks
	related to the agencies scope.
	"""

	def __init__(self) -> None:
		self.handler_name = 'AgenciesHandler'
		self.seed_url = SeedUrls.AGENCIES_LIST_URL
		self.file = (
			Paths.RAW_DATA_DIR
			/ 'agencies'
			/ 'agencies_list.html'
		)

		# --- Scraping methods ---

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
			f'Agencies list page scraped and '
			f'saved to {self.file!r}.',
			extra={'task': task_log},
		)

		return agencies_list_html
