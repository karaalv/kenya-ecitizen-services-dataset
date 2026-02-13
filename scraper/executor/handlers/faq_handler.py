"""
This module contains the FAQ handler for
executing scheduled tasks related to the FAQ
scope of the scraping process.
"""

import logging

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.processing.recipes.faq_page import (
	faq_page_processing_recipe,
)
from scraper.schemas.faq import FAQEntry
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.scraping.recipes.faq_page import (
	faq_page_scrape_recipe,
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
		# Handler configuration
		self.handler_name = 'FAQHandler'
		self.seed_url = SeedUrls.FAQ_URL
		self.file = Paths.RAW_DATA_DIR / 'faq' / 'faq.html'

		# Entity state
		self.faq_entities: dict[str, FAQEntry] = {}

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
			recipe=faq_page_scrape_recipe,
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

	# --- Processing methods ---

	def process_faq_page(
		self, task_log: str, task: SchedulerTask
	) -> None:
		"""
		Method to process the raw HTML content of
		the FAQ page into structured FAQEntry
		entities.
		"""
		if not does_file_exist(self.file):
			logger.error(
				f'FAQ file not found at {self.file!r} '
				'for processing.',
				extra={'task': task_log},
			)
			raise ExecutorProcessingFailure(
				message=f'FAQ file not found at '
				f'{self.file!r} for processing.',
				task_log=task_log,
				task=task,
			)

		faq_html = read_file(self.file)

		self.faq_entities = faq_page_processing_recipe(
			html=faq_html,
			task_log=task_log,
			task=task,
		)

		logger.info(
			f'FAQ page processed into'
			f' {len(self.faq_entities)} entries.',
			extra={'task': task_log},
		)
