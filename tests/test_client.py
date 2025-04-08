# tests/test_client.py

import pytest
import requests_mock
import requests

from src.sysmlv2_client import (
    SysMLV2Client,
    SysMLV2Error,
    SysMLV2AuthError,
    SysMLV2APIError,
    SysMLV2NotFoundError,
    SysMLV2BadRequestError,
    SysMLV2ConflictError,
)

# --- Constants for testing ---
TEST_BASE_URL = "http://test-sysml-api.com"
TEST_BEARER_TOKEN = "Bearer FAKE_TOKEN_12345"
TEST_PROJECT_ID = "test_proj_1"
TEST_COMMIT_ID = "main"
TEST_ELEMENT_ID = "elem_abc"


# --- Fixtures ---

@pytest.fixture
def client():
    """Provides a SysMLV2Client instance for testing."""
    return SysMLV2Client(base_url=TEST_BASE_URL, bearer_token=TEST_BEARER_TOKEN)

@pytest.fixture
def mock_session(client):
    """Mocks the requests session used by the client."""
    adapter = requests_mock.Adapter()
    client._session.mount('mock://', adapter) # Use mock adapter for test URLs if needed
    # Primarily, we'll mock specific URLs using requests_mock directly in tests
    return adapter


# --- Test Cases ---

def test_client_initialization(client):
    """Tests successful client initialization."""
    assert client.base_url == TEST_BASE_URL
    assert client._bearer_token == TEST_BEARER_TOKEN
    assert client._headers["Authorization"] == TEST_BEARER_TOKEN
    assert "Content-Type" in client._headers
    assert "Accept" in client._headers

def test_client_initialization_invalid_token():
    """Tests client initialization failure with invalid token format."""
    with pytest.raises(ValueError, match="bearer_token must be provided and start with 'Bearer '"):
        SysMLV2Client(base_url=TEST_BASE_URL, bearer_token="INVALID_TOKEN")
    with pytest.raises(ValueError, match="bearer_token must be provided and start with 'Bearer '"):
        SysMLV2Client(base_url=TEST_BASE_URL, bearer_token="") # Empty token

def test_client_initialization_invalid_url():
    """Tests client initialization failure with invalid base URL."""
    with pytest.raises(ValueError, match="base_url cannot be empty"):
        SysMLV2Client(base_url="", bearer_token=TEST_BEARER_TOKEN)


# --- Test Get Projects ---

def test_get_projects_success(client, requests_mock):
    """Tests successfully retrieving projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    mock_response_data = {"elements": [{"id": "proj1", "name": "Project 1"}, {"id": "proj2"}]}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    projects = client.get_projects()

    assert projects == mock_response_data["elements"]
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "GET"
    assert requests_mock.last_request.headers["Authorization"] == TEST_BEARER_TOKEN

def test_get_projects_success_empty(client, requests_mock):
    """Tests successfully retrieving an empty list of projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    mock_response_data = {"elements": []} # API returns empty list
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    projects = client.get_projects()

    assert projects == []

def test_get_projects_success_no_elements_key(client, requests_mock):
    """Tests retrieving projects when the response structure is unexpected."""
    mock_url = f"{TEST_BASE_URL}/projects"
    mock_response_data = [{"id": "proj1", "name": "Project 1"}] # Missing 'elements' key
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    # The client should return an empty list due to .get('elements', [])
    projects = client.get_projects()

    assert projects == mock_response_data # Should return the list directly

