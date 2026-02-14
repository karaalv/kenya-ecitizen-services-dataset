"""
This module contains functions for normalising
data during processing.
"""

import re
import unicodedata
from urllib.parse import (
	quote,
	unquote,
	urljoin,
	urlparse,
	urlunparse,
)

_WS_REGEX = re.compile(r'\s+', re.UNICODE)
_ALLOWED_REGEX = re.compile(r'[^a-z0-9]')
_CONTROL_REGEX = re.compile(
	r'[\x00-\x1F\x7F]',
)

BASE_URL = 'https://ecitizen.go.ke/'


def normalise_ws(text: str) -> str:
	"""
	Collapse whitespace to single spaces and trim.
	"""
	return _WS_REGEX.sub(' ', text).strip()


def normalise_text(text: str) -> str:
	"""
	Normalise scraped text safely.

	- Ensures valid Unicode
	- Removes control characters
	- Normalises Unicode (NFC)
	- Collapses whitespace
	"""

	# Ensure it's a str
	if not isinstance(text, str):
		text = str(text)

	# Unicode normalisation (safe, preserves accents)
	text = unicodedata.normalize('NFC', text)

	# Remove control characters
	text = _CONTROL_REGEX.sub('', text)

	# Collapse whitespace
	text = normalise_ws(text)

	return text


def normalise_text_hashing(text: str) -> str:
	"""
	Deterministic normalisation for ID hashing:
	- Unicode NFKD
	- Casefold for robust comparisons
	- Remove all non-alphanumeric characters
	"""
	norm = normalise_ws(unicodedata.normalize('NFKD', text))
	norm = norm.casefold()
	return _ALLOWED_REGEX.sub('', norm)


def parse_int(text: str) -> int | None:
	"""
	Parse a string representing an integer.
	Returns None if invalid.
	"""
	if not isinstance(text, str):
		return None

	clean = text.strip()

	if not clean:
		return None

	if not clean.isdigit():
		return None

	return int(clean)


def normalise_url(
	url: str,
	base_url: str = BASE_URL,
) -> str:
	"""
	Resolve relative URLs and normalise them.

	- Only resolves against base_url if URL has no scheme
	- Lowercases scheme + host
	- Removes fragment
	- Percent-encodes safely (UTF-8)
	- Avoids double-encoding via quote(unquote(...))
	"""

	url = url.strip()

	parsed = urlparse(url)

	# Resolve only if relative or scheme-less
	if not parsed.scheme:
		url = urljoin(base_url, url)
		parsed = urlparse(url)

	scheme = parsed.scheme.lower()
	netloc = parsed.netloc.lower()

	path = quote(unquote(parsed.path), safe='/')
	query = quote(unquote(parsed.query), safe='=&')

	return urlunparse(
		(
			scheme,
			netloc,
			path,
			parsed.params,
			query,
			'',  # remove fragment
		)
	)
