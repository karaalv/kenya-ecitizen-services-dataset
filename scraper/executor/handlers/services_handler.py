"""
This module contains the handler for
executing scheduled tasks related to the
services scope of the scraping process.
(Note: Given the nature of the data, the services
handler is strictly comprised of processing the data scraped
from the ministries pages related to the services.)
"""


class ServicesHandler:
	"""
	Handler for executing scheduled tasks
	related to the services scope.
	"""

	def __init__(self) -> None:
		self.handler_name = 'ServicesHandler'

	# --- Processing methods ---
