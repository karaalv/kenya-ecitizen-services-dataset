"""
This module contains tests for the processing
recipes used to turn html documents into structured data.
"""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scraper.processing.recipes.agencies_list import (
	agencies_list_processing_recipe,
)
from scraper.processing.recipes.faq_page import (
	faq_page_processing_recipe,
)
from scraper.processing.recipes.ministries import (
	ministry_departments_agencies_processing_recipe,
	ministry_overview_processing_recipe,
	ministry_service_processing_recipe,
)
from scraper.processing.recipes.ministries_list import (
	ministries_list_processing_recipe,
)
from scraper.schemas.scheduler_task import (
	EmptyTask,
	ScrapingPhase,
	TaskOperation,
)
from scraper.utils.files import read_file

# --- Test data paths ---

TEST_DATA_DIR = (
	Path(__file__).resolve().parents[1] / 'test_data'
)

TEST_FAQ_PAGE_PATH = TEST_DATA_DIR / 'faq_page.html'
TEST_AGENCIES_LIST_PAGE_PATH = (
	TEST_DATA_DIR / 'agencies_list.html'
)
TEST_MINISTRIES_LIST_PAGE_PATH = (
	TEST_DATA_DIR / 'ministries_list.html'
)

TEST_MINISTRY_OVERVIEW_PAGE_PATH = (
	TEST_DATA_DIR / 'ministry_overview.html'
)
TEST_MINISTRY_AGENCIES_PAGE_PATH = (
	TEST_DATA_DIR / 'ministry_agencies.html'
)
TEST_MINISTRY_SERVICES_PAGE_PATH = (
	TEST_DATA_DIR / 'ministry_services.html'
)

# --- Test helper functions ---


def _get_query_params(url: str) -> dict[str, str]:
	"""
	Helper function to extract query parameters from a URL.
	"""
	parsed_url = urlparse(url)
	return {
		k: v[0]
		for k, v in parse_qs(parsed_url.query).items()
	}


# --- Test cases ---


def test_faq_page_processing_recipe():
	"""
	Test the faq_page_processing_recipe with a
	sample FAQ page HTML.
	"""
	html = read_file(TEST_FAQ_PAGE_PATH)
	task_log = 'Test log for FAQ page processing'
	task = EmptyTask(
		scope=ScrapingPhase.FAQ,
		operation=TaskOperation.FAQ_PROCESS,
	)

	faq_entries = faq_page_processing_recipe(
		html, task_log, task
	)

	# Basic assertions to check if the processing worked
	assert faq_entries is not None
	assert isinstance(faq_entries, dict)
	assert len(faq_entries) > 0

	# Assert that each id is unique
	assert len(faq_entries) == len(
		set(faq_entries.keys())
	), 'FAQ IDs are not unique'

	# Check that the entries have the expected structure
	for _, entry in faq_entries.items():
		assert hasattr(entry, 'faq_id')
		assert entry.faq_id is not None

		assert hasattr(entry, 'question')
		assert entry.question is not None

		assert hasattr(entry, 'answer')
		assert entry.answer is not None


def test_agencies_list_processing_recipe():
	"""
	Test the agencies_list_processing_recipe with a
	sample agencies list page HTML.
	"""
	html = read_file(TEST_AGENCIES_LIST_PAGE_PATH)
	task_log = 'Test log for agencies list processing'
	task = EmptyTask(
		scope=ScrapingPhase.AGENCIES_LIST,
		operation=TaskOperation.AGENCIES_LIST_PROCESS,
	)

	agency_entries = agencies_list_processing_recipe(
		html, task_log, task
	)

	# Basic assertions to check if the processing worked
	assert agency_entries is not None
	assert isinstance(agency_entries, dict)
	assert len(agency_entries) > 0

	# Assert that each id is unique
	assert len(agency_entries) == len(
		set(agency_entries.keys())
	), 'Agency name hashes are not unique'

	# Check that the entries have the expected structure
	for _, entry in agency_entries.items():
		assert hasattr(entry, 'agency_id')
		assert entry.agency_id is not None

		assert hasattr(entry, 'agency_name_hash')
		assert entry.agency_name_hash is not None

		assert hasattr(entry, 'agency_name')
		assert entry.agency_name is not None

		assert hasattr(entry, 'agency_description')
		assert entry.agency_description is not None

		assert hasattr(entry, 'agency_url')
		assert entry.agency_url is not None

		assert hasattr(entry, 'logo_url')
		assert entry.logo_url is not None


def test_ministries_list_processing_recipe():
	"""
	Test the ministries_list_processing_recipe with a
	sample ministries list page HTML.
	"""
	html = read_file(TEST_MINISTRIES_LIST_PAGE_PATH)
	task_log = 'Test log for ministries list processing'
	task = EmptyTask(
		scope=ScrapingPhase.MINISTRIES_LIST,
		operation=TaskOperation.MINISTRIES_LIST_PROCESS,
	)

	ministry_entries = ministries_list_processing_recipe(
		html, task_log, task
	)

	# Basic assertions to check if the processing worked
	assert ministry_entries is not None
	assert isinstance(ministry_entries, dict)
	assert len(ministry_entries) > 0

	# Check that the entries have the expected structure
	for _, entry in ministry_entries.items():
		assert hasattr(entry, 'ministry_id')
		assert entry.ministry_id is not None

		assert hasattr(entry, 'ministry_name')
		assert entry.ministry_name is not None

		assert hasattr(entry, 'ministry_url')
		assert entry.ministry_url is not None

	# Assert that each id is unique
	assert len(ministry_entries) == len(
		set(ministry_entries.keys())
	), 'Ministry IDs are not unique'


