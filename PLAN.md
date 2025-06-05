# Project Plan: PrismDrive Linux CLI

**Objective:** Create a command-line interface (CLI) tool in Python that interacts with the PrismDrive API to perform file and folder operations, including list, copy (upload/download/duplicate), transfer (move), delete, edit (metadata), and rename. The tool should be buildable as a Linux binary.

**Target Directory:** `prismedrive/`

**Core Technologies:**
*   **Language:** Python 3.x
*   **Key Libraries:**
    *   `requests`: For making HTTP API calls.
    *   `click` (recommended) or `argparse`: For creating a user-friendly command-line interface. `click` is often preferred for its ease of use and composability.
    *   `python-dotenv` (optional but good practice): For managing environment variables (e.g., API base URL).
    *   `keyring` (optional, for secure credential storage): To securely store user credentials instead of plain text files, if desired.
    *   `PyInstaller` or similar: For packaging the Python application into a standalone Linux executable.
    *   `tqdm`: For displaying progress bars during uploads/downloads.

---

### Phase 1: Project Setup & Core API Client

1.  **Directory Structure:**
    ```
    prismedrive/
    ├── prismedrive_cli/           # Main application package
    │   ├── __init__.py
    │   ├── main.py                # CLI entry point (using click)
    │   ├── api_client.py          # Handles all API communication
    │   ├── auth.py                # Authentication logic
    │   ├── commands/              # Directory for different command groups
    │   │   ├── __init__.py
    │   │   ├── files.py           # File/folder related commands
    │   │   └── ...                # Other command groups if needed
    │   └── utils.py               # Utility functions (e.g., error handling, config)
    ├── tests/                     # Unit and integration tests
    │   ├── __init__.py
    │   └── ...
    ├── .env.example               # Example environment variables
    ├── config.ini.example         # Example configuration file (if used)
    ├── requirements.txt           # Python dependencies
    ├── setup.py                   # For packaging (optional if only using PyInstaller)
    └── README.md                  # Project documentation
    ```
    *Status: Completed.*

2.  **Virtual Environment:**
    *   Set up a Python virtual environment (e.g., `python -m venv .venv` and activate it).
    *Status: Assumed completed by user.*

3.  **Install Dependencies:**
    *   Create `requirements.txt` with initial dependencies: `requests`, `click`, `python-dotenv`, `tqdm`.
    *   Install: `pip install -r requirements.txt`
    *Status: Completed (initial dependencies + tqdm).*

4.  **API Client (`prismedrive_cli/api_client.py`):**
    *   Define a class `PrismDriveAPIClient`.
    *   **Constructor:** Takes API base URL.
    *   **Authentication:** Store and manage the Bearer token. Include a method to set the token.
    *   **Request Helper:** A private method (`_request`) to handle common request logic and basic error handling. A streaming request helper (`_stream_request`) is also implemented.
    *   **Endpoint Methods:** Implement methods for each API call defined in the Swagger:
        *   `login(email, password, device_name)` (Implemented in `auth.py`)
        *   `list_entries(parent_id=None, per_page=50, deleted_only=False, ...)` (maps to `GET /file-entries`) - *Status: Implemented.*
        *   `upload_file(file_path, parent_id=None, relative_path=None)` (maps to `POST /uploads`) - *Status: Implemented.*
        *   `create_folder(name, parent_id=None)` (maps to `POST /folders`) - *Status: Implemented.*
        *   `update_entry_metadata(entry_id, name=None, description=None)` (maps to `PUT /file-entries`) - *Status: Implemented.*
        *   `delete_entries(entry_ids, delete_forever=False)` (maps to `DELETE /file-entries`) - *Status: Pending.*
        *   `move_entries(entry_ids, destination_id)` (maps to `POST /file-entries/move`) - *Status: Pending.*
        *   `duplicate_entries(entry_ids, destination_id=None)` (maps to `POST /file-entries/duplicate`) - *Status: Pending.*
        *   `download_file_content(entry_url, local_path)` - *Status: Pending.*

5.  **Authentication Module (`prismedrive_cli/auth.py`):**
    *   `login(api_client, email, password, device_name)`: Calls `api_client.login()`, stores the token. - *Status: Implemented.*
    *   `logout()`: Clears the stored token. - *Status: Implemented.*
    *   `get_token()`: Retrieves the stored token. - *Status: Implemented.*
    *   `ensure_authenticated()`: Decorator or helper to check for a token before running commands. - *Status: Implemented.*

---

### Phase 2: CLI Structure and Basic Commands

1.  **CLI Entry Point (`prismedrive_cli/main.py`):**
    *   Use `click` to define the main command group (`prismdrive`).
    *   Initialize `api_client` and load token.
    *   Add `login` and `logout` commands.
    *   Add other command groups (e.g., `files_group`).
    *Status: Completed.*

