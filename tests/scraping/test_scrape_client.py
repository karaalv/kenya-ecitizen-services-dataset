import time

from playwright.async_api import Page

from scraper.exceptions.scraper import (
	RetryableScrapeError,
)
from scraper.scraping.rate_limiter import RatePolicy
from scraper.scraping.scrape_client import ScrapeClient

# --- Test constants ---


async def google_search_recipe(url: str, page: Page) -> str:
	"""
	A simple scraping recipe that performs a
	Google search and returns the page title.
	"""
	print(f'Navigating to {url}')
	title = await page.title()
	print(f'Page title: {title}')
	if 'Google' not in title:
		raise RetryableScrapeError(
			'Unexpected page title, may '
			'not have loaded correctly',
			page_url=url,
		)
	return title


async def test_scrape_client():
	"""
	Test the ScrapeClient with a simple
	Google search recipe, assert request
	is longer than minimum delay
	"""
	client = ScrapeClient()
	await client.init_browser()

	url = 'https://www.google.com'
	title = await client.run(
		url=url,
		task_log='Testing Google search recipe',
		recipe=google_search_recipe,
	)

	assert 'Google' in title
	await client.close_browser()


async def test_scrape_client_rate_limiting():
	"""
	Test that the ScrapeClient respects rate limits
	by making multiple requests and asserting delays.
	"""
	client = ScrapeClient()
	await client.init_browser()

	url = 'https://www.google.com'
	task_log = (
		'Testing rate limiting with multiple requests'
	)

	for i in range(3):
		start_time = time.monotonic()
		title = await client.run(
			url=url,
			task_log=f'{task_log} #{i + 1}',
			recipe=google_search_recipe,
		)
		elapsed = time.monotonic() - start_time

		assert 'Google' in title
		if i > 0:
			assert elapsed >= RatePolicy.min_delay_s

	await client.close_browser()
