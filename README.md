# SysML v2 Python Client

A basic Python client library for interacting with a SysML v2 API server, specifically tested against the OpenMBEE Flexo implementation.

## Features

*   Provides methods for core SysML v2 operations:
    *   Projects: Get, Create
    *   Elements: Get, Create, Update, Delete, Get Owned
    *   Commits: Create
*   Handles authentication using Bearer tokens.
*   Includes basic error handling and custom exceptions.

## Setup

### 1. Run Flexo SysMLv2 Service Locally

This client is designed to work with a running instance of the OpenMBEE Flexo SysMLv2 service.

*   **Prerequisites:** Docker and Docker Compose installed.
*   **Get Setup Files:** The necessary `docker-compose.yml` and configuration files are located in the `flexo-setup/docker-compose/` directory within this project (downloaded from `Open-MBEE/flexo-mms-sysmlv2`).
*   **Start Services:** Navigate to the `flexo-setup/docker-compose/` directory in your terminal and run:
    ```bash
    docker compose up -d
    ```
    *(Note: On Apple Silicon Macs, ensure Docker Desktop's Rosetta emulation is enabled and `platform: linux/amd64` is set in the `docker-compose.yml` if you encounter architecture issues).*
*   **Initial Org Setup (Potential Manual Step):** For a fresh database, you may need to perform an initial organization setup.
    *   Download/locate the `flexo-sysmlv2.postman_collection.json` file (should be in `flexo-setup/docker-compose/`).
    *   Import it into Postman.
    *   Go to the collection's "Variables" tab and set:
        *   `flexoHost` (CURRENT VALUE) to `localhost:8080`
        *   `host` (CURRENT VALUE) to `localhost:8083`
    *   Save the variables.
    *   Run the first request in the `sysmlv2.` folder (likely named "Create Org"). Check for a successful response.
    *   Refer to `flexo-setup/docker-compose/README.md` for more details.
*   **Authentication Token:** The required Bearer token for the client is found in `flexo-setup/docker-compose/env/flexo-sysmlv2.env` under the `FLEXO_AUTH` variable. Copy this entire value (including `Bearer `).

### 2. Install Client (Development)

Currently, you can use the client directly from the source code. Ensure the `src` directory is in your Python path.

```python
# Example: Add src to path if running scripts/notebooks from project root
import sys
import os
sys.path.insert(0, os.path.abspath('./src'))

from sysmlv2_client import SysMLV2Client
```

*(Future work could include packaging this library for easier installation via pip).*

## Basic Usage

```python
from sysmlv2_client import SysMLV2Client, SysMLV2Error

BASE_URL = "http://localhost:8083"
# Replace with the actual token from flexo-setup/docker-compose/env/flexo-sysmlv2.env
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Truncated for example

try:
    client = SysMLV2Client(base_url=BASE_URL, bearer_token=BEARER_TOKEN)
    print("Client initialized.")

    # Get projects
    projects = client.get_projects()
    print(f"Found projects: {projects}")

    # Create a project (example data)
    new_proj_data = {"@type": "Project", "name": "Client Test Project"}
    created_proj = client.create_project(new_proj_data)
    print(f"Created project: {created_proj}")
    project_id = created_proj.get('id')

    if project_id:
        # Create an element (example data)
        new_elem_data = {"@type": "PartDefinition", "name": "MyBlock"}
        created_elem = client.create_element(project_id, new_elem_data)
        print(f"Created element: {created_elem}")

except SysMLV2Error as e:
    print(f"An API error occurred: {e}")
except ValueError as e:
    print(f"Initialization error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

See the [examples/basic_usage.ipynb](examples/basic_usage.ipynb) Jupyter Notebook for more detailed examples of creating, reading, updating, and deleting elements.

## Running Tests

Unit tests are implemented using `pytest` and `requests-mock`.

1.  **Install Dependencies:**
    ```bash
    pip install pytest requests requests-mock
    ```
2.  **Run Tests:** Navigate to the project root directory in your terminal and run:
    ```bash
    pytest
    ```

## TODO / Future Improvements

*   Verify the exact endpoint for `get_owned_elements`.
*   Verify the expected response key (`elements`) for list endpoints (`get_projects`, `get_owned_elements`).
*   Implement optional Pydantic models (`src/sysmlv2_client/models.py`) for request/response data validation and structure.
*   Add more comprehensive error handling based on specific API error responses.
*   Package the library for `pip` installation.
*   Add more detailed documentation (e.g., API method specifics).
*   Implement remaining SysML v2 API endpoints as needed.