"""
This module contains the scraping recipe for
a Ministry Page.
"""

from playwright.async_api import Page
from pydantic import BaseModel

from scraper.exceptions.scraper import RetryableScrapeError


class MinistryPageData(BaseModel):
	overview: str
	departments_and_agencies: str


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
		overview=overview_html,
		departments_and_agencies=agencies_html,
	)
