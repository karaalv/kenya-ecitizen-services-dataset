"""
This module contains utility functions for testing
the scheduler class and its related components.
"""

from scraper.schemas.scheduler_task import (
	AgencyServicesIdentifier,
	DepartmentServicesIdentifier,
	MinistryServicesIdentifier,
)


def get_agency_service_identifier(
	agency_id: str = 'Test_Agency',
) -> AgencyServicesIdentifier:
	return AgencyServicesIdentifier(
		agency_id=agency_id,
		ministry_departments_agencies_url='test_url',
	)


def get_department_services_identifier(
	department_id: str = 'Test_Department',
	agency_ids: list[str] = [  # noqa: B006
		'Test_Agency1',
		'Test_Agency2',
	],
) -> DepartmentServicesIdentifier:
	return DepartmentServicesIdentifier(
		department_id=department_id,
		agencies={
			agency_id: get_agency_service_identifier(
				agency_id
			)
			for agency_id in agency_ids
		},
	)


def get_ministry_services_identifier(
	ministry_id: str = 'Test_Ministry',
	department_ids: dict[str, list[str]] = {  # noqa: B006
		'Test_Department1': [
			'Test_Agency1',
			'Test_Agency2',
		],
		'Test_Department2': [
			'Test_Agency3',
			'Test_Agency4',
		],
	},
) -> MinistryServicesIdentifier:
	return MinistryServicesIdentifier(
		ministry_id=ministry_id,
		departments={
			department_id: get_department_services_identifier(  # noqa: E501
				department_id, agency_ids
			)
			for department_id, agency_ids in department_ids.items()  # noqa: E501
		},
	)
