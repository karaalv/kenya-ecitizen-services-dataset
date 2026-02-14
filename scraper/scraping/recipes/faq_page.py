"""
This module contains the scraping recipe for the
FAQ page.
"""

from playwright.async_api import Page

from scraper.exceptions.scraper import RetryableScrapeError


async def faq_page_scrape_recipe(
	url: str, page: Page
) -> str:
	"""
	Recipe for scraping the FAQ page content.
	"""
	# Wait for content to load
	await page.wait_for_selector('div#FAQs ul li')

	faq = page.locator('div#FAQs').first
	html = await faq.inner_html()

	if not html:
		raise RetryableScrapeError(
			'Failed to extract FAQ content',
			page_url=url,
		)
	return html
