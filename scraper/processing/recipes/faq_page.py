"""
This module contains the processing recipe for
turning the raw HTML content of the FAQ page into
structured FAQEntry data.
"""

import re

from bs4 import BeautifulSoup

from scraper.exceptions.executor import (
	ExecutorProcessingFailure,
)
from scraper.schemas.faq import FAQEntry
from scraper.schemas.scheduler_task import SchedulerTask
from scraper.utils.hashing import stable_id
from scraper.utils.normalise import normalise_text


def faq_page_processing_recipe(
	html: str, task_log: str, task: SchedulerTask
) -> dict[str, FAQEntry]:
	"""
	Recipe to process the raw HTML content of
	the FAQ page.
	"""
	soup = BeautifulSoup(html, 'lxml')
	faq_items = soup.find_all('li', id=re.compile(r'^faq_'))
	faq_entries: dict[str, FAQEntry] = {}

	for item in faq_items:
		# Use button to anchor search
		btn = item.find('button')
		if not btn:
			continue

		question_raw = btn.get_text(' ', strip=True)
		question = normalise_text(question_raw)

		# Answer is usually the next sibling div
		answer_div = btn.find_next_sibling('div')

		# If the DOM is slightly different, fall back to
		# searching inside the li for the first div
		# after button
		if not answer_div:
			divs = item.find_all('div')
			answer_div = divs[0] if divs else None

		answer_raw = ''
		if answer_div:
			answer_raw = answer_div.get_text(
				' ', strip=True
			)
		answer = normalise_text(answer_raw)

		faq_id = stable_id([question, answer])

		if faq_id in faq_entries:
			continue

		faq_entries[faq_id] = FAQEntry(
			faq_id=faq_id,
			question=question,
			answer=answer,
		)

	if not faq_entries:
		raise ExecutorProcessingFailure(
			message='No FAQ entries found during '
			f'processing. Found {len(faq_items)}'
			' potential items but failed to extract '
			'valid question-answer pairs.',
			task_log=task_log,
			task=task,
		)

	return faq_entries