def test_ministry_overview_processing_recipe():
	"""
	Test the ministry_overview_processing_recipe with a
	sample ministry overview page HTML.
	"""
	html = read_file(TEST_MINISTRY_OVERVIEW_PAGE_PATH)
	processed_data = ministry_overview_processing_recipe(
		html
	)

	# Basic assertions to check if the processing worked
	assert processed_data is not None
	assert hasattr(processed_data, 'reported_agency_count')
	assert processed_data.reported_agency_count is not None

	assert hasattr(processed_data, 'reported_service_count')
	assert processed_data.reported_service_count is not None

	assert hasattr(processed_data, 'ministry_description')
	assert processed_data.ministry_description is not None


def test_ministry_departments_agencies_processing_recipe():
	"""
	Test the ministry_departments_agencies_processing_recipe
	with a sample ministry departments and agencies
	page HTML.
	"""
	html = read_file(TEST_MINISTRY_AGENCIES_PAGE_PATH)
	ministry_id = 'test_ministry_id'
	ministry_url = 'https://ecitizen.go.ke/en/ministries/the-state-law-office'

	department_entries, agency_data = (
		ministry_departments_agencies_processing_recipe(
			html=html,
			ministry_id=ministry_id,
			ministry_url=ministry_url,
		)
	)

	# Basic assertions to check if the processing worked
	assert department_entries is not None
	assert isinstance(department_entries, dict)
	assert len(department_entries) > 0
	assert len(department_entries) == len(
		set(department_entries.keys())
	), 'Department IDs are not unique'

	assert agency_data is not None
	assert isinstance(agency_data, dict)
	assert len(agency_data) > 0
	assert len(agency_data) == len(
		set(agency_data.keys())
	), 'Agency name hashes are not unique'

	# Check that the department entries have the
	# expected structure
	for _, dept_entry in department_entries.items():
		assert hasattr(dept_entry, 'department_id')
		assert dept_entry.department_id is not None

		assert hasattr(dept_entry, 'ministry_id')
		assert dept_entry.ministry_id is not None
		assert dept_entry.ministry_id == ministry_id

		assert hasattr(dept_entry, 'department_name')
		assert dept_entry.department_name is not None

		assert hasattr(dept_entry, 'observed_agency_count')
		assert dept_entry.observed_agency_count is not None

		assert hasattr(
			dept_entry, 'ministry_departments_url'
		)
		assert (
			dept_entry.ministry_departments_url is not None
		)
		assert (
			ministry_url
			in dept_entry.ministry_departments_url
		)

		params = _get_query_params(
			dept_entry.ministry_departments_url
		)
		assert 'department' in params
		assert params['department'] is not None

	# Check that the agency data entries have the
	# expected structure
	for _, agency_entry in agency_data.items():
		assert hasattr(agency_entry, 'agency_id')
		assert agency_entry.agency_id is not None

		assert hasattr(agency_entry, 'department_id')
		assert agency_entry.department_id is not None

		assert hasattr(agency_entry, 'ministry_id')
		assert agency_entry.ministry_id is not None
		assert agency_entry.ministry_id == ministry_id

		assert hasattr(agency_entry, 'agency_name')
		assert agency_entry.agency_name is not None

		assert hasattr(agency_entry, 'agency_name_hash')
		assert agency_entry.agency_name_hash is not None

		assert hasattr(
			agency_entry,
			'ministry_departments_agencies_url',
		)
		assert (
			agency_entry.ministry_departments_agencies_url
			is not None
		)
		assert (
			ministry_url
			in agency_entry.ministry_departments_agencies_url  # noqa: E501
		)

		params = _get_query_params(
			agency_entry.ministry_departments_agencies_url
		)
		assert 'department' in params
		assert 'agency' in params
		assert params['department'] is not None
		assert params['agency'] is not None


def test_ministry_service_processing_recipe():
	"""
	Test the ministry_service_processing_recipe with a
	sample ministry services page HTML.
	"""
	html = read_file(TEST_MINISTRY_SERVICES_PAGE_PATH)
	ministry_id = 'test_ministry_id'
	department_id = 'test_department_id'
	agency_id = 'test_agency_id'

	service_entries = ministry_service_processing_recipe(
		html=html,
		ministry_id=ministry_id,
		department_id=department_id,
		agency_id=agency_id,
	)

	# Basic assertions to check if the processing worked
	assert service_entries is not None
	assert isinstance(service_entries, dict)
	assert len(service_entries) > 0
	assert len(service_entries) == len(
		set(service_entries.keys())
	), 'Service IDs are not unique'

	# Check that the service entries have the
	# expected structure
	for _, service_entry in service_entries.items():
		assert hasattr(service_entry, 'service_id')
		assert service_entry.service_id is not None

		assert hasattr(service_entry, 'ministry_id')
		assert service_entry.ministry_id is not None
		assert service_entry.ministry_id == ministry_id

		assert hasattr(service_entry, 'department_id')
		assert service_entry.department_id is not None
		assert service_entry.department_id == department_id

		assert hasattr(service_entry, 'agency_id')
		assert service_entry.agency_id is not None
		assert service_entry.agency_id == agency_id

		assert hasattr(service_entry, 'service_name')
		assert service_entry.service_name is not None

		assert hasattr(service_entry, 'service_url')
		assert service_entry.service_url is not None
