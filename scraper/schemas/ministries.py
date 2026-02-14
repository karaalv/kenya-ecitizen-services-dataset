"""
This module contains schemas for the ministries data
scraped from the eCitizen website.
"""

from pydantic import BaseModel, ConfigDict, Field

from scraper.schemas.departments import DepartmentEntry
from scraper.schemas.scheduler_task import (
	MinistryServicesIdentifier,
)


class MinistryPageData(BaseModel):
	"""
	Schema for the content scraped
	from a Ministry page
	"""

	ministry_id: str
	overview: str
	departments_and_agencies: str


class MinistryPageOverviewData(BaseModel):
	"""
	Schema for processed data from a Ministry
	page, after applying the processing recipe.
	"""

	ministry_id: str
	reported_agency_count: int | None
	reported_service_count: int | None
	ministry_description: str


class MinistryPageAgencyData(BaseModel):
	"""
	Schema for the data related to agencies
	observed on a Ministry page, after applying
	the processing recipe.
	"""

	agency_id: str
	department_id: str
	ministry_id: str
	agency_name: str
	agency_name_hash: str
	ministry_departments_agencies_url: str


class MinistryPageProcessingResult(BaseModel):
	"""
	Schema for the result of processing a Ministry
	page, containing both the overview data and the
	agencies data.
	"""

	ministry_id: str
	ministry_services_identifier: MinistryServicesIdentifier
	department_entries: dict[str, DepartmentEntry]
	ministry_page_agency_data: dict[
		str, MinistryPageAgencyData
	]


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

	reported_agency_count: int | None = Field(
		...,
		description=(
			'Agency count reported by the eCitizen '
			'platform.'
		),
	)
	observed_agency_count: int | None = Field(
		...,
		description=(
			'Agency count observed in the dataset.'
		),
	)
	reported_service_count: int | None = Field(
		...,
		description=(
			'Service count reported by the eCitizen '
			'platform.'
		),
	)
	observed_service_count: int | None = Field(
		...,
		description=(
			'Service count observed in the dataset.'
		),
	)
	observed_department_count: int | None = Field(
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
