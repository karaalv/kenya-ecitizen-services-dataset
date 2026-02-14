"""
This module contains the FAQ handler for
executing scheduled tasks related to the FAQ
scope of the scraping process.
"""

import logging

import pandas as pd

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.insights.core import render_insights_report
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
from scraper.utils.handlers import (
	save_df,
	state_to_df,
	state_to_str,
	str_to_state,
)

logger = logging.getLogger(__name__)


class FAQHandler:
	"""
	Handler for executing scheduled tasks
	related to the FAQ scope.
	"""

	def __init__(self) -> None:
		# Handler configuration
		self.handler_name = 'FAQ HANDLER'
		self.seed_url = SeedUrls.FAQ_URL
		self.file = Paths.RAW_DATA_DIR / 'faq' / 'faq.html'
		self.state_file = (
			Paths.TEMP_DIR / 'faq_handler_state.json'
		)

		# Processed file locations
		self.processed_data_dir = (
			Paths.PROCESSED_DATA_DIR / 'faq'
		)

		self.processed_data_json = (
			self.processed_data_dir / 'faqs.json'
		)
		self.processed_data_csv = (
			self.processed_data_dir / 'faqs.csv'
		)

		# Insights file location
		self.insights_file = Paths.INSIGHTS_DIR / 'faqs.md'

		# Entity state
		self.faq_entities: dict[str, FAQEntry] = (
			self._load_state()
		)

	def save_state(self) -> None:
		"""
		Method to save the handler state to a file.
		"""
		state_str = state_to_str(self.faq_entities)
		write_file(
			path=self.state_file,
			content=state_str,
		)

	def _load_state(self) -> dict[str, FAQEntry]:
		"""
		Method to load the handler state from a file.
		"""
		if not does_file_exist(self.state_file):
			logger.debug(
				f'[{self.handler_name}]\n'
				f'FAQ handler state file not found at '
				f'{self.state_file!r}, starting with '
				f'empty state.',
			)
			return {}

		state_str = read_file(self.state_file)
		return str_to_state(state_str, FAQEntry)

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
			logger.debug(
				f'[{self.handler_name}]\n'
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

		logger.debug(
			f'[{self.handler_name}]\n'
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
				f'[{self.handler_name}]\n'
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

		logger.debug(
			f'[{self.handler_name}]\n'
			f'FAQ page processed into'
			f' {len(self.faq_entities)} entries.',
			extra={'task': task_log},
		)

	# --- Finalisation and analytics methods --- #

	def faqs_insights(self, faq_df: pd.DataFrame) -> None:
		"""
		Use the insights engine to render a report
		based on the FAQ data.
		"""

		insights = render_insights_report(
			df=faq_df,
			id_col='faq_id',
			state=self.faq_entities,
			title='FAQ Insights',
		)
		write_file(
			path=self.insights_file,
			content=insights,
		)

	def finalise(self) -> None:
		"""
		Method to finalise the FAQ handler by saving the
		processed data to files and performing analysis.
		"""
		# Convert state to DataFrame for analysis
		faq_df = state_to_df(self.faq_entities, FAQEntry)

		# Save final state
		self.save_state()

		# Save processed data to files
		save_df(
			df=faq_df,
			csv_path=self.processed_data_csv,
			json_path=self.processed_data_json,
		)

		# Produce insights
		self.faqs_insights(faq_df)

		logger.debug(
			f'[{self.handler_name}]\n'
			f'FAQ handler finalised. Processed data saved '
			f'to {self.processed_data_dir!r} and insights '
			f'saved to {self.insights_file!r}.',
		)
