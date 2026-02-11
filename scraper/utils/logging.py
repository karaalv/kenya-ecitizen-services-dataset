"""
This module contains utility functions
for logging within the scraper, primarily
around managing the `logger` instance used
across the codebase for consistent logging
practices.
"""

import logging
from pathlib import Path

from scraper.schemas.scheduler_task import SchedulerTask


class SafeFormatter(logging.Formatter):
	"""
	Log formatter that ensures optional fields
	are always present on the LogRecord.
	"""

	def format(self, record: logging.LogRecord) -> str:
		if not hasattr(record, 'task'):
			record.task = '-'
		return super().format(record)


# Use once in the main entry point of the
# application to configure logging
def setup_logging(
	log_file: Path,
	*,
	level: int = logging.INFO,
) -> None:
	"""
	Configure global logging.

	- Writes logs to file and stdout
	- Ensures log directory exists
	- Adds safe handling for custom fields
	"""
	log_file.parent.mkdir(
		parents=True,
		exist_ok=True,
	)

	formatter = SafeFormatter(
		'%(asctime)s | %(levelname)s | %(name)s | '
		'%(task)s | %(message)s'
	)

	file_handler = logging.FileHandler(
		log_file,
		encoding='utf-8',
	)
	file_handler.setFormatter(formatter)

	stream_handler = logging.StreamHandler()
	stream_handler.setFormatter(formatter)

	root = logging.getLogger()
	root.setLevel(level)

	# Avoid duplicate handlers if setup is called twice
	root.handlers.clear()

	root.addHandler(file_handler)
	root.addHandler(stream_handler)


def get_task_log(task: SchedulerTask) -> str:
	"""
	Helper function to create a consistent log string
	for a given task.
	"""
	return f'{task.scope}:{task.operation}'
