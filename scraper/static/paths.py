from pathlib import Path


class Paths:
	"""
	Class to manage file paths for the scraper.
	This class contains static references to
	various directories and files used in the scraping
	process.
	"""

	PROJECT_ROOT = Path(__file__).resolve().parents[3]

	# Data directories
	DATA_DIR = PROJECT_ROOT / 'data'
	RAW_DATA_DIR = DATA_DIR / 'raw'
	PROCESSED_DATA_DIR = DATA_DIR / 'processed'

	# Insights directory
	INSIGHTS_DIR = DATA_DIR / 'insights'

	# Temporary directory
	TEMP_DIR = DATA_DIR / 'tmp'
	LOGS_DIR = TEMP_DIR / 'logs'
