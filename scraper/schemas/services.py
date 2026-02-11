"""
This moule contains schemas for the services data
scraped from the eCitizen website.
"""

from pydantic import BaseModel, ConfigDict, Field


class ServiceEntry(BaseModel):
	"""
	Schema for Service entries in the services
	entity, see `docs/schema.md` for details.
	"""

	model_config = ConfigDict(
		extra='forbid',
		str_strip_whitespace=True,
	)

	service_id: str = Field(
		...,
		description=(
			'Identifier derived from '
			'`ministry_id-department_id-'
			'agency_id-service_name`.'
		),
	)

	agency_id: str = Field(
		...,
		description=('Identifier of responsible agency.'),
	)
	department_id: str = Field(
		...,
		description=('Identifier of parent department.'),
	)
	ministry_id: str = Field(
		...,
		description=('Identifier of parent ministry.'),
	)

	service_name: str = Field(
		...,
		description=(
			'Service name as listed on the '
			'eCitizen platform.'
		),
	)
	service_url: str = Field(
		...,
		description=(
			'URL of the service page on the '
			'eCitizen platform.'
		),
	)

	service_description: str | None = Field(
		None,
		description=(
			'Reserved for future use, currently null.'
		),
	)
	requirements: str | None = Field(
		None,
		description=(
			'Reserved for future use, currently null.'
		),
	)
