"""
This module contains schemas for the
departments data scraped from the eCitizen
website.
"""

from pydantic import BaseModel, ConfigDict, Field


class DepartmentEntry(BaseModel):
	"""
	Schema for Department entries in the
	departments entity, see `docs/schema.md`
	for details.
	"""

	model_config = ConfigDict(
		extra='forbid',
		str_strip_whitespace=True,
	)

	department_id: str = Field(
		...,
		description=(
			'Identifier derived from '
			'`ministry_id-department_name`.'
		),
	)
	ministry_id: str = Field(
		...,
		description=('Identifier of parent ministry.'),
	)
	department_name: str = Field(
		...,
		description=(
			'Department name as listed on '
			'the eCitizen platform.'
		),
	)

	observed_agency_count: int = Field(
		...,
		description=(
			'Number of agencies observed '
			'under the department.'
		),
	)
	observed_service_count: int = Field(
		...,
		description=(
			'Number of services observed '
			'under the department.'
		),
	)

	ministry_departments_url: str = Field(
		...,
		description=(
			'Ministry page URL scoped to the '
			'department via query parameters.'
		),
	)
