"""
This module is used to test the normalisation
functions used in the application.
"""

from scraper.utils.normalise import BASE_URL, normalise_url

# --- Test cases ---


def test_normalise_url():
	test_cases = [
		# --- Absolute URLs (should not join base) ---
		# Basic http
		('http://example.com', 'http://example.com'),
		# Basic https
		('https://example.com', 'https://example.com'),
		# Uppercase scheme + host
		('HTTP://EXAMPLE.COM', 'http://example.com'),
		# With path
		(
			'http://example.com/path/to/resource',
			'http://example.com/path/to/resource',
		),
		# With query
		(
			'http://example.com?param=value',
			'http://example.com?param=value',
		),
		# Fragment should be removed
		(
			'http://example.com#section',
			'http://example.com',
		),
		# With port
		(
			'http://example.com:8080',
			'http://example.com:8080',
		),
		# --- Relative URLs (should join BASE_URL) ---
		# Leading slash
		('/en/ministries', f'{BASE_URL}en/ministries'),
		# No leading slash
		('en/ministries', f'{BASE_URL}en/ministries'),
		# With query
		(
			'/en/ministries?department=finance',
			f'{BASE_URL}en/ministries?department=finance',
		),
		# Fragment removed after join
		('/en/ministries#top', f'{BASE_URL}en/ministries'),
		# UTF-8 encoding
		('/münchen', f'{BASE_URL}m%C3%BCnchen'),
	]

	for input_url, expected in test_cases:
		assert normalise_url(input_url) == expected
