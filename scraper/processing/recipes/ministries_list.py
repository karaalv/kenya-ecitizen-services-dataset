"""
This module contains the processing recipe for
turning the raw HTML content of the Ministries list
page into structured MinistryEntry data.
"""

from bs4 import BeautifulSoup

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.schemas.ministries import MinistryEntry
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.utils.hashing import stable_id
from scraper.utils.normalise import (
	normalise_text,
	normalise_url,
)


def ministries_list_processing_recipe(
	html: str, task_log: str, task: SchedulerTask
) -> dict[str, MinistryEntry]:
	"""
	Recipe to process the raw HTML content of
	the Ministries list page.
	"""
	soup = BeautifulSoup(html, 'lxml')
	ministry_items = soup.find_all('a')

	ministry_entries: dict[str, MinistryEntry] = {}

	for item in ministry_items:
		# Url for ministry
		ministry_url_raw = item.get('href', '')
		ministry_url_str = (
			str(ministry_url_raw)
			if ministry_url_raw
			else ''
		)

		# ministry name
		ministry_name_raw = item.get_text(' ', strip=True)
		ministry_name_str = (
			str(ministry_name_raw)
			if ministry_name_raw
			else ''
		)

		ministry_id = stable_id([ministry_name_str])

		if ministry_id in ministry_entries:
			continue

		ministry_entries[ministry_id] = MinistryEntry(
			ministry_id=ministry_id,
			ministry_name=normalise_text(ministry_name_str),
			ministry_description='',
			reported_agency_count=None,
			observed_agency_count=None,
			reported_service_count=None,
			observed_service_count=None,
			observed_department_count=None,
			ministry_url=normalise_url(ministry_url_str),
		)

	if not ministry_entries:
		raise ExecutorProcessingFailure(
			message=f'No ministry entries found during '
			f'processing. Found {len(ministry_entries)} '
			'entries, but unable to extract valid data.',
			task_log=task_log,
			task=task,
		)

	return ministry_entries
