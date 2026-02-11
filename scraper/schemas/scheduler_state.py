"""
This module contains schemas for scheduler state
management which tracks the progress of the
scraping process.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ScrapingPhase(str, Enum):
	"""
	Enum of the main phases of the
	scraping process.
	"""

	FAQ = 'FAQ'
	AGENCIES_LIST = 'AGENCIES_LIST'
	MINISTRIES_LIST = 'MINISTRIES_LIST'
	MINISTRIES_PAGES = 'MINISTRIES_PAGES'
	MINISTRIES_SERVICES = 'MINISTRIES_SERVICES'
	FINALISATION = 'FINALISATION'


class StepCheck(BaseModel):
	"""
	Schema for tracking if an individual scraping and
	processing step has been completed.
	"""

	model_config = ConfigDict(
		extra='forbid',
	)

	scraped: bool = Field(
		default=False,
		description=(
			'Whether the scraping step has been completed.'
		),
	)
	processed: bool = Field(
		default=False,
		description=(
			'Whether the processing step has '
			'has been completed'
		),
	)


class AgencyServicesState(BaseModel):
	"""
	Schema for tracking the scraping and processing
	state of individual agencies and their services.
	"""

	agency_id: str = Field(
		...,
		description=('Unique identifier for the agency'),
	)
	ministry_departments_agencies_url: str = Field(
		...,
		description=(
			'URL of the ministry page with the'
			'agency and department query parameters '
			'used to access service information for '
			'the agency.'
		),
	)
	state: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Scraping and processing state for the agency'
		),
	)


class DepartmentState(BaseModel):
	"""
	Schema for tracking the scraping and processing
	state of individual departments.
	"""

	model_config = ConfigDict(
		extra='forbid',
	)

	department_id: str = Field(
		...,
		description=(
			'Unique identifier for the department'
		),
	)
	agencies: dict[str, AgencyServicesState] = Field(
		default_factory=dict,
		description=(
			'List of agencies under the department'
			'with their scraping and processing state'
		),
	)


class MinistryState(BaseModel):
	"""
	Schema for tracking the scraping and processing
	state of individual ministries.
	"""

	model_config = ConfigDict(
		extra='forbid',
	)

	ministry_id: str = Field(
		...,
		description=('Unique identifier for the ministry'),
	)
	departments: dict[str, DepartmentState] = Field(
		default_factory=dict,
		description=(
			'List of departments under the ministry'
			'with their scraping and processing state'
		),
	)
	page: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Whether the ministry detail page has been '
			'scraped.'
		),
	)
	services: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Whether the services under the ministry'
			'has been scraped.'
		),
	)
	complete: bool = Field(
		default=False,
		description=(
			'Whether the ministry data has been fully'
			'processed and is complete.'
		),
	)


class SchedulerState(BaseModel):
	"""
	Schema for tracking the overall state of the
	scraping process across all phases.
	"""

	model_config = ConfigDict(
		extra='forbid',
	)

	faq: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Scraping and processing state for the '
			'FAQ phase'
		),
	)
	agencies_list: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Scraping and processing state for the '
			'agencies list phase'
		),
	)
	ministries_list: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Scraping and processing state for the '
			'ministries list phase'
		),
	)
	ministry_pages: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Scraping and processing state for the '
			'ministries detail phase'
		),
	)
	ministry_services: StepCheck = Field(
		default_factory=StepCheck,
		description=(
			'Scraping and processing state for the '
			'ministries services phase'
		),
	)
	finalisation_checks: bool = Field(
		default=False,
		description=(
			'Whether final checks have been completed to'
			'confirm the dataset is complete and ready for'
			'publishing.'
		),
	)
	ministries_detail: dict[str, MinistryState] = Field(
		default_factory=dict,
		description=(
			'List of ministries with their scraping and '
			'processing state for the ministries '
			'detail phase'
		),
	)
