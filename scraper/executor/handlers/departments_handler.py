"""
This module contains the handler for
executing scheduled tasks related to the
departments scope of the scraping process.
(Note: Given the nature of the data, the departments
handler is strictly comprised of processing the data scraped
from the ministries pages related to the departments.)
"""


class DepartmentsHandler:
	"""
	Handler for executing scheduled tasks
	related to the departments scope.
	"""

	def __init__(self) -> None:
		self.handler_name = 'DepartmentsHandler'

	# --- Processing methods ---
