from scraper.scheduler.scheduler_state import (
	SchedulerStateManager,
)
from scraper.schemas.scheduler_state import SchedulerState
from scraper.utils.hashing import stable_id
from tests.utils.files import delete_file
from tests.utils.scheduler import (
	get_ministry_services_identifier,
)

# --- Test Constants ---

TEST_MINISTRY_IDS = [
	stable_id([f'Test Ministry{i}']) for i in range(3)
]

# --- Tests for SchedulerState ---


def test_creating_scheduler_state():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Check that the state manager is initialized correctly
	assert isinstance(
		state_manager.get_state(), SchedulerState
	)

	# Assert main fields are initialized to their
	# default values
	state = state_manager.get_state()
	assert state.faq.scraped is False
	assert state.agencies_list.scraped is False
	assert state.ministries_list.scraped is False
	assert state.ministry_pages.scraped is False
	assert state.ministry_services.scraped is False
	assert state.faq.processed is False
	assert state.agencies_list.processed is False
	assert state.ministries_list.processed is False
	assert state.ministry_pages.processed is False
	assert state.ministry_services.processed is False


def test_updating_scheduler_state():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Update some fields in the state
	state_manager.update_faq_state(
		scraped=True, processed=True
	)
	state_manager.update_agencies_list_state(scraped=True)
	state_manager.update_ministries_list_state(
		processed=True
	)

	# Check that the updates are reflected in the state
	state = state_manager.get_state()
	assert state.faq.scraped is True
	assert state.faq.processed is True
	assert state.agencies_list.scraped is True
	assert state.agencies_list.processed is False
	assert state.ministries_list.scraped is False
	assert state.ministries_list.processed is True


def test_loading_state_from_file():
	# Create a SchedulerStateManager instance and
	# update state
	state_manager = SchedulerStateManager()
	state_manager.update_faq_state(
		scraped=True, processed=True
	)

	# Save the state to a file
	state_manager.save_state()

	# Create a new instance that loads from the file
	new_state_manager = SchedulerStateManager()

	# Check that the loaded state matches the saved state
	new_state = new_state_manager.get_state()
	assert new_state.faq.scraped is True
	assert new_state.faq.processed is True

	# Clean up the state file after the test
	delete_file(state_manager.state_file)


def test_applying_ministries_list_state():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministries list state with test ministry IDs
	state_manager.apply_ministries_list_state(
		TEST_MINISTRY_IDS
	)

	# Check that the ministries list state is
	# updated correctly
	state = state_manager.get_state()
	state_ids = [
		id for id in state.ministries_detail.keys()
	]
	assert set(state_ids) == set(TEST_MINISTRY_IDS)


def test_updating_ministry_page_scraped_state():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministries list state with test ministry IDs
	state_manager.apply_ministries_list_state(
		TEST_MINISTRY_IDS
	)

	# Update the scraped state for one of the ministries
	test_ministry_id = TEST_MINISTRY_IDS[0]
	state_manager.update_ministry_page_scraped_state(
		test_ministry_id
	)

	# Check that the scraped state for the ministry is
	# updated
	state = state_manager.get_state()
	ministry_details = state.ministries_detail.get(
		test_ministry_id
	)
	assert ministry_details is not None
	assert ministry_details.page.scraped is True


def test_updating_ministries_page_processed_state():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministries list state with test ministry IDs
	state_manager.apply_ministries_list_state(
		TEST_MINISTRY_IDS
	)

	# Update the processed state for all ministries
	state_manager.update_ministries_page_processed_state(
		TEST_MINISTRY_IDS
	)

	# Check that the processed state for all ministries is
	# updated
	state_manager.check_global_ministries_page_processed_state()
	assert (
		state_manager.get_state().ministry_pages.processed
		is True
	)

	state = state_manager.get_state()
	for ministry_id in TEST_MINISTRY_IDS:
		ministry_details = state.ministries_detail.get(
			ministry_id
		)
		assert ministry_details is not None
		assert ministry_details.page.processed is True


def test_updating_all_ministry_pages_scraped_state():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministries list state with test ministry IDs
	state_manager.apply_ministries_list_state(
		TEST_MINISTRY_IDS
	)

	# Update the scraped state for all ministries
	for ministry_id in TEST_MINISTRY_IDS:
		state_manager.update_ministry_page_scraped_state(
			ministry_id
		)

	# Check that the scraped state for all ministries is
	# updated
	state_manager.check_global_ministries_page_scraped_state()
	assert (
		state_manager.get_state().ministry_pages.scraped
		is True
	)

	state = state_manager.get_state()
	for ministry_id in TEST_MINISTRY_IDS:
		ministry_details = state.ministries_detail.get(
			ministry_id
		)
		assert ministry_details is not None
		assert ministry_details.page.scraped is True


