from scraper.scheduler.scheduler import Scheduler
from scraper.schemas.scheduler_state import MinistryState
from scraper.schemas.scheduler_task import (
	EmptyPayload,
	MinistryIdentifier,
	MinistryIdentifiers,
	MinistryServicesIdentifiersList,
	MinistryTaskListPayload,
	MinistryTaskPayload,
	ScrapingPhase,
	ServicesProcessedIdentifier,
	ServicesScrapedIdentifier,
	ServiceTaskListPayload,
	ServiceTaskPayload,
	TaskOperation,
	TaskResult,
)
from scraper.static.paths import Paths
from scraper.utils.hashing import stable_id
from tests.utils.files import delete_file
from tests.utils.scheduler import (
	get_ministry_services_identifier,
)

# --- Test Constants ---

TEST_MINISTRY_IDS = [
	stable_id([f'Test Ministry{i}']) for i in range(3)
]


def _get_ministry_state_for_id(
	ministry_id: str,
) -> MinistryState:
	"""
	Helper function to create a MinistryState
	object for a given ministry ID.
	"""
	return MinistryState(
		ministry_id=ministry_id,
	)


# --- Tests for Scheduler ---


def test_scheduler_initialization():
	"""
	Test that the Scheduler initializes with the
	correct state.
	"""
	state_file_name = 'test_scheduler_0_state.json'
	delete_file(Paths.TEMP_DIR / state_file_name)

	scheduler = Scheduler(state_file_name=state_file_name)

	state = scheduler._state_manager.get_state()
	# Scheduler properties
	assert scheduler is not None
	assert scheduler.current_task is None
	assert not scheduler._ministries_page_scrape_queue
	assert not scheduler._ministries_services_queue
	# Scheduler state manager
	assert state is not None
	assert state.faq.scraped is False
	assert state.faq.processed is False
	assert state.agencies_list.scraped is False
	assert state.agencies_list.processed is False
	assert state.ministries_list.scraped is False
	assert state.ministries_list.processed is False
	assert state.ministry_pages.scraped is False
	assert state.ministry_pages.processed is False
	assert state.ministry_services.scraped is False
	assert state.ministry_services.processed is False
	assert state.finalisation_checks is False


def test_scheduler_faq_phase_completion():
	"""
	Test that the Scheduler correctly schedules
	FAQ scraping and processing tasks, and updates state
	when they are completed.
	"""
	state_file_name = 'test_scheduler_1_state.json'
	delete_file(Paths.TEMP_DIR / state_file_name)

	scheduler = Scheduler(state_file_name=state_file_name)

	# Get scrape task
	scrape_task = scheduler.next_task()
	assert scrape_task is not None
	assert scrape_task.scope == ScrapingPhase.FAQ
	assert scrape_task.operation == TaskOperation.FAQ_SCRAPE
	assert isinstance(scrape_task.payload, EmptyPayload)

	# Simulate completing scrape task
	scrape_result = TaskResult(
		task=scrape_task,
		success=True,
		error_message=None,
	)

	scheduler.apply_task_result(scrape_result)
	state = scheduler._state_manager.get_state()
	assert state.faq.scraped is True
	assert state.faq.processed is False

	# Get process task
	process_task = scheduler.next_task()
	assert process_task is not None
	assert process_task.scope == ScrapingPhase.FAQ
	assert (
		process_task.operation == TaskOperation.FAQ_PROCESS
	)
	assert isinstance(process_task.payload, EmptyPayload)

	# Simulate completing process task
	process_result = TaskResult(
		task=process_task,
		success=True,
		error_message=None,
	)
	scheduler.apply_task_result(process_result)
	state = scheduler._state_manager.get_state()
	assert state.faq.scraped is True
	assert state.faq.processed is True

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)


