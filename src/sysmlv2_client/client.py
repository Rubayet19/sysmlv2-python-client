# src/sysmlv2_client/client.py

import requests
import json
from typing import Optional, Dict, Any, List

from .exceptions import (
    SysMLV2Error,
    SysMLV2AuthError,
    SysMLV2APIError,
    SysMLV2NotFoundError,
    SysMLV2BadRequestError,
    SysMLV2ConflictError,
)

class SysMLV2Client:
    """
    A client for interacting with a SysML v2 API server (like OpenMBEE Flexo).
    """
    def __init__(self, base_url: str, bearer_token: str):
        """
        Initializes the SysMLV2Client.

        Args:
            base_url: The base URL of the SysML v2 API server (e.g., "http://localhost:8083").
            bearer_token: The bearer token for authentication (including "Bearer ").
        """
        if not base_url:
            raise ValueError("base_url cannot be empty.")
        if not bearer_token or not bearer_token.lower().startswith("bearer "):
            raise ValueError("bearer_token must be provided and start with 'Bearer '.")

        self.base_url = base_url.rstrip('/')
        self._bearer_token = bearer_token
        self._headers = {
            "Authorization": self._bearer_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Add other common headers if needed
        }
        self._session = requests.Session()
        self._session.headers.update(self._headers)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
    ) -> Dict[str, Any]:
        """
        Internal helper method to make API requests.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path (e.g., "/projects").
            params: URL parameters.
            data: Request body data (will be JSON encoded).
            expected_status: The expected HTTP status code for a successful request.

        Returns:
            The JSON response from the API.

        Raises:
            SysMLV2AuthError: If authentication fails (401 or 403).
            SysMLV2NotFoundError: If the resource is not found (404).
            SysMLV2BadRequestError: If the request is malformed (400).
            SysMLV2ConflictError: If a conflict occurs (409).
            SysMLV2APIError: For other API-related errors.
            SysMLV2Error: For general client or connection errors.
        """
        url = f"{self.base_url}{endpoint}"
        json_data = json.dumps(data) if data else None

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                data=json_data,
                # Consider adding a timeout
                # timeout=10
            )

            # Check for specific error codes first
            if response.status_code == 401 or response.status_code == 403:
                raise SysMLV2AuthError(f"Authentication failed: {response.status_code} - {response.text}")
            if response.status_code == 404:
                raise SysMLV2NotFoundError(f"Resource not found at {endpoint}: {response.text}")
            if response.status_code == 400:
                 # Try to parse error details if available
                try:
                    error_details = response.json()
                except json.JSONDecodeError:
                    error_details = response.text
                raise SysMLV2BadRequestError(f"Bad request for {endpoint}: {error_details}")
            if response.status_code == 409:
                raise SysMLV2ConflictError(f"Conflict detected for {endpoint}: {response.text}")

            # Check if the status code matches the expected one
            if response.status_code != expected_status:
                raise SysMLV2APIError(
                    status_code=response.status_code,
                    message=f"Unexpected status code for {method} {endpoint}. Response: {response.text}"
                )

            # Handle successful responses with no content (e.g., DELETE)
            if response.status_code == 204 or not response.content:
                return {}

            # Parse successful JSON response
            return response.json()

        except requests.exceptions.RequestException as e:
            raise SysMLV2Error(f"Network error during request to {url}: {e}") from e
        except json.JSONDecodeError as e:
             raise SysMLV2Error(f"Failed to decode JSON response from {url}: {e}. Response text: {response.text}") from e

    # --- Core API Methods will be added below ---

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of projects.
        Corresponds to: GET /projects
        """
        # Assuming the API returns a structure like {"elements": [...]} or similar
        response_data = self._request(method="GET", endpoint="/projects", expected_status=200)
        # Extract the list of projects, default to empty list if not found
        # TODO: Verify the actual key for the list in the API response (e.g., 'projects', 'elements')
        if isinstance(response_data, list):
            return response_data # API returned a list directly
        elif isinstance(response_data, dict):
             # TODO: Verify the actual key for the list in the API response (e.g., 'projects', 'elements')
            return response_data.get('elements', []) # Try to extract from dict
        else:
            # Unexpected response type, raise an error or return empty list?
            # For now, return empty list, but logging a warning might be good
            return []

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new project.
        Corresponds to: POST /projects
        Args:
            project_data: Dictionary representing the project to create.
                          Structure depends on the API specification.
        """
        return self._request(
            method="POST",
            endpoint="/projects",
            data=project_data,
            expected_status=201  # Typically 201 Created for POST
        )

    def get_element(self, project_id: str, element_id: str, commit_id: str = "main") -> Dict[str, Any]:
        """
        Retrieves a specific element from a commit within a project.
        Corresponds to: GET /projects/{project_id}/commits/{commit_id}/elements/{element_id}
        """
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}"
        return self._request(method="GET", endpoint=endpoint, expected_status=200)

    def create_element(self, project_id: str, element_data: Dict[str, Any], commit_id: str = "main") -> Dict[str, Any]:
        """
        Creates a new element within a specific commit of a project.
        Corresponds to: POST /projects/{project_id}/commits/{commit_id}/elements
        Args:
            project_id: The ID of the project.
            element_data: Dictionary representing the element to create.
            commit_id: The commit ID (defaults to 'main').
        """
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements"
        return self._request(
            method="POST",
            endpoint=endpoint,
            data=element_data,
            expected_status=201
        )

    def update_element(self, project_id: str, element_id: str, element_data: Dict[str, Any], commit_id: str = "main") -> Dict[str, Any]:
        """
        Updates an existing element within a specific commit of a project.
        Corresponds to: PUT /projects/{project_id}/commits/{commit_id}/elements/{element_id}
        Args:
            project_id: The ID of the project.
            element_id: The ID of the element to update.
            element_data: Dictionary representing the updated element data.
            commit_id: The commit ID (defaults to 'main').
        """
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}"
        return self._request(
            method="PUT",
            endpoint=endpoint,
            data=element_data,
            expected_status=200
        )

    def delete_element(self, project_id: str, element_id: str, commit_id: str = "main") -> None:
        """
        Deletes an element from a specific commit within a project.
        Corresponds to: DELETE /projects/{project_id}/commits/{commit_id}/elements/{element_id}
        """
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}"
        self._request(method="DELETE", endpoint=endpoint, expected_status=204)
        # DELETE requests typically return no content on success
        return None

    def get_owned_elements(self, project_id: str, element_id: str, commit_id: str = "main") -> List[Dict[str, Any]]:
        """
        Retrieves elements owned by a specific element.
        NOTE: Exact endpoint/method needs verification against API spec/cookbook.
        Might be GET /projects/{project_id}/commits/{commit_id}/elements/{element_id}/owned-elements
        or potentially part of a broader query mechanism.
        """
        # NOTE: Endpoint needs verification based on actual API spec
        endpoint = f"/projects/{project_id}/commits/{commit_id}/elements/{element_id}/owned"
        response_data = self._request(method="GET", endpoint=endpoint, expected_status=200)
        # Assuming the API returns a structure like {"elements": [...]}
        # TODO: Verify the actual key for the list in the API response
        if isinstance(response_data, list):
            return response_data # API returned a list directly
        elif isinstance(response_data, dict):
            # TODO: Verify the actual key for the list in the API response
            return response_data.get('elements', []) # Try to extract from dict
        else:
            # Unexpected response type
            return []

    def create_commit(self, project_id: str, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new commit in a project.
        Corresponds to: POST /projects/{project_id}/commits
        Args:
            project_id: The ID of the project.
            commit_data: Dictionary representing the commit details (e.g., message, parent commit).
        """
        endpoint = f"/projects/{project_id}/commits"
        return self._request(
            method="POST",
            endpoint=endpoint,
            data=commit_data,
            expected_status=201
        )