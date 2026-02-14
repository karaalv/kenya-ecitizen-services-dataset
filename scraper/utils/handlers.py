"""
This module contains helper functions for handlers
within the executor component.
"""

import json
from pathlib import Path
from typing import Any, TypeVar

import pandas as pd
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def state_to_str(state: dict[str, T]) -> str:
	"""
	Helper function to convert a handler state
	dictionary to a JSON string for saving to a file.
	"""
	return json.dumps(
		{k: v.model_dump() for k, v in state.items()},
		ensure_ascii=False,
		indent=2,
	)


def str_to_state(
	state_str: str, model_cls: type[T]
) -> dict[str, T]:
	"""
	Helper function to convert a JSON string read from a
	file back into a handler state dictionary with values
	validated against the specified Pydantic model class.
	"""
	state_dict: dict[str, Any] = json.loads(state_str)

	return {
		k: model_cls.model_validate(v)
		for k, v in state_dict.items()
	}


def state_to_df(
	state: dict[str, T], model_cls: type[T]
) -> pd.DataFrame:
	"""
	Helper function to convert a handler state
	dictionary to a pandas DataFrame for analysis.
	"""
	rows = [v.model_dump() for v in state.values()]
	df = pd.DataFrame(rows)

	# Enforce model field order in the DataFrame
	# columns
	df = df[list(model_cls.model_fields.keys())]

	# Convert empty strings to NaN for better analysis
	df.replace('', pd.NA, inplace=True)
	return df


def save_df(
	df: pd.DataFrame,
	csv_path: str | Path,
	json_path: str | Path,
) -> None:
	"""
	Save DataFrame to CSV and JSON.

	- CSV written as UTF-8
	- JSON written as list of records
	- Index not saved
	"""

	csv_path = Path(csv_path)
	json_path = Path(json_path)

	# Ensure parent directories exist
	csv_path.parent.mkdir(
		parents=True,
		exist_ok=True,
	)
	json_path.parent.mkdir(
		parents=True,
		exist_ok=True,
	)

	# Save CSV
	df.to_csv(
		csv_path,
		index=False,
		encoding='utf-8',
	)

	# Save JSON (records = list of dicts)
	df.to_json(
		json_path,
		orient='records',
		indent=2,
		force_ascii=False,
	)
