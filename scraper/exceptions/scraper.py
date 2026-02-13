class ScrapingError(Exception):
	"""Base class for scraping-related errors."""

	def __init__(
		self,
		message: str,
		*,
		task_log: str | None = None,
		page_url: str | None = None,
	) -> None:
		super().__init__(message)
		self.task_log = task_log
		self.page_url = page_url

	def __str__(self) -> str:
		base = super().__str__()
		parts: list[str] = [base]

		if self.page_url is not None:
			parts.append(f'Page URL: {self.page_url}')

		if self.task_log is not None:
			parts.append(f'Task Log:\n{self.task_log}')

		return '\n'.join(parts)

	def __repr__(self) -> str:
		return (
			f'{self.__class__.__name__}('
			f'message={super().__str__()!r}, '
			f'page_url={self.page_url!r}, '
			f'task_log={self.task_log!r})'
		)


class ScrapeClientError(ScrapingError):
	"""Browser/context lifecycle failure."""


class RetryableScrapeError(ScrapingError):
	"""A scrape attempt failed but may succeed on retry."""


class FatalScrapeError(ScrapingError):
	"""Scrape failed permanently or retries exhausted."""