def test_scheduler_agencies_list_phase_completion():
	"""
	Test that the Scheduler correctly schedules
	agencies list scraping and processing tasks,
	and updates state when they are completed.
	"""
	state_file_name = 'test_scheduler_2_state.json'
	delete_file(Paths.TEMP_DIR / state_file_name)

	scheduler = Scheduler(state_file_name=state_file_name)

	# Bypass FAQ phase
	scheduler._state_manager._state.faq.scraped = True
	scheduler._state_manager._state.faq.processed = True
	scheduler._state_manager.save_state()

	# Get scrape task
	scrape_task = scheduler.next_task()
	assert scrape_task is not None
	assert scrape_task.scope == ScrapingPhase.AGENCIES_LIST
	assert (
		scrape_task.operation
		== TaskOperation.AGENCIES_LIST_SCRAPE
	)
	assert isinstance(scrape_task.payload, EmptyPayload)

	# Simulate completing scrape task
	scrape_result = TaskResult(
		task=scrape_task,
		success=True,
		error_message=None,
	)

	scheduler.apply_task_result(scrape_result)
	state = scheduler._state_manager.get_state()
	assert state.agencies_list.scraped is True
	assert state.agencies_list.processed is False

	# Get process task
	process_task = scheduler.next_task()
	assert process_task is not None
	assert process_task.scope == ScrapingPhase.AGENCIES_LIST
	assert (
		process_task.operation
		== TaskOperation.AGENCIES_LIST_PROCESS
	)
	assert isinstance(process_task.payload, EmptyPayload)

	# Simulate completing process task
	process_result = TaskResult(
		task=process_task,
		success=True,
		error_message=None,
	)
	scheduler.apply_task_result(process_result)
	state = scheduler._state_manager.get_state()
	assert state.agencies_list.scraped is True
	assert state.agencies_list.processed is True

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)


def test_scheduler_ministries_list_phase_completion():
	"""
	Test that the Scheduler correctly schedules
	ministries list scraping and processing tasks,
	and updates state when they are completed.
	"""
	state_file_name = 'test_scheduler_3_state.json'
	delete_file(Paths.TEMP_DIR / state_file_name)

	scheduler = Scheduler(state_file_name=state_file_name)

	# Bypass previous phases
	scheduler._state_manager._state.faq.scraped = True
	scheduler._state_manager._state.faq.processed = True
	scheduler._state_manager._state.agencies_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.agencies_list.processed = True  # noqa: E501
	scheduler._state_manager.save_state()

	# Get scrape task
	scrape_task = scheduler.next_task()
	assert scrape_task is not None
	assert (
		scrape_task.scope == ScrapingPhase.MINISTRIES_LIST
	)
	assert (
		scrape_task.operation
		== TaskOperation.MINISTRIES_LIST_SCRAPE
	)
	assert isinstance(scrape_task.payload, EmptyPayload)

	# Simulate completing scrape task
	scrape_result = TaskResult(
		task=scrape_task,
		success=True,
		error_message=None,
	)

	scheduler.apply_task_result(scrape_result)
	state = scheduler._state_manager.get_state()
	assert state.ministries_list.scraped is True
	assert state.ministries_list.processed is False

	# Get process task
	process_task = scheduler.next_task()
	assert process_task is not None
	assert (
		process_task.scope == ScrapingPhase.MINISTRIES_LIST
	)
	assert (
		process_task.operation
		== TaskOperation.MINISTRIES_LIST_PROCESS
	)
	assert isinstance(process_task.payload, EmptyPayload)

	# Simulate completing process task
	ministry_identifiers = MinistryIdentifiers(
		ministry_ids=TEST_MINISTRY_IDS
	)
	process_result = TaskResult(
		task=process_task,
		success=True,
		error_message=None,
		discovered_data=ministry_identifiers,
	)
	scheduler.apply_task_result(process_result)
	state = scheduler._state_manager.get_state()
	assert state.ministries_list.scraped is True
	assert state.ministries_list.processed is True

	# Check that ministry IDs were added to the ministries
	# page scrape queue
	assert len(
		scheduler._ministries_page_scrape_queue
	) == len(TEST_MINISTRY_IDS)
	queue_ids = {
		ministry_state.ministry_id
		for ministry_state in scheduler._ministries_page_scrape_queue  # noqa: E501
	}
	for ministry_id in TEST_MINISTRY_IDS:
		assert ministry_id in queue_ids

	# Check ministry IDs were added to the state
	state_ids = scheduler._state_manager.get_state().ministries_detail  # noqa: E501
	for ministry_id in TEST_MINISTRY_IDS:
		assert ministry_id in state_ids

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)


