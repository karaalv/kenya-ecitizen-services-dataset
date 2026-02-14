"""
Scraping client module, this class is used to manage
playwright browser interactions for scraping tasks.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from playwright.async_api import (
	Browser,
	BrowserContext,
	Page,
	Playwright,
	async_playwright,
)

from scraper.exceptions.scraper import (
	FatalScrapeError,
	RetryableScrapeError,
	ScrapeClientError,
)
from scraper.scraping.rate_limiter import (
	RateLimiter,
	RatePolicy,
	RetryPolicy,
)

# Scraping recipe type, a callable that returns
# an awaitable result of type T.

T = TypeVar('T')
ScrapingRecipe = Callable[[str, Page], Awaitable[T]]

logger = logging.getLogger(__name__)


class ScrapeClient:
	def __init__(self) -> None:
		self._rate_limiter = RateLimiter(
			rate=RatePolicy(),
			retry=RetryPolicy(),
		)

		self._playwright: Playwright | None = None
		self._browser: Browser | None = None
		self._context: BrowserContext | None = None

		self._user_agent = (
			'kenya-ecitizen-scraper/1.0 '
			'(public research dataset; '
			'contact: alvinnjiiri@gmail.com)'
		)

		self._page_timeout_ms = 30_000
		self._max_retries = 5

	# --- Browser management --- #

	async def init_browser(self) -> None:
		if self._context is not None:
			return
		try:
			self._playwright = (
				await async_playwright().start()
			)
			self._browser = (
				await self._playwright.chromium.launch(
					headless=True
				)
			)
			self._context = await self._browser.new_context(
				user_agent=self._user_agent,
			)
		except Exception as e:
			await self._cleanup_partial_init()
			raise ScrapeClientError(
				'Failed to initialise browser.',
				task_log=None,
				page_url=None,
			) from e

	async def close_browser(self) -> None:
		await self._safe_close_context()
		await self._safe_close_browser()
		await self._safe_stop_playwright()

	async def _cleanup_partial_init(self) -> None:
		await self._safe_close_context()
		await self._safe_close_browser()
		await self._safe_stop_playwright()

	async def _safe_close_context(self) -> None:
		ctx = self._context
		self._context = None
		if ctx is None:
			return
		try:
			await ctx.close()
		except Exception:
			logger.exception('Context close failed')

	async def _safe_close_browser(self) -> None:
		br = self._browser
		self._browser = None
		if br is None:
			return
		try:
			await br.close()
		except Exception:
			logger.exception('Browser close failed')

	async def _safe_stop_playwright(self) -> None:
		pw = self._playwright
		self._playwright = None
		if pw is None:
			return
		try:
			await pw.stop()
		except Exception:
			logger.exception('Playwright stop failed')

	# --- Scraping execution --- #

	async def run(
		self,
		url: str,
		task_log: str,
		recipe: ScrapingRecipe[T],
	) -> T:
		ctx = self._context
		if ctx is None:
			raise ScrapeClientError(
				'Context not initialised. '
				'Call init_browser() first.',
				task_log=task_log,
				page_url=url,
			)

		logger.info(
			f'[{task_log}] Starting scrape for {url!r}',
		)

		for attempt in range(1, self._max_retries + 1):
			await self._rate_limiter.wait_turn()

			page = await ctx.new_page()
			try:
				page.set_default_timeout(
					self._page_timeout_ms
				)

				await self._goto_or_retry(
					page=page,
					url=url,
					task_log=task_log,
					attempt=attempt,
				)

				return await self._recipe_or_retry(
					page=page,
					recipe=recipe,
					url=url,
					task_log=task_log,
					attempt=attempt,
				)

			except RetryableScrapeError as e:
				logger.warning(
					f'[SCRAPE_CLIENT] Attempt {attempt} '
					'failed with '
					f'[{task_log}] retryable: {e!r}'
				)
				self._rate_limiter.enter_backoff()
				continue

			except FatalScrapeError as e:
				logger.error(
					f'[SCRAPE_CLIENT] Attempt {attempt} '
					'failed with '
					f'[{task_log}] fatal: {e!r}'
				)
				raise

			finally:
				await self._safe_close_page(
					page=page,
					task_log=task_log,
					url=url,
				)

		raise FatalScrapeError(
			f'All {self._max_retries} attempts exhausted.',
			task_log=task_log,
			page_url=url,
		)

	async def _goto_or_retry(
		self,
		*,
		page: Page,
		url: str,
		task_log: str,
		attempt: int,
	) -> None:
		try:
			await page.goto(
				url,
				wait_until='domcontentloaded',
			)
		except Exception as e:
			raise RetryableScrapeError(
				f'Navigation failed on attempt {attempt}.',
				task_log=task_log,
				page_url=url,
			) from e

	async def _recipe_or_retry(
		self,
		*,
		page: Page,
		recipe: ScrapingRecipe[T],
		url: str,
		task_log: str,
		attempt: int,
	) -> T:
		try:
			return await recipe(url, page)
		except (RetryableScrapeError, FatalScrapeError):
			raise
		except Exception as e:
			raise RetryableScrapeError(
				f'Recipe failed on attempt {attempt}.',
				task_log=task_log,
				page_url=url,
			) from e

	async def _safe_close_page(
		self,
		*,
		page: Page,
		task_log: str,
		url: str,
	) -> None:
		try:
			await page.close()
		except Exception:
			logger.exception(
				f'[{task_log}] page close '
				f'failed for {url!r}'
			)
