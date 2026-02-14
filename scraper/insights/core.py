"""
This module contains the core components of
the insights generation process, which analyses
the result of a handler to produce an insights
Markdown file.
"""

import json
from typing import TypeVar

import pandas as pd
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def render_insights_report(
	df: pd.DataFrame,
	state: dict[str, T],
	ignore_cols: list[str] | None = None,
	*,
	title: str = 'Insights Report',
	id_col: str = 'id',
	max_ids_per_issue: int = 100,
	max_models_dump: int = 100,
) -> str:
	"""
	Render a markdown insights report for a dataframe.

	Args:
		df:
			The dataframe to analyse.
		state:
			Mapping from id -> Pydantic model (or None).
			Used to dump detailed records for missing data.
		ignore_cols:
			Columns to ignore for missingness analysis.
		title:
			Top-level title in markdown.
		id_col:
			Column name containing record IDs.
		max_ids_per_issue:
			Cap number of IDs listed per issue.
		max_models_dump:
			Cap number of model dumps included in the
			report.

	Returns:
		A single markdown string.
	"""
	sections: list[str] = [f'# {title}\n']

	sections.append(
		render_overview_section(
			df=df,
			ignore_cols=ignore_cols,
			id_col=id_col,
		)
	)

	sections.append(
		render_duplicates_section(
			df=df,
			id_col=id_col,
			max_ids=max_ids_per_issue,
		)
	)

	sections.append(
		render_missing_data_section(
			df=df,
			state=state,
			ignore_cols=ignore_cols,
			id_col=id_col,
			max_ids=max_ids_per_issue,
			max_models_dump=max_models_dump,
		)
	)

	# Clean join, ensure spacing
	return (
		'\n'.join(s.strip('\n') for s in sections).strip()
		+ '\n'
	)


def render_overview_section(
	df: pd.DataFrame,
	ignore_cols: list[str] | None = None,
	*,
	id_col: str = 'id',
) -> str:
	ignore = set(ignore_cols or [])

	total_rows = int(len(df))
	total_cols = int(len(df.columns))
	has_id = id_col in df.columns

	if has_id:
		id_series = df[id_col].astype(str)
		unique_ids = int(id_series.nunique(dropna=True))
		dup_rows = int(
			id_series.duplicated(keep=False).sum()
		)
	else:
		unique_ids = 0
		dup_rows = 0

	# Missingness over selected columns
	cols = [c for c in df.columns if c not in ignore]
	if len(cols) == 0:
		missing_cells = 0
		total_cells = 0
		missing_pct = 0.0
	else:
		sub = df[cols]
		missing_cells = int(sub.isna().sum().sum())
		total_cells = int(sub.shape[0] * sub.shape[1])
		missing_pct = (
			(missing_cells / total_cells * 100.0)
			if total_cells
			else 0.0
		)

	lines: list[str] = []
	lines.append('## Overview\n')
	lines.append(f'- **Rows:** {total_rows}')
	lines.append(f'- **Columns:** {total_cols}')
	if has_id:
		lines.append(
			f'- **Unique `{id_col}`:** {unique_ids}'
		)
		lines.append(
			f'- **Duplicate `{id_col}` rows:** {dup_rows}'
		)
	else:
		lines.append(
			f'- **ID column `{id_col}`:** not present'
		)

	lines.append(
		'- **Missing cells '
		f'(excluding ignored columns):** {missing_cells}'
		f' / {total_cells} ({missing_pct:.2f}%)'
	)

	if ignore:
		ignore_list = ', '.join(
			f'`{c}`' for c in sorted(ignore)
		)
		lines.append(
			f'- **Ignored columns:** {ignore_list}'
		)
	else:
		lines.append('- **Ignored columns:** none')

	return '\n'.join(lines) + '\n'