def test_scheduler_ministries_page_phase_completion():
	"""
	Test that the Scheduler correctly schedules
	ministry page scraping and processing tasks,
	and updates state when they are completed.
	"""
	test_file_name = 'test_scheduler_4_state.json'
	delete_file(Paths.TEMP_DIR / test_file_name)

	scheduler = Scheduler(state_file_name=test_file_name)

	# Bypass previous phases
	scheduler._state_manager._state.faq.scraped = True
	scheduler._state_manager._state.faq.processed = True
	scheduler._state_manager._state.agencies_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.agencies_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.processed = True  # noqa: E501

	# Add test ministry IDs to state and scrape queue
	ministry_identifiers = MinistryIdentifiers(
		ministry_ids=TEST_MINISTRY_IDS
	)
	scheduler._apply_ministries_list_to_scrape_queue(
		ministry_identifiers=ministry_identifiers
	)
	scheduler._state_manager.save_state()

	# --- Scrape ---

	# Check that scrape tasks are generated
	# for each ministry whilst simulating
	# completing them in sequence and checking
	# state updates
	for ministry_id in TEST_MINISTRY_IDS:
		# Get scrape task
		scrape_task = scheduler.next_task()
		assert scrape_task is not None
		assert (
			scrape_task.scope
			== ScrapingPhase.MINISTRIES_PAGES
		)
		assert (
			scrape_task.operation
			== TaskOperation.MINISTRIES_PAGE_SCRAPE
		)
		assert isinstance(
			scrape_task.payload, MinistryTaskPayload
		)
		assert (
			scrape_task.payload.ministry_id == ministry_id
		)
		# Simulate completing scrape task
		scrape_result = TaskResult(
			task=scrape_task,
			success=True,
			error_message=None,
			discovered_data=MinistryIdentifier(
				ministry_id=ministry_id
			),
		)
		scheduler.apply_task_result(scrape_result)

		# Check that ministry is not in the page
		# scrape queue anymore
		queue_ids = {
			ministry_state.ministry_id
			for ministry_state in scheduler._ministries_page_scrape_queue  # noqa: E501
		}
		assert ministry_id not in queue_ids

		# Check state updates
		state = scheduler._state_manager.get_state()
		assert ministry_id in state.ministries_detail
		ministry_state = state.ministries_detail[
			ministry_id
		]
		assert ministry_state.page.scraped is True
		assert ministry_state.page.processed is False

	# Once all ministries have been scraped, check that
	# global ministry page scrape state is updated
	state = scheduler._state_manager.get_state()
	assert state.ministry_pages.scraped is True
	assert state.ministry_pages.processed is False

	# --- Process ---

	# Assert that next task is batch processing task for
	# all ministries that were scraped
	process_task = scheduler.next_task()
	assert process_task is not None
	assert (
		process_task.scope == ScrapingPhase.MINISTRIES_PAGES
	)
	assert (
		process_task.operation
		== TaskOperation.MINISTRIES_PAGE_PROCESS
	)
	assert isinstance(
		process_task.payload, MinistryTaskListPayload
	)
	assert set(
		[
			m.ministry_id
			for m in process_task.payload.ministry_ids
		]
	) == set(TEST_MINISTRY_IDS)

	# Simulate completing process task
	ministry_services_identifiers = []
	for ministry_id in TEST_MINISTRY_IDS:
		ministry_services_identifier = (
			get_ministry_services_identifier(
				ministry_id=ministry_id
			)
		)
		ministry_services_identifiers.append(
			ministry_services_identifier
		)
	process_result = TaskResult(
		task=process_task,
		success=True,
		error_message=None,
		discovered_data=MinistryServicesIdentifiersList(
			ministry_services_identifiers=ministry_services_identifiers
		),
	)
	scheduler.apply_task_result(process_result)

	# Check that all ministries have their page processing
	# state updated
	state = scheduler._state_manager.get_state()
	for ministry_id in TEST_MINISTRY_IDS:
		assert ministry_id in state.ministries_detail
		ministry_state = state.ministries_detail[
			ministry_id
		]
		assert ministry_state.page.scraped is True
		assert ministry_state.page.processed is True

	# Check that global ministry page processing state is
	# updated
	assert state.ministry_pages.scraped is True
	assert state.ministry_pages.processed is True

	# Check that ministry services scrape tasks have been
	# scheduled for all ministries
	queue_ids = {
		mid
		for mid, _ in scheduler._ministries_services_queue
	}
	for ministry_id in TEST_MINISTRY_IDS:
		assert ministry_id in queue_ids

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)


