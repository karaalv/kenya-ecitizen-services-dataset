"""
This module contains a live integration test for
handlers that execute scraping tasks, using the actual
urls of the Kenya eCitizen portal. Note this test
can only be run as an integration test with the relevant
environment variable set.
Run with:
    RUN_SCRAPE_TESTS=1 pytest -m integration
"""

from os import getenv

import pytest

from scraper.executor.handlers.agencies_handler import (
	AgenciesHandler,
)
from scraper.executor.handlers.faq_handler import FAQHandler
from scraper.executor.handlers.ministries_handler import (
	MinistriesHandler,
)
from scraper.schemas.ministries import MinistryEntry
from scraper.schemas.scheduler_task import (
	EmptyTask,
	ScrapingPhase,
	TaskOperation,
)
from scraper.scraping.scrape_client import ScrapeClient
from scraper.static.paths import Paths
from scraper.utils.files import does_file_exist
from tests.utils.files import delete_file

# --- Test Constants ---

TEST_MINISTRY_PAGE_URL = 'https://accounts.ecitizen.go.ke/en/ministries/the-state-law-office'
TEST_SERVICE_PAGE_URL = 'https://accounts.ecitizen.go.ke/en/ministries/the-state-law-office?department=registrar-generals-department&agency=registrar-of-marriages'


@pytest.mark.integration
async def test_scrape_handlers():
	# Check if integration tests should be run
	if getenv('RUN_SCRAPE_TESTS') != '1':
		pytest.skip('Integration disabled')

	scrape_client = ScrapeClient()
	await scrape_client.init_browser()

	ministries_handler = MinistriesHandler()
	agencies_handler = AgenciesHandler()
	faq_handler = FAQHandler()

	task_log = 'test_scrape_handlers'
	task = EmptyTask(
		scope=ScrapingPhase.FINALISATION,
		operation=TaskOperation.FINALISATION_CHECKS,
	)

	faq_html = await faq_handler.scrape_faq_page(
		task_log=task_log,
		scrape_client=scrape_client,
	)

	# Test faq page
	assert faq_html.strip() != '', (
		'FAQ page content is empty'
	)
	assert does_file_exist(faq_handler.file), (
		'FAQ page content was not saved to file'
	)
	delete_file(faq_handler.file)

	# Test agencies list page
	agencies_list_html = (
		await agencies_handler.scrape_agencies_list_page(
			task_log=task_log,
			scrape_client=scrape_client,
		)
	)
	assert agencies_list_html.strip() != '', (
		'Agencies list page content is empty'
	)
	assert does_file_exist(agencies_handler.file), (
		'Agencies list page content was not saved to file'
	)
	delete_file(agencies_handler.file)

	# Test ministries list page
	ministries_list_html = await ministries_handler.scrape_ministries_list_page(  # noqa: E501
		task_log=task_log,
		scrape_client=scrape_client,
	)
	assert ministries_list_html.strip() != '', (
		'Ministries list page content is empty'
	)
	assert does_file_exist(ministries_handler.file), (
		'Ministries list page content was not saved to file'
	)
	delete_file(ministries_handler.file)

	# Test individual ministry page

	# Add test id and url in handler state
	test_ministry_id = 'the-state-law-office'
	ministries_handler.ministry_entries[
		test_ministry_id
	] = MinistryEntry(
		ministry_id=test_ministry_id,
		ministry_url=TEST_MINISTRY_PAGE_URL,
		ministry_name='The State Law Office',
		ministry_description='',
		reported_agency_count=None,
		reported_service_count=None,
		observed_agency_count=None,
		observed_service_count=None,
		observed_department_count=None,
	)

	ministry_page_html = (
		await ministries_handler.scrape_ministry_page(
			ministry_id=test_ministry_id,
			task_log=task_log,
			task=task,
			scrape_client=scrape_client,
		)
	)

	assert ministry_page_html.overview.strip() != '', (
		'Ministry page content is empty'
	)
	assert (
		ministry_page_html.departments_and_agencies.strip()
		!= ''
	), (
		'Ministry departments and agencies page '
		'content is empty'
	)
	ministry_overview_file = (
		Paths.RAW_DATA_DIR
		/ 'ministries'
		/ test_ministry_id
		/ 'overview.html'
	)

	ministry_departments_agencies_file = (
		Paths.RAW_DATA_DIR
		/ 'ministries'
		/ test_ministry_id
		/ 'departments_agencies.html'
	)

	assert does_file_exist(ministry_overview_file), (
		'Ministry overview page content '
		'was not saved to file'
	)
	assert does_file_exist(
		ministry_departments_agencies_file
	), (
		'Ministry departments and agencies page content '
		'was not saved to file'
	)
	delete_file(ministry_overview_file)
	delete_file(ministry_departments_agencies_file)

	# Test ministry service page
	test_department_id = 'registrar-generals-department'
	test_agency_id = 'registrar-of-marriages'
	service_page_html = await ministries_handler.scrape_ministry_services_page(  # noqa: E501
		ministry_id=test_ministry_id,
		department_id=test_department_id,
		agency_id=test_agency_id,
		ministry_departments_agencies_url=TEST_SERVICE_PAGE_URL,
		task_log=task_log,
		scrape_client=scrape_client,
	)

	assert service_page_html.strip() != '', (
		'Ministry service page content is empty'
	)
	services_file = (
		Paths.RAW_DATA_DIR
		/ 'ministries'
		/ test_ministry_id
		/ test_department_id
		/ test_agency_id
		/ 'services.html'
	)
	assert does_file_exist(services_file), (
		'Ministry service page content '
		'was not saved to file'
	)
	delete_file(services_file)

	# close the scrape client browser after tests
	await scrape_client.close_browser()
