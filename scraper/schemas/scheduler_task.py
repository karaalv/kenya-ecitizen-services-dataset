"""
This module contains schemas for scheduler
task definitions which represent the individual
units of work for the scraping process.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from scraper.schemas.scheduler_state import ScrapingPhase


class TaskOperation(str, Enum):
	"""
	Enum for the specific operation of a task
	done by the executor using the handler
	related to the phase of the task.
	"""

	# --- Scraping and processing operations ---
	# These operations are used to define the specific
	# scraping and processing tasks for each phase

	# FAQ related operations
	FAQ_SCRAPE = 'FAQ_SCRAPE'
	FAQ_PROCESS = 'FAQ_PROCESS'

	# Agencies list related operations
	AGENCIES_LIST_SCRAPE = 'AGENCIES_LIST_SCRAPE'
	AGENCIES_LIST_PROCESS = 'AGENCIES_LIST_PROCESS'

	# Ministries list related operations
	MINISTRIES_LIST_SCRAPE = 'MINISTRIES_LIST_SCRAPE'
	MINISTRIES_LIST_PROCESS = 'MINISTRIES_LIST_PROCESS'

	# Ministries detail related operations
	# note this is scraping and processing
	# the ministry overview and departments/agencies
	# information
	MINISTRIES_PAGE_SCRAPE = 'MINISTRIES_PAGE_SCRAPE'
	MINISTRIES_PAGE_PROCESS = 'MINISTRIES_PAGE_PROCESS'

	# Services related operations
	MINISTRIES_SERVICES_SCRAPE = (
		'MINISTRIES_SERVICES_SCRAPE'
	)
	MINISTRIES_SERVICES_PROCESS = (
		'MINISTRIES_SERVICES_PROCESS'
	)

	# Finalisation operations for any
	# final steps
	FINALISATION_CHECKS = 'FINALISATION_CHECKS'


# --- Scheduler task and payload schemas ---


class MinistryTaskPayload(BaseModel):
	"""
	Schema for the payload of a ministries detail
	scraping and processing task, which includes the
	identifier for the ministry.
	"""

	ministry_id: str = Field(
		...,
		description=(
			'Unique identifier for the ministry '
			'the task is related to.'
		),
	)


class MinistryTaskListPayload(BaseModel):
	"""
	Schema for a list of ministries to be
	processed in a task.
	"""

	ministry_ids: list[MinistryTaskPayload] = Field(
		...,
		description=(
			'List of unique identifiers for the ministries '
			'the task is related to.'
		),
	)


class ServiceTaskPayload(BaseModel):
	"""
	Schema for the payload of a service scraping
	and processing task, which includes identifiers for
	the ministry, department and agency the service
	belongs to.
	"""

	ministry_id: str = Field(
		...,
		description=(
			'Unique identifier for the ministry '
			'the service belongs to.'
		),
	)
	department_id: str = Field(
		...,
		description=(
			'Unique identifier for the department '
			'the service belongs to.'
		),
	)
	agency_id: str = Field(
		...,
		description=(
			'Unique identifier for the agency '
			'the service belongs to.'
		),
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


class ServiceTaskListPayload(BaseModel):
	"""
	Schema for a list of services to be
	processed in a task.
	"""

	service_tasks: list[ServiceTaskPayload] = Field(
		...,
		description=('List of service task payloads'),
	)


class EmptyPayload(BaseModel):
	"""
	Schema for tasks that do not require any
	payload.
	"""

	empty: bool = Field(
		default=True,
		description=(
			'A placeholder field to allow for'
			' tasks that do not require any payload.'
		),
	)


PayloadUnion = (
	MinistryTaskPayload
	| MinistryTaskListPayload
	| ServiceTaskPayload
	| ServiceTaskListPayload
	| EmptyPayload
)


class SchedulerTask(BaseModel):
	"""
	Schema for defining individual tasks in the
	scraping scheduler.
	"""

	model_config = ConfigDict(
		extra='forbid',
	)

	scope: ScrapingPhase = Field(
		...,
		description=(
			'The main phase of the scraping process '
			'this task belongs to.'
		),
	)
	operation: TaskOperation = Field(
		...,
		description=(
			'The specific operation this task'
			' performs, which determines the handler'
			' used by the executor.'
		),
	)
	payload: PayloadUnion = Field(
		default_factory=EmptyPayload,
		description=(
			'The payload of the task, which may include '
			'identifiers for the ministry, department and '
			'agency the task is related to. This is only '
			'applicable for tasks related to service '
			'scraping and processing.'
		),
	)


# --- Scheduler task result schema ---


class EmptyDiscoveredData(BaseModel):
	"""
	Schema for tasks that do not discover any
	new data to be passed back to the scheduler.
	"""

	empty: bool = Field(
		default=True,
		description=(
			'A placeholder field to allow for'
			' tasks that do not discover any new data.'
		),
	)


class MinistryIdentifier(BaseModel):
	"""
	Schema for a single ministry identifier discovered
	during scraping to be passed back to the scheduler
	for state updates.
	"""

	ministry_id: str = Field(
		...,
		description=(
			'Unique identifier for the ministry '
			'discovered during scraping to be passed back '
			'to the scheduler for state updates.'
		),
	)


class MinistryIdentifiers(BaseModel):
	"""
	Schema for passing discovered ministry identifiers
	back to the scheduler for state updates.
	"""

	ministry_ids: list[str] = Field(
		...,
		description=(
			'List of unique identifiers for the ministries '
			'discovered during scraping to be passed back '
			'to the scheduler for state updates.'
		),
	)


class AgencyServicesIdentifier(BaseModel):
	"""
	Schema for identifiers related to services discovered
	during scraping of an agency page, to be passed back
	to the scheduler for state updates.
	"""

	agency_id: str = Field(
		...,
		description=(
			'Unique identifier for the agency'
			'discovered during scraping to be passed back '
			'to the scheduler for state updates.'
		),
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


class DepartmentServicesIdentifier(BaseModel):
	"""
	Schema for identifiers related to services discovered
	during scraping of a department page, to be passed
	back to the scheduler for state updates.
	"""

	department_id: str = Field(
		...,
		description=(
			'Unique identifier for the department'
		),
	)
	agencies: dict[str, AgencyServicesIdentifier] = Field(
		default_factory=dict,
		description=(
			'Dictionary mapping agency identifiers to '
			'related service identifiers discovered during '
			'scraping.'
		),
	)


class MinistryServicesIdentifier(BaseModel):
	"""
	Schema for identifiers related to services discovered
	after scraping a ministry page via the ministries
	departments and agencies, to be passed back to the
	scheduler for state updates.
	"""

	ministry_id: str = Field(
		...,
		description=('Unique identifier for the ministry'),
	)
	departments: dict[str, DepartmentServicesIdentifier] = (
		Field(
			default_factory=dict,
			description=(
				'Dictionary mapping department identifiers '
				'to their related service identifiers '
				'discovered during scraping.'
			),
		)
	)


class ServicesScrapedIdentifier(BaseModel):
	"""
	Schema for identifiers related to a service that has
	been scraped, to be passed back to the scheduler for
	state updates.
	"""

	ministry_id: str = Field(
		...,
		description=(
			'Unique identifier for the ministry'
			'the service belongs to.'
		),
	)
	department_id: str = Field(
		...,
		description=(
			'Unique identifier for the department'
			'the service belongs to.'
		),
	)
	agency_id: str = Field(
		...,
		description=(
			'Unique identifier for the agency'
			'the service belongs to.'
		),
	)


class ServicesProcessedIdentifier(BaseModel):
	"""
	Schema for identifiers related to a service that has
	been processed, to be passed back to the scheduler for
	state updates.
	"""

	ministry_id: str = Field(
		...,
		description=(
			'Unique identifier for the ministry'
			'the service belongs to.'
		),
	)
	department_agencies: dict[str, list[str]] = Field(
		...,
		description=(
			'Dictionary mapping department identifiers '
			'to a list of agency identifiers for agencies '
			'that had their services processed.'
		),
	)


DiscoveredDataUnion = (
	MinistryIdentifier
	| MinistryIdentifiers
	| MinistryServicesIdentifier
	| ServicesScrapedIdentifier
	| ServicesProcessedIdentifier
	| EmptyDiscoveredData
)


class TaskResult(BaseModel):
	"""
	Schema for the result of a completed task, which
	includes the task itself and any relevant metadata
	such as success status and error messages.
	"""

	task: SchedulerTask = Field(
		...,
		description='The task that was executed.',
	)
	success: bool = Field(
		...,
		description=(
			'Indicates whether the task was successful.'
		),
	)
	error_message: str | None = Field(
		default=None,
		description='Error message if the task failed.',
	)

	discovered_data: DiscoveredDataUnion = Field(
		default_factory=EmptyDiscoveredData,
		description=(
			'Any new data discovered during task execution '
			'that needs to be passed back to the scheduler '
			'for state updates. This is only applicable for'
			' tasks that involve scraping and may discover '
			'ministries to be added to the processing '
			'queue.'
		),
	)