def render_duplicates_section(
	df: pd.DataFrame,
	*,
	id_col: str = 'id',
	max_ids: int = 100,
) -> str:
	lines: list[str] = []
	lines.append('## Duplicates\n')

	if id_col not in df.columns:
		lines.append(
			f'- `{id_col}` not present, '
			f'cannot analyse duplicates.\n'
		)
		return '\n'.join(lines)

	id_series = df[id_col].astype(str)

	dup_mask = id_series.duplicated(keep=False)
	dup_df = df.loc[dup_mask, [id_col]].copy()

	if dup_df.empty:
		lines.append('- No duplicates found.\n')
		return '\n'.join(lines)

	counts = (
		dup_df[id_col]
		.value_counts(dropna=False)
		.sort_values(ascending=False)
	)

	total_dup_ids = int(counts.shape[0])
	total_dup_rows = int(dup_df.shape[0])

	lines.append(f'- **Duplicate IDs:** {total_dup_ids}')
	lines.append(f'- **Rows involved:** {total_dup_rows}\n')

	lines.append('| ID | Count |')
	lines.append('|---|---:|')

	shown = 0
	for _id, cnt in counts.items():
		if shown >= max_ids:
			break
		lines.append(f'| `{_id}` | {int(cnt)} |')
		shown += 1

	if total_dup_ids > max_ids:
		lines.append(
			f'\n_Only showing first '
			f'{max_ids} duplicate IDs._'
		)

	return '\n'.join(lines) + '\n'


def render_missing_data_section(
	df: pd.DataFrame,
	state: dict[str, T],
	ignore_cols: list[str] | None = None,
	*,
	id_col: str = 'id',
	max_ids: int = 100,
	max_models_dump: int = 50,
) -> str:
	lines: list[str] = []
	lines.append('## Missing Data\n')

	ignore = set(ignore_cols or [])
	cols = [c for c in df.columns if c not in ignore]

	if len(cols) == 0:
		lines.append(
			'- All columns are ignored, '
			'skipping missingness.\n'
		)
		return '\n'.join(lines)

	if id_col not in df.columns:
		lines.append(
			f'- `{id_col}` not present, cannot list '
			f'missing records by ID.\n'
		)
		return '\n'.join(lines)

	# Missingness by column
	missing_counts = (
		df[cols].isna().sum().sort_values(ascending=False)
	)
	total_rows = int(len(df))

	lines.append('### Missingness by Column\n')
	lines.append('| Column | Missing | % Rows |')
	lines.append('|---|---:|---:|')

	for col, cnt in missing_counts.items():
		cnt_int = int(cnt)
		pct = (
			(cnt_int / total_rows * 100.0)
			if total_rows
			else 0.0
		)
		lines.append(
			f'| `{col}` | {cnt_int} | {pct:.2f}% |'
		)

	# Detailed records per column
	lines.append('\n### Missing Records Detail\n')

	model_dumps_used = 0

	for col, cnt in missing_counts.items():
		cnt_int = int(cnt)
		if cnt_int == 0:
			continue

		lines.append(f'\n#### `{col}`\n')

		missing_rows = df[df[col].isna()]
		ids = missing_rows[id_col].astype(str).tolist()

		lines.append(f'- Missing rows: {cnt_int}')
		lines.append(
			f'- Affected IDs: '
			f'{min(len(ids), max_ids)} shown'
		)

		shown_ids = ids[:max_ids]
		if shown_ids:
			lines.append('')
			for _id in shown_ids:
				lines.append(f'- `{_id}`')

		if len(ids) > max_ids:
			lines.append(
				f'\n_Only showing first {max_ids} IDs._'
			)

		# Join with state dict to dump records
		if not state:
			lines.append(
				'\n_No state dict provided, '
				'skipping dumps._'
			)
			continue

		lines.append(
			'\n**Record dumps (from handler state):**\n'
		)

		dumped_here = 0
		for _id in shown_ids:
			if model_dumps_used >= max_models_dump:
				break

			model = state.get(_id)
			if model is None:
				lines.append(
					f'- `{_id}`: _not found in state_'
				)
				continue

			dump = _safe_model_dump_json(model)
			lines.append(f'- `{_id}`')
			lines.append('```json')
			lines.append(dump)
			lines.append('```')

			model_dumps_used += 1
			dumped_here += 1

		if (
			dumped_here == 0
			and model_dumps_used >= max_models_dump
		):
			lines.append(
				f'_Model dump cap reached '
				f'({max_models_dump})._'
			)

	if model_dumps_used >= max_models_dump:
		lines.append(
			f'\n_Model dump cap reached '
			f'({max_models_dump}) across report._'
		)

	return '\n'.join(lines) + '\n'


def _safe_model_dump_json(model: BaseModel) -> str:
	try:
		# Pydantic v2
		return model.model_dump_json(indent=2)
	except Exception:
		try:
			# Pydantic v1 fallback
			data = model.dict()
			return json.dumps(data, indent=2, default=str)
		except Exception:
			return json.dumps(
				{'error': 'Failed to serialise model'},
				indent=2,
			)
