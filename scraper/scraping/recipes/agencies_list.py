"""
This module contains the scraping recipe for the
Agencies List page.
"""

from playwright.async_api import Page

from scraper.exceptions.scraper import RetryableScrapeError


async def agencies_list_page_recipe(
	url: str, page: Page
) -> str:
	"""
	Recipe for scraping the Agencies List page content.
	"""
	# Wait for content to load using anchor
	anchor = 'https://adc.go.ke/shop'
	await page.wait_for_selector(
		f'div.grid a[href="{anchor}"]'
	)

	agencies_list = page.locator('div.grid').first
	grid = await agencies_list.inner_html()

	if not grid:
		raise RetryableScrapeError(
			'Failed to extract Agencies List content',
			page_url=url,
		)
	return grid
