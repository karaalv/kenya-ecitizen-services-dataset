"""
This module contains the processing recipe for
turning the raw HTML content of the agencies list
page into structured AgencyEntry data.
"""

from bs4 import BeautifulSoup

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.schemas.agencies import AgencyEntry
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.utils.hashing import stable_id
from scraper.utils.normalise import (
	normalise_text,
	normalise_url,
)


def agencies_list_processing_recipe(
	html: str, task_log: str, task: SchedulerTask
) -> dict[str, AgencyEntry]:
	"""
	Recipe to process the raw HTML content of
	the agencies list page.
	"""
	soup = BeautifulSoup(html, 'lxml')
	agency_items = soup.find_all('a')

	agency_entries: dict[str, AgencyEntry] = {}

	for item in agency_items:
		# Url for agency
		agency_url_raw = item.get('href', '')
		agency_url_str = (
			str(agency_url_raw) if agency_url_raw else ''
		)

		# Url for agency logo
		img_tag = item.find('img')
		logo_url_raw = (
			img_tag.get('src', '') if img_tag else ''
		)
		logo_url_str = (
			str(logo_url_raw) if logo_url_raw else ''
		)

		# Extract the agency name
		h4_tag = item.find('h4')
		agency_name_raw = (
			h4_tag.get_text(' ', strip=True)
			if h4_tag
			else ''
		)

		# Extract description
		p_tag = item.find('p')
		agency_description_raw = (
			p_tag.get_text(' ', strip=True) if p_tag else ''
		)

		# Use agency hash as identifier,
		# will update to stable id later
		# in processing
		agency_name = normalise_text(agency_name_raw)
		agency_name_hash = stable_id([agency_name])

		if agency_name_hash in agency_entries:
			continue

		agency_entries[agency_name_hash] = AgencyEntry(
			agency_id='',
			agency_name_hash=agency_name_hash,
			ministry_id='',
			department_id='',
			agency_name=agency_name,
			agency_description=normalise_text(
				agency_description_raw
			),
			logo_url=normalise_url(logo_url_str),
			agency_url=normalise_url(agency_url_str),
			observed_service_count=None,
			ministry_departments_agencies_url='',
		)

	if not agency_entries:
		raise ExecutorProcessingFailure(
			message='No agency entries found during '
			f'processing. Found {len(agency_items)} '
			'potential items but failed to extract '
			'valid agency entries.',
			task=task,
			task_log=task_log,
		)

	return agency_entries
