"""
This module contains the scraping recipe for the
services on a Ministry page.
"""

from playwright.async_api import Page

from scraper.exceptions.scraper import RetryableScrapeError


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
