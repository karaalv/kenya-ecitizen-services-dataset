"""
This module contains processing utilities related to the
ministries scope of the scraping process.
"""

from scraper.schemas.departments import DepartmentEntry
from scraper.schemas.ministries import (
	MinistryPageAgencyData,
)
from scraper.schemas.scheduler_task import (
	AgencyServicesIdentifier,
	DepartmentServicesIdentifier,
	MinistryServicesIdentifier,
	ServicesProcessedIdentifier,
)
from scraper.schemas.services import ServiceEntry


def build_ministry_services_identifier(
	*,
	ministry_id: str,
	departments: dict[str, DepartmentEntry],
	agencies: dict[str, MinistryPageAgencyData],
) -> MinistryServicesIdentifier:
	"""
	Build a MinistryServicesIdentifier from processed
	departments and ministry page agency data.
	"""

	dept_map: dict[str, DepartmentServicesIdentifier] = {}

	# Initialise departments
	for dept_id in departments.keys():
		dept_map[dept_id] = DepartmentServicesIdentifier(
			department_id=dept_id,
			agencies={},
		)

	# Populate agencies into departments
	for agency_data in agencies.values():
		dept_id = agency_data.department_id

		# Defensive: ensure department exists
		if dept_id not in dept_map:
			dept_map[dept_id] = (
				DepartmentServicesIdentifier(
					department_id=dept_id,
					agencies={},
				)
			)

		dept_map[dept_id].agencies[
			agency_data.agency_id
		] = AgencyServicesIdentifier(
			agency_id=agency_data.agency_id,
			ministry_departments_agencies_url=(
				agency_data.ministry_departments_agencies_url
			),
		)

	return MinistryServicesIdentifier(
		ministry_id=ministry_id,
		departments=dept_map,
	)


def build_services_processed_identifier(
	*,
	ministry_id: str,
	services: list[ServiceEntry],
) -> ServicesProcessedIdentifier:
	"""
	Build a ServicesProcessedIdentifier from processed
	service entries.
	"""
	department_agencies: dict[str, list[str]] = {}
	for service in services:
		dept_id = service.department_id
		agency_id = service.agency_id

		if dept_id not in department_agencies:
			department_agencies[dept_id] = []

		department_agencies[dept_id].append(agency_id)

	return ServicesProcessedIdentifier(
		ministry_id=ministry_id,
		department_agencies=department_agencies,
	)