def test_apply_ministry_services_identifier():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministry services identifier for a test ministry
	test_ministry_id = TEST_MINISTRY_IDS[0]
	test_department_id = stable_id(['Test Department'])
	test_agency_id = stable_id(['Test Agency'])

	# First add id to ministries list
	state_manager.apply_ministries_list_state(
		[test_ministry_id]
	)

	# Then apply the ministry services identifier
	ministry_services_identifier = (
		get_ministry_services_identifier(
			ministry_id=test_ministry_id,
			department_ids={
				test_department_id: [test_agency_id]
			},
		)
	)
	state_manager.apply_ministry_services_identifier(
		ministry_services_identifier
	)

	# Check that the ministry services identifier is applied
	# correctly in the state
	state = state_manager.get_state()
	ministry_state = state.ministries_detail.get(
		test_ministry_id
	)
	assert ministry_state is not None
	assert ministry_state.ministry_id == test_ministry_id

	departments = ministry_state.departments.get(
		test_department_id
	)
	assert departments is not None
	assert departments.department_id == test_department_id

	agencies = departments.agencies.get(test_agency_id)
	assert agencies is not None
	assert agencies.agency_id == test_agency_id


def test_update_ministry_services_scraped_and_processed_state():  # noqa: E501
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministry services identifier for a test ministry
	test_ministry_id = TEST_MINISTRY_IDS[0]
	test_department_id = stable_id(['Test Department'])
	test_agency_id = stable_id(['Test Agency'])

	# First add id to ministries list
	state_manager.apply_ministries_list_state(
		[test_ministry_id]
	)

	# Then apply the ministry services identifier
	ministry_services_identifier = (
		get_ministry_services_identifier(
			ministry_id=test_ministry_id,
			department_ids={
				test_department_id: [test_agency_id]
			},
		)
	)
	state_manager.apply_ministry_services_identifier(
		ministry_services_identifier
	)

	# Mark page as scraped and processed to set up for
	# testing the services state updates
	state_manager.update_ministry_page_scraped_state(
		test_ministry_id
	)
	state_manager.update_ministries_page_processed_state(
		[test_ministry_id]
	)

	# --- Scraped state tests ---

	# Update the scraped state for the ministry services
	state_manager.update_ministry_services_scraped_state(
		ministry_id=test_ministry_id,
		department_id=test_department_id,
		agency_id=test_agency_id,
	)

	# Check that the scraped state for the ministry
	# services is updated correctly in the state
	state = state_manager.get_state()
	ministry_state = state.ministries_detail.get(
		test_ministry_id
	)
	assert ministry_state is not None
	assert ministry_state.services.scraped is True

	# --- Processed state tests ---

	# Update the processed state for the ministry services
	state_manager.update_ministry_services_processed_state(
		ministry_id=test_ministry_id,
		department_agencies={
			test_department_id: [test_agency_id]
		},
	)

	# Check that the processed state for the ministry
	# services is updated correctly in the state
	state = state_manager.get_state()
	ministry_state = state.ministries_detail.get(
		test_ministry_id
	)
	assert ministry_state is not None
	assert ministry_state.services.processed is True

	assert ministry_state.complete is True


def test_check_ministry_services_global_flags():
	# Create a SchedulerStateManager instance
	state_manager = SchedulerStateManager()

	# Apply ministry services identifier for a test ministry
	# Use first 2 ministries for this test
	test_ministry_ids = TEST_MINISTRY_IDS[:2]
	test_department_id = stable_id(['Test Department'])
	test_agency_id = stable_id(['Test Agency'])

	# First add ids to ministries list
	state_manager.apply_ministries_list_state(
		test_ministry_ids
	)

	# Then apply the ministry services identifier
	# for both ministries
	for ministry_id in test_ministry_ids:
		ministry_services_identifier = (
			get_ministry_services_identifier(
				ministry_id=ministry_id,
				department_ids={
					test_department_id: [test_agency_id]
				},
			)
		)
		state_manager.apply_ministry_services_identifier(
			ministry_services_identifier
		)

	# --- Scrape tests ---

	# Test updating scraped state for one ministry
	# and checking global flags
	state_manager.update_ministry_services_scraped_state(
		ministry_id=test_ministry_ids[0],
		department_id=test_department_id,
		agency_id=test_agency_id,
	)
	state_manager.check_global_ministry_services_scraped_state()
	state = state_manager.get_state()
	# Not all ministries have services scraped
	assert state.ministry_services.scraped is False

	# Update scraped state for the second ministry and
	# check global flags again
	state_manager.update_ministry_services_scraped_state(
		ministry_id=test_ministry_ids[1],
		department_id=test_department_id,
		agency_id=test_agency_id,
	)
	state_manager.check_global_ministry_services_scraped_state()
	state = state_manager.get_state()
	# All ministries have services scraped
	assert state.ministry_services.scraped is True

	# --- Processed tests ---

	# Test updating processed state for one ministry
	# and checking global flags
	state_manager.update_ministry_services_processed_state(
		ministry_id=test_ministry_ids[0],
		department_agencies={
			test_department_id: [test_agency_id]
		},
	)
	state_manager.check_global_ministry_services_processed_state()
	state = state_manager.get_state()
	# Not all ministries have services processed
	assert state.ministry_services.processed is False

	# Update processed state for the second ministry and
	# check global flags again
	state_manager.update_ministry_services_processed_state(
		ministry_id=test_ministry_ids[1],
		department_agencies={
			test_department_id: [test_agency_id]
		},
	)
	state_manager.check_global_ministry_services_processed_state()
	state = state_manager.get_state()
	# All ministries have services processed
	assert state.ministry_services.processed is True