def test_get_projects_auth_error(client, requests_mock):
    """Tests authentication error during get_projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    requests_mock.get(mock_url, status_code=401, text="Unauthorized")

    with pytest.raises(SysMLV2AuthError, match="Authentication failed: 401"):
        client.get_projects()

def test_get_projects_api_error(client, requests_mock):
    """Tests a generic API error during get_projects."""
    mock_url = f"{TEST_BASE_URL}/projects"
    requests_mock.get(mock_url, status_code=500, text="Internal Server Error")

    with pytest.raises(SysMLV2APIError, match="Unexpected status code for GET /projects"):
        client.get_projects()

# --- Test Create Project ---

def test_create_project_success(client, requests_mock):
    """Tests successfully creating a project."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "New Project", "description": "A test project"}
    response_data = {"id": "new_proj_id", **request_data} # Echo back data + ID
    requests_mock.post(mock_url, json=response_data, status_code=201)

    created_project = client.create_project(request_data)

    assert created_project == response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.json() == request_data
    assert requests_mock.last_request.headers["Authorization"] == TEST_BEARER_TOKEN
    assert requests_mock.last_request.headers["Content-Type"] == "application/json"

def test_create_project_bad_request(client, requests_mock):
    """Tests a 400 Bad Request error during project creation."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "Missing required field"} # Invalid data
    error_response = {"error": "Missing description"}
    requests_mock.post(mock_url, json=error_response, status_code=400)

    with pytest.raises(SysMLV2BadRequestError, match="Bad request for /projects"):
        client.create_project(request_data)

def test_create_project_conflict(client, requests_mock):
    """Tests a 409 Conflict error during project creation."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "Existing Project"}
    requests_mock.post(mock_url, status_code=409, text="Project already exists")

    with pytest.raises(SysMLV2ConflictError, match="Conflict detected for /projects"):
        client.create_project(request_data)

def test_create_project_auth_error(client, requests_mock):
    """Tests authentication error during create_project."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "New Project"}
    requests_mock.post(mock_url, status_code=403, text="Forbidden")

    with pytest.raises(SysMLV2AuthError, match="Authentication failed: 403"):
        client.create_project(request_data)

def test_create_project_api_error(client, requests_mock):
    """Tests a generic API error during create_project."""
    mock_url = f"{TEST_BASE_URL}/projects"
    request_data = {"name": "New Project"}
    requests_mock.post(mock_url, status_code=503, text="Service Unavailable")

    # Expecting 201, but got 503
    with pytest.raises(SysMLV2APIError, match="Unexpected status code for POST /projects"):
        client.create_project(request_data)


# --- Test Get Element ---

def test_get_element_success(client, requests_mock):
    """Tests successfully retrieving an element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    mock_response_data = {"id": TEST_ELEMENT_ID, "name": "Test Element", "type": "Block"}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    element = client.get_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert element == mock_response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "GET"

def test_get_element_not_found(client, requests_mock):
    """Tests a 404 Not Found error during get_element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/not_found_id"
    requests_mock.get(mock_url, status_code=404, text="Element not found")

    with pytest.raises(SysMLV2NotFoundError, match="Resource not found"):
        client.get_element(TEST_PROJECT_ID, "not_found_id", TEST_COMMIT_ID)

def test_get_element_auth_error(client, requests_mock):
    """Tests authentication error during get_element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    requests_mock.get(mock_url, status_code=401)

    with pytest.raises(SysMLV2AuthError):
        client.get_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

# --- Test Create Element ---

def test_create_element_success(client, requests_mock):
    """Tests successfully creating an element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements"
    request_data = {"name": "New Element", "type": "Part"}
    response_data = {"id": "new_elem_id", **request_data}
    requests_mock.post(mock_url, json=response_data, status_code=201)

    created_element = client.create_element(TEST_PROJECT_ID, request_data, TEST_COMMIT_ID)

    assert created_element == response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.json() == request_data

def test_create_element_bad_request(client, requests_mock):
    """Tests a 400 Bad Request error during element creation."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements"
    request_data = {"name": "Invalid"} # Missing type maybe
    requests_mock.post(mock_url, status_code=400, json={"error": "Missing type field"})

    with pytest.raises(SysMLV2BadRequestError):
        client.create_element(TEST_PROJECT_ID, request_data, TEST_COMMIT_ID)

# --- Test Update Element ---

