"""
This module contains functions for normalising
data during processing.
"""

import re
import unicodedata

_WS_REGEX = re.compile(r'\s+', re.UNICODE)
_ALLOWED_REGEX = re.compile(r'[^a-z0-9]')


def normalise_ws(text: str) -> str:
	"""
	Collapse whitespace to single spaces and trim.
	"""
	return _WS_REGEX.sub(' ', text).strip()


def normalise_text(text: str) -> str:
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