2.  **File Commands (`prismedrive_cli/commands/files.py`):**
    *   Create a `click` command group for file operations (`files`).
    *   **`list` (ls):** - *Status: Implemented.*
    *   **`upload`:** - *Status: Implemented.*
    *   **`download`:** - *Status: Pending.*
    *   **`delete` (rm):** - *Status: Pending.*
    *   **`mkdir`:** - *Status: Implemented.*
    *   **`rename` (mv on name, or specific rename command):** Functionality covered by `update`. A dedicated `rename` command is *Status: Pending (Optional)*.
    *   **`move` (mv on location):** - *Status: Pending.*
    *   **`copy` (cp):** - *Status: Pending.*
    *   **`edit` (metadata):** Functionality covered by `update`.
    *   **"Edit" (file content):** - *Status: Pending.*
    *   **`filestream`:** Command for streaming upload with progress bar. - *Status: Implemented.*

---

### Phase 3: Configuration, Error Handling, and Packaging

1.  **Configuration (`prismedrive_cli/utils.py` or dedicated config module):**
    *   Store API base URL (using `.env`).
    *   Store authentication token (handled in `auth.py`).
    *   Functions to load/save configuration.
    *Status: Basic configuration using .env and token storage in auth.py implemented. Using `keyring` is *Status: Pending (Optional)*.*

2.  **Enhanced Error Handling:**
    *   Centralized error display.
    *   Catch `requests.exceptions.RequestException` for network issues.
    *   Handle API errors (401, 403, 422) gracefully.
    *   Provide verbose/debug logging option.
    *Status: Basic error handling in API client and commands implemented. Top-level handler added in main.py. Specific handling for AttributeError added in api_client and files.py. Persistent AttributeError during streaming upload is a known issue requiring further investigation with a traceback.*

3.  **Building for Linux:**
    *   Add `PyInstaller` or similar.
    *   Create build script.
    *   Test binary.
    *Status: Pending.*

---

### Phase 4: Testing and Documentation

1.  **Testing (`tests/`):**
    *   Unit Tests.
    *   Integration Tests.
    *Status: Pending.*

2.  **Documentation (`README.md`):**
    *   Installation instructions.
    *   Configuration details.
    *   Usage examples for all commands.
    *   Build instructions.
    *Status: Pending (Needs to be updated with implemented commands and known issues).*

---

### Mermaid Diagram: CLI Command Structure (Simplified)

```mermaid
graph TD
    A[prismdrive CLI] --> B(auth);
    A --> C(files & folders);

    B --> B1[login];
    B --> B2[logout];

    C --> C1[list / ls];
    C --> C2[upload];
    C --> C3[download];
    C --> C4[delete / rm];
    C --> C5[mkdir];
    C --> C6[rename / mv_meta];
    C --> C7[move / mv_loc];
    C --> C8[copy / cp];
    C --> C9[edit-meta];
    C --> C10[edit-content];
    C --> C11[filestream]; %% Added filestream command

    subgraph Core
        D[APIClient]
        E[AuthHandler]
        F[ConfigManager]
    end

    B1 --> E;
    B2 --> E;
    C1 --> D;
    C2 --> D;
    C3 --> D;
    C4 --> D;
    C5 --> D;
    C6 --> D;
    C7 --> D;
    C8 --> D;
    C9 --> D;
    C10 --> D;
    C11 --> D; %% filestream uses APIClient

    D --> G{PrismDrive API};
    E --> F;
```

---

**Key Considerations & Potential Challenges:**

*   **API Base URL:** The Swagger uses `SITE_URL`. We need the actual base API endpoint. Assuming `https://app.prismdrive.com/api` for now.
*   **File Download:** Clarify how file content is downloaded. The `FileEntry.url` seems promising.
*   **Rename vs. Move:** The API has distinct endpoints. The CLI needs to map user intent (e.g., `mv oldname newname` vs. `mv file /new/folder/`) to the correct API calls (`update_entry_metadata` vs. `move_entries`).
*   **`PUT /file-entries` for Update:** The Swagger for `PUT /file-entries` doesn't show an `entryId` in the path. This is unusual. It might expect the `id` in the body, or it's a batch update. This needs to be confirmed during implementation. If it's a batch update, we might need to fetch the entry, modify it, and then send the whole updated entry object.
*   **Path Resolution:** Converting user-friendly paths (e.g., `/my/folder/file.txt`) to `parentId` or `entryIds` will require logic to traverse the remote directory structure or make multiple API calls.
*   **Large File Uploads/Downloads:** Consider chunked transfers if the `requests` library doesn't handle this transparently for very large files, to manage memory and provide progress. The Swagger for `POST /uploads` uses `multipart/form-data` which is standard.
*   **Rate Limiting:** Be mindful of API rate limits (not specified in Swagger, but common). Implement retries with backoff if needed.
*   **Idempotency:** For operations like upload or create folder, consider how to handle cases where the item already exists.
*   **Persistent AttributeError during Streaming Upload:** A known issue where an AttributeError related to accessing 'base_url' on the ProgressFile object occurs after a successful streaming upload. This likely indicates a problem in the post-upload processing or cleanup within the CLI's execution flow and requires further debugging with a full traceback.
*   **Slow Upload Speed:** The upload speed is slower than expected given the user's internet connection. This is likely due to external factors such as PrismDrive API/server performance or network conditions, as client-side progress bar overhead was ruled out.
