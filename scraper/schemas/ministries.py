"""
This module contains schemas for the ministries data
scraped from the eCitizen website.
"""

from pydantic import BaseModel, ConfigDict, Field


class MinistryPageData(BaseModel):
	"""
	Schema for the content scraped
	from a Ministry page
	"""

	overview: str
	departments_and_agencies: str


class MinistryEntry(BaseModel):
	"""
	Schema for Ministry entries in the ministries entity,
	see `docs/schema.md` for details.
	"""

	model_config = ConfigDict(
		extra='forbid',
		str_strip_whitespace=True,
	)

	ministry_id: str = Field(
		...,
		description=(
			'Identifier derived from normalised '
			'ministry name.'
		),
	)
	ministry_name: str = Field(
		...,
		description=(
			'Ministry name as listed on the eCitizen '
			'platform.'
		),
	)
	ministry_description: str = Field(
		...,
		description=('Public ministry description.'),
	)

	reported_agency_count: int = Field(
		...,
		description=(
			'Agency count reported by the eCitizen '
			'platform.'
		),
	)
	observed_agency_count: int = Field(
		...,
		description=(
			'Agency count observed in the dataset.'
		),
	)
	reported_service_count: int = Field(
		...,
		description=(
			'Service count reported by the eCitizen '
			'platform.'
		),
	)
	observed_service_count: int = Field(
		...,
		description=(
			'Service count observed in the dataset.'
		),
	)
	observed_department_count: int = Field(
		...,
		description=(
			'Department count observed in the dataset.'
		),
	)

	ministry_url: str = Field(
		...,
		description=(
			'URL of ministry page on the eCitizen platform.'
		),
	)
