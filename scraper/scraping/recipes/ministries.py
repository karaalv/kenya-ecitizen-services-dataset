"""
This module contains all scraping recipes
related to the Ministries scope of the
scraping process.
"""

from playwright.async_api import Page

from scraper.exceptions.scraper import RetryableScrapeError
from scraper.schemas.ministries import MinistryPageData


async def ministries_list_page_recipe(
	url: str, page: Page
) -> str:
	"""
	Recipe for scraping the Ministries List page content.
	"""
	# Wait for content to load
	await page.wait_for_selector(
		"ul a[href^='/en/ministries/']"
	)

	ministries_list = page.locator('ul').first
	list_html = await ministries_list.inner_html()

	if not list_html:
		raise RetryableScrapeError(
			'Failed to extract Ministries List content',
			page_url=url,
		)
	return list_html


async def ministry_page_recipe(
	url: str, page: Page
) -> MinistryPageData:
	"""
	Recipe for scraping the Ministry page content.
	"""
	# Wait for content to load
	await page.wait_for_selector("h2:has-text('Overview')")

	# Overview section
	overview = page.locator('div.lg\\:grid').first
	overview_html = await overview.inner_html()

	# Departments and Agencies section
	agencies_lists = page.locator("ul[role='listbox']")
	agencies_html = await agencies_lists.evaluate_all(
		'els => els.map(el => el.outerHTML).join("\\n")'
	)

	if not overview_html or not agencies_html:
		raise RetryableScrapeError(
			'Failed to extract Ministry page content',
			page_url=url,
		)
	return MinistryPageData(
		ministry_id='',  # Placeholder, to be filled
		overview=overview_html,
		departments_and_agencies=agencies_html,
	)


async def ministry_services_page_recipe(
	url: str, page: Page
) -> str:
	"""
	Recipe for scraping the services on a Ministry
	page content.
	"""
	# Wait for content to load
	await page.wait_for_selector('div.space-y-3 a')

	services = page.locator('div.space-y-3').first
	services_html = await services.inner_html()

	if not services_html:
		raise RetryableScrapeError(
			'Failed to extract Ministry services content',
			page_url=url,
		)
	return services_html