def test_scheduler_ministries_services_phase_completion():
	"""
	Test that the Scheduler correctly schedules
	ministry services scraping and processing tasks,
	and updates state when they are completed.
	"""
	test_file_name = 'test_scheduler_5_state.json'
	delete_file(Paths.TEMP_DIR / test_file_name)

	scheduler = Scheduler(state_file_name=test_file_name)

	# Bypass previous phases
	scheduler._state_manager._state.faq.scraped = True
	scheduler._state_manager._state.faq.processed = True
	scheduler._state_manager._state.agencies_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.agencies_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministry_pages.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministry_pages.processed = True  # noqa: E501

	# Create test service identifiers for ministries
	# and add them to state
	test_ministry_services_identifiers = [
		get_ministry_services_identifier(
			ministry_id=ministry_id
		)
		for ministry_id in TEST_MINISTRY_IDS
	]
	# Add test ministry IDs to state and add
	# service identifiers
	scheduler._state_manager.apply_ministries_list_state(
		TEST_MINISTRY_IDS
	)

	for (
		ministry_service_identifier
	) in test_ministry_services_identifiers:
		scheduler._state_manager.apply_ministry_services_identifier(
			ministry_identifier=ministry_service_identifier
		)

	scheduler._state_manager.save_state()
	scheduler._apply_ministry_services_to_scrape_queue()

	# Check that scrape tasks are generated for each
	# ministry in the queue
	queue_ids = {
		mid
		for mid, _ in scheduler._ministries_services_queue
	}
	for (
		ministry_service_identifier
	) in test_ministry_services_identifiers:
		ministry_id = (
			ministry_service_identifier.ministry_id
		)
		assert ministry_id in queue_ids

	# Check that scrape tasks are generated for each
	# ministry whilst simulating completing them in
	# sequence and checking state updates - We also
	# check that ministries are processed in batches
	for (
		ministry_service_identifier
	) in test_ministry_services_identifiers:
		ministry_id = (
			ministry_service_identifier.ministry_id
		)
		for (
			department_id,
			department_services_identifier,
		) in (
			ministry_service_identifier.departments.items()
		):
			for (
				agency_id,
				agency_services_identifier,
			) in department_services_identifier.agencies.items():  # noqa: E501
				# Get scrape task
				task = scheduler.next_task()
				assert task is not None
				assert (
					task.scope
					== ScrapingPhase.MINISTRIES_SERVICES
				)
				assert (
					task.operation
					== TaskOperation.MINISTRIES_SERVICES_SCRAPE  # noqa: E501
				)
				assert isinstance(
					task.payload, ServiceTaskPayload
				)
				assert (
					task.payload.ministry_id == ministry_id
				)
				assert (
					task.payload.department_id
					== department_id
				)
				assert task.payload.agency_id == agency_id
				assert (
					task.payload.agency_id
					== agency_services_identifier.agency_id
				)
				assert (
					task.payload.ministry_departments_agencies_url
					== agency_services_identifier.ministry_departments_agencies_url  # noqa: E501
				)

				# Simulate completing scrape task
				scrape_result = TaskResult(
					task=task,
					success=True,
					error_message=None,
					discovered_data=ServicesScrapedIdentifier(
						ministry_id=ministry_id,
						department_id=department_id,
						agency_id=agency_id,
					),
				)
				scheduler.apply_task_result(scrape_result)

				# Check state updates
				state = scheduler._state_manager.get_state()
				assert (
					ministry_id in state.ministries_detail
				)
				ministry_state = state.ministries_detail[
					ministry_id
				]
				assert (
					department_id
					in ministry_state.departments
				)
				department_state = (
					ministry_state.departments[
						department_id
					]
				)
				agencies = department_state.agencies[
					agency_id
				]
				assert agencies.state.scraped is True
				assert agencies.state.processed is False

		# Once all services for the ministry have been
		# scraped, check that the next task processes all
		# services for the ministry in a batch and that
		# state is updated accordingly
		# Check that ministry queue is empty
		ministry_services_queue = (
			scheduler._ministries_services_queue[0][1]
		)
		assert not ministry_services_queue

		# Check state
		state = scheduler._state_manager.get_state()
		ministry_state = state.ministries_detail[
			ministry_id
		]
		assert ministry_state.services.scraped is True
		assert ministry_state.services.processed is False

		# Check that next task is batch processing
		# task for the ministry
		process_task = scheduler.next_task()
		assert process_task is not None
		assert (
			process_task.scope
			== ScrapingPhase.MINISTRIES_SERVICES
		)
		assert (
			process_task.operation
			== TaskOperation.MINISTRIES_SERVICES_PROCESS
		)
		assert isinstance(
			process_task.payload, ServiceTaskListPayload
		)

		# Inspect payload to check that it contains all
		# services for the ministry
		for (
			service_task_payload
		) in process_task.payload.service_tasks:
			assert (
				service_task_payload.ministry_id
				== ministry_id
			)
			assert (
				service_task_payload.department_id
				in ministry_service_identifier.departments
			)
			assert (
				service_task_payload.agency_id
				in ministry_service_identifier.departments[
					service_task_payload.department_id
				].agencies
			)
			agency_services_identifier = (
				ministry_service_identifier.departments[
					service_task_payload.department_id
				].agencies[service_task_payload.agency_id]
			)
			assert (
				service_task_payload.ministry_departments_agencies_url
				== agency_services_identifier.ministry_departments_agencies_url  # noqa: E501
			)

		# Simulate completing process task
		departments_agencies = {
			d_id: []
			for d_id in ministry_service_identifier.departments  # noqa: E501
		}
		for (
			department_id,
			department_services_identifier,
		) in (
			ministry_service_identifier.departments.items()
		):
			for (
				agency_id
			) in department_services_identifier.agencies:  # noqa: E501
				departments_agencies[department_id].append(
					agency_id
				)
		process_result = TaskResult(
			task=process_task,
			success=True,
			error_message=None,
			discovered_data=ServicesProcessedIdentifier(
				ministry_id=ministry_id,
				department_agencies=departments_agencies,
			),
		)
		scheduler.apply_task_result(process_result)

		# Check state updates
		state = scheduler._state_manager.get_state()
		assert ministry_id in state.ministries_detail
		ministry_state = state.ministries_detail[
			ministry_id
		]
		assert ministry_state.services.scraped is True
		assert ministry_state.services.processed is True
		for (
			department_id,
			department_services_identifier,
		) in (
			ministry_service_identifier.departments.items()
		):
			assert (
				department_id in ministry_state.departments
			)
			department_state = ministry_state.departments[
				department_id
			]
			for (
				agency_id
			) in department_services_identifier.agencies:  # noqa: E501
				assert (
					agency_id in department_state.agencies
				)
				agency_state = department_state.agencies[
					agency_id
				]
				assert agency_state.state.scraped is True
				assert agency_state.state.processed is True

	# Check global flags
	state = scheduler._state_manager.get_state()
	assert state.ministry_services.scraped is True
	assert state.ministry_services.processed is True

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)


