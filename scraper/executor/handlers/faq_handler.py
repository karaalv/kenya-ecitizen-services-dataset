"""
This module contains the FAQ handler for
executing scheduled tasks related to the FAQ
scope of the scraping process.
"""

import logging

from scraper.scraping.recipes.faq_page import (
	faq_page_recipe,
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


class FAQHandler:
	"""
	Handler for executing scheduled tasks
	related to the FAQ scope.
	"""

	def __init__(self) -> None:
		self.handler_name = 'FAQHandler'
		self.seed_url = SeedUrls.FAQ_URL
		self.file = Paths.RAW_DATA_DIR / 'faq' / 'faq.html'

		# --- Scraping methods ---

	async def scrape_faq_page(
		self,
		task_log: str,
		scrape_client: ScrapeClient,
	) -> str:
		"""
		Method to scrape the FAQ page content.
		"""
		# If file already exists, read and return content
		if does_file_exist(self.file):
			logger.info(
				f'FAQ file already exists at '
				f'{self.file!r}, reading content.',
				extra={'task': task_log},
			)
			return read_file(self.file)

		faq_html = await scrape_client.run(
			url=self.seed_url,
			task_log=task_log,
			recipe=faq_page_recipe,
		)

		# Save scraped content to file
		write_file(
			path=self.file,
			content=faq_html,
		)

		logger.info(
			f'FAQ page scraped and saved to {self.file!r}.',
			extra={'task': task_log},
		)

		return faq_html
