"""
This module contains functions for hashing
data during processing in order to create
stable identifiers for records.
"""

import hashlib
from typing import Final

from scraper.utils.normalise import normalise_text_hashing

_HASH_LENGTH: Final[int] = 12


def sha256_hash(text: str) -> str:
	"""
	Generates a SHA-256 hash of the input text and
	returns the first 12 characters as a stable identifier.
	"""
	normalised = normalise_text_hashing(text)
	if not normalised:
		return ''
	hash_object = hashlib.sha256(normalised.encode('utf-8'))
	return hash_object.hexdigest()[:_HASH_LENGTH]


def stable_id(
	inputs: list[str],
) -> str:
	"""
	Generates a stable identifier by concatenating the
	input strings with delimiters, normalising the result
	and hashing it using the sha256_hash function.
	"""
	inputs_normalised = map(normalise_text_hashing, inputs)
	return sha256_hash('-'.join(inputs_normalised))
