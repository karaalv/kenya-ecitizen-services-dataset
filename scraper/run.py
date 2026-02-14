"""
This module acts as the entry point for running
the scraper. It initializes necessary components,
schedules tasks, and executes handlers to perform
the scraping and insights generation processes.
"""

import logging

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from scraper.executor.executor import Executor
from scraper.scheduler.scheduler import Scheduler
from scraper.static.paths import Paths
from scraper.utils.logging import (
	format_exception,
	get_task_log,
	setup_logging,
)

red = '\033[91m'
reset = '\033[0m'

logger = logging.getLogger(__name__)


async def main():
	# Configure logging
	setup_logging(
		log_file=Paths.LOGS_DIR / 'scraper.log',
		level=logging.INFO,
	)

	# Initialize scheduler and executor
	scheduler = Scheduler()
	executor = await Executor.create()

	progress_bar = tqdm(
		total=None,
		unit='task',
		dynamic_ncols=True,
	)

	# Rum tasks in loop
	try:
		with logging_redirect_tqdm():
			while True:
				next_task = scheduler.next_task()
				if next_task is None:
					break

				# Log progress
				progress_bar.set_description(
					get_task_log(next_task)
				)

				task_result = await executor.execute_task(
					next_task
				)
				scheduler.apply_task_result(task_result)
				progress_bar.update(1)
	except Exception as e:
		print(f'{red}--- Error during execution ---{reset}')
		print(format_exception(e))
		print(f'{red}-------- End of error --------{reset}')
	finally:
		progress_bar.close()
		await executor.close()
