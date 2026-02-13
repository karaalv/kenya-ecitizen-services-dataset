"""
This module contains processing recipes for
turning the raw HTML content of the Ministries
pages into structured data.
"""

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from scraper.schemas.departments import DepartmentEntry
from scraper.schemas.ministries import (
	MinistryPageAgencyData,
	MinistryPageProcessedData,
)
from scraper.schemas.services import ServiceEntry
from scraper.utils.hashing import stable_id
from scraper.utils.normalise import (
	normalise_text,
	normalise_url,
	parse_int,
)


def ministries_overview_processing_recipe(
	html: str,
) -> MinistryPageProcessedData:
	"""
	Recipe to process the raw HTML content of
	the ministries overview page.
	"""
	soup = BeautifulSoup(html, 'lxml')

	# Reported counts are in dd tags
	# agencies count is in the first dd,
	# services count in the second
	dd_tags = soup.find_all('dd')

	total_agencies_raw = (
		dd_tags[0].get_text(strip=True) if dd_tags else None
	)
	total_services_raw = (
		dd_tags[1].get_text(strip=True)
		if len(dd_tags) > 1
		else None
	)

	# Ministry description is in article tag
	description_tag = soup.find('article')
	description_raw = (
		description_tag.get_text(' ', strip=True)
		if description_tag
		else None
	)

	total_agencies_str = (
		str(total_agencies_raw)
		if total_agencies_raw
		else ''
	)
	total_services_str = (
		str(total_services_raw)
		if total_services_raw
		else ''
	)
	description_str = (
		str(description_raw) if description_raw else ''
	)

	return MinistryPageProcessedData(
		reported_agency_count=parse_int(total_agencies_str),
		reported_service_count=parse_int(
			total_services_str
		),
		ministry_description=normalise_text(
			description_str
		),
	)


# Helper functions to process the ministries departments
# and agencies page
def _dept_name(department_block) -> str:
	"""
	Helper function to extract and normalise
	the department name from a given block
	in the DOM.
	"""
	sp = department_block.find('span')
	if sp is None:
		return ''
	return normalise_text(sp.get_text(' '))


def _dept_url(
	department_block,
	ministry_url: str,
) -> str:
	a = department_block.select_one('ul a[href]')
	if a is None:
		return ministry_url

	href = a.get('href', '')
	url = normalise_url(href)

	qs = parse_qs(urlparse(url).query)
	dq = qs.get('department', [''])[0]

	if not dq:
		return ministry_url

	return normalise_url(f'{ministry_url}?department={dq}')


def ministries_departments_agencies_processing_recipe(
	html: str,
	ministry_id: str,
	ministry_url: str,
) -> tuple[
	dict[str, DepartmentEntry],
	dict[str, MinistryPageAgencyData],
]:
	"""
	Recipe to process the raw HTML content of
	the ministries departments and agencies page.

	Returns a tuple of two dictionaries:
	- [0]: dict[department_id, DepartmentEntry]
	- [1]: dict[agency_name_hash, MinistryPageAgencyData]
	"""
	soup = BeautifulSoup(html, 'lxml')

	root = soup.find('ul', role='listbox')
	if root is None:
		return {}, {}

	department_entries: dict[str, DepartmentEntry] = {}
	ministry_agencies_data: dict[
		str, MinistryPageAgencyData
	] = {}

	for department_block in root.find_all(
		'div', recursive=False
	):
		department_name = _dept_name(department_block)

		# If no department name found, skip this block
		if not department_name:
			continue

		department_id = stable_id(
			[ministry_id, department_name]
		)
		links = department_block.select('ul a[href]')
		observed_agency_count = 0

		for a in links:
			agency_name_raw = a.get_text(' ', strip=True)
			agency_name = normalise_text(agency_name_raw)

			if not agency_name:
				continue
			agency_services_url_raw = a.get('href', '')
			agency_services_url_str = (
				str(agency_services_url_raw)
				if agency_services_url_raw
				else ''
			)

			observed_agency_count += 1
			agency_id = stable_id(
				[ministry_id, department_id, agency_name]
			)
			agency_services_url = normalise_url(
				agency_services_url_str
			)
			agency_name_hash = stable_id([agency_name])

			ministry_agencies_data[agency_name_hash] = (
				MinistryPageAgencyData(
					agency_id=agency_id,
					department_id=department_id,
					ministry_id=ministry_id,
					agency_name=agency_name,
					agency_name_hash=agency_name_hash,
					ministry_departments_agencies_url=agency_services_url,
				)
			)

		department_entries[department_id] = DepartmentEntry(
			department_id=department_id,
			ministry_id=ministry_id,
			department_name=department_name,
			observed_agency_count=observed_agency_count,
			observed_service_count=None,
			ministry_departments_url=_dept_url(
				department_block, ministry_url
			),
		)

	return department_entries, ministry_agencies_data


def ministry_service_processing_recipe(
	html: str,
	ministry_id: str,
	department_id: str,
	agency_id: str,
) -> dict[str, ServiceEntry]:
	"""
	Recipe to process the raw HTML content of
	a ministry department agency services page.

	Returns a dictionary of service_id to ServiceEntry.
	"""
	soup = BeautifulSoup(html, 'lxml')

	service_entries: dict[str, ServiceEntry] = {}

	service_items = soup.find_all('a')
	for item in service_items:
		service_name_raw = item.get_text(' ', strip=True)
		service_name = normalise_text(service_name_raw)

		if not service_name:
			continue

		service_id = stable_id(
			[
				ministry_id,
				department_id,
				agency_id,
				service_name,
			]
		)

		service_url_raw = item.get('href', '')
		service_url_str = (
			str(service_url_raw) if service_url_raw else ''
		)
		service_url = normalise_url(service_url_str)

		service_entries[service_id] = ServiceEntry(
			service_id=service_id,
			ministry_id=ministry_id,
			department_id=department_id,
			agency_id=agency_id,
			service_name=service_name,
			service_url=service_url,
		)

	return service_entries
