"""
This module contains the scraping recipe for the
Ministries List page.
"""

from playwright.async_api import Page

from scraper.exceptions.scraper import RetryableScrapeError


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