def test_update_element_success(client, requests_mock):
    """Tests successfully updating an element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    request_data = {"name": "Updated Element Name"}
    response_data = {"id": TEST_ELEMENT_ID, **request_data}
    requests_mock.put(mock_url, json=response_data, status_code=200)

    updated_element = client.update_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, request_data, TEST_COMMIT_ID)

    assert updated_element == response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "PUT"
    assert requests_mock.last_request.json() == request_data

def test_update_element_not_found(client, requests_mock):
    """Tests updating a non-existent element (404)."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/not_found_id"
    request_data = {"name": "Updated Name"}
    requests_mock.put(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.update_element(TEST_PROJECT_ID, "not_found_id", request_data, TEST_COMMIT_ID)

# --- Test Delete Element ---

def test_delete_element_success(client, requests_mock):
    """Tests successfully deleting an element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    requests_mock.delete(mock_url, status_code=204) # No content expected

    result = client.delete_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert result is None # Method returns None on success
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "DELETE"

def test_delete_element_not_found(client, requests_mock):
    """Tests deleting a non-existent element (404)."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/not_found_id"
    requests_mock.delete(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.delete_element(TEST_PROJECT_ID, "not_found_id", TEST_COMMIT_ID)

def test_delete_element_auth_error(client, requests_mock):
    """Tests authentication error during delete_element."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}"
    requests_mock.delete(mock_url, status_code=401)

    with pytest.raises(SysMLV2AuthError):
        client.delete_element(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)


# --- Test Get Owned Elements ---

def test_get_owned_elements_success(client, requests_mock):
    """Tests successfully retrieving owned elements."""
    # Note: Using the assumed endpoint, needs verification
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}/owned"
    mock_response_data = {"elements": [{"id": "owned_elem_1"}, {"id": "owned_elem_2"}]}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    owned_elements = client.get_owned_elements(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert owned_elements == mock_response_data["elements"]
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "GET"

def test_get_owned_elements_not_found(client, requests_mock):
    """Tests 404 when parent element not found for owned elements."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/not_found_parent/owned"
    requests_mock.get(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.get_owned_elements(TEST_PROJECT_ID, "not_found_parent", TEST_COMMIT_ID)

def test_get_owned_elements_empty(client, requests_mock):
    """Tests retrieving empty owned elements list."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits/{TEST_COMMIT_ID}/elements/{TEST_ELEMENT_ID}/owned"
    mock_response_data = {"elements": []}
    requests_mock.get(mock_url, json=mock_response_data, status_code=200)

    owned_elements = client.get_owned_elements(TEST_PROJECT_ID, TEST_ELEMENT_ID, TEST_COMMIT_ID)

    assert owned_elements == []

# --- Test Create Commit ---

def test_create_commit_success(client, requests_mock):
    """Tests successfully creating a commit."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits"
    request_data = {"message": "Initial commit", "parentCommitId": None}
    response_data = {"id": "new_commit_id", **request_data}
    requests_mock.post(mock_url, json=response_data, status_code=201)

    created_commit = client.create_commit(TEST_PROJECT_ID, request_data)

    assert created_commit == response_data
    assert requests_mock.last_request.url == mock_url
    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.json() == request_data

def test_create_commit_bad_request(client, requests_mock):
    """Tests 400 Bad Request during commit creation."""
    mock_url = f"{TEST_BASE_URL}/projects/{TEST_PROJECT_ID}/commits"
    request_data = {} # Missing message
    requests_mock.post(mock_url, status_code=400, json={"error": "Missing commit message"})

    with pytest.raises(SysMLV2BadRequestError):
        client.create_commit(TEST_PROJECT_ID, request_data)

def test_create_commit_project_not_found(client, requests_mock):
    """Tests 404 when project not found during commit creation."""
    mock_url = f"{TEST_BASE_URL}/projects/invalid_project/commits"
    request_data = {"message": "Commit message"}
    requests_mock.post(mock_url, status_code=404)

    with pytest.raises(SysMLV2NotFoundError):
        client.create_commit("invalid_project", request_data)