def test_scheduler_finalisation_checks():
	"""
	Test that the Scheduler correctly schedules
	finalisation check task after all ministries have
	their services processed, and updates state when
	the task is completed.
	"""
	test_file_name = 'test_scheduler_6_state.json'
	delete_file(Paths.TEMP_DIR / test_file_name)

	scheduler = Scheduler(state_file_name=test_file_name)

	# Bypass all phases except finalisation checks
	scheduler._state_manager._state.faq.scraped = True
	scheduler._state_manager._state.faq.processed = True
	scheduler._state_manager._state.agencies_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.agencies_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministry_pages.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministry_pages.processed = True  # noqa: E501
	scheduler._state_manager._state.ministry_services.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministry_services.processed = True  # noqa: E501

	# Assert that next task is finalisation check task
	task = scheduler.next_task()
	assert task is not None
	assert task.scope == ScrapingPhase.FINALISATION
	assert (
		task.operation == TaskOperation.FINALISATION_CHECKS
	)
	assert isinstance(task.payload, EmptyPayload)

	# Simulate completing finalisation checks task
	result = TaskResult(
		task=task,
		success=True,
		error_message=None,
	)
	scheduler.apply_task_result(result)

	# Check state updates
	state = scheduler._state_manager.get_state()
	assert state.finalisation_checks is True

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)


def test_scheduler_completion():
	"""
	Test that the Scheduler correctly identifies when the
	entire scraping process is complete after finalisation
	checks are marked as completed.
	"""
	test_file_name = 'test_scheduler_7_state.json'
	delete_file(Paths.TEMP_DIR / test_file_name)

	scheduler = Scheduler(state_file_name=test_file_name)

	# Bypass all phases and finalisation checks
	scheduler._state_manager._state.faq.scraped = True
	scheduler._state_manager._state.faq.processed = True
	scheduler._state_manager._state.agencies_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.agencies_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministries_list.processed = True  # noqa: E501
	scheduler._state_manager._state.ministry_pages.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministry_pages.processed = True  # noqa: E501
	scheduler._state_manager._state.ministry_services.scraped = True  # noqa: E501
	scheduler._state_manager._state.ministry_services.processed = True  # noqa: E501
	scheduler._state_manager._state.finalisation_checks = (
		True  # noqa: E501
	)

	# Assert that next task is None, indicating completion
	task = scheduler.next_task()
	assert task is None

	# Clear saved state file after test
	delete_file(scheduler._state_manager.state_file)
