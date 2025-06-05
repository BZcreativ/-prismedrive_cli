# PrismDrive CLI

A Command-Line Interface (CLI) for interacting with the PrismDrive API.

## Description

This tool allows users to manage their files and folders on PrismDrive directly from the command line. It supports operations such as listing, uploading, downloading, deleting, moving, and renaming files and folders.

## Features (Planned)

*   List files and folders
*   Upload files and folders
*   Download files and folders
*   Create folders
*   Delete files and folders (to trash or permanently)
*   Move files and folders
*   Rename files and folders
*   Copy files and folders (duplicate)
*   Edit file/folder metadata
*   Secure credential storage (optional, via system keyring)
*   Streaming upload with progress bar

## Prerequisites

*   Python 3.7+
*   An account with PrismDrive

## Installation

### From Source / Development Setup

1.  **Clone the repository (if applicable):**
    ```bash
    # git clone https://github.com/your_username/prismedrive-cli.git
    # cd prismedrive-cli
    ```

2.  **Create and activate a virtual environment:**
    *   Using `venv`:
        ```bash
        python -m venv .venv
        source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
        ```
    *   Or using Conda:
        ```bash
        conda create -n prismdrive_env python=3.10
        conda activate prismedrive_env
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `requirements.txt` should include `requests`, `click`, `python-dotenv`, and `tqdm`)*

4.  **Install the CLI in editable mode (optional, for development):**
    ```bash
    pip install -e .
    ```

### As a Standalone Executable (Planned)

Instructions for downloading and using a pre-built binary will be provided here once available.

## Configuration

1.  **Login:**
    The first time you use the CLI, or after logging out, you will need to log in:
    ```bash
    prismdrive login
    ```
    You will be prompted for your email and password. Your access token will be stored locally (currently in a file managed by `auth.py`). Secure storage using `keyring` is a planned feature.

2.  **Environment Variables (Optional):**
    You can create a `.env` file in the project root (copy from `.env.example`) to set variables like `PRISMDRIVE_API_BASE_URL`.

## Usage

Once installed and configured, you can use the `prismdrive` command.

```bash
prismdrive --help
```

### Implemented Commands

Here are the commands that are currently implemented:

#### Authentication

*   **`prismdrive login`**: Logs in to PrismDrive and stores your session token.
    ```bash
    prismdrive login
    # Follow prompts for email and password
    ```
    You can also set `PRISMDRIVE_EMAIL` and `PRISMDRIVE_PASSWORD` environment variables to avoid prompts.

*   **`prismdrive logout`**: Logs out from PrismDrive and clears your stored token.
    ```bash
    prismdrive logout
    ```

#### File and Folder Management (`files` group)

*   **`prismdrive files list [remote_path]`**: Lists files and folders. If `remote_path` is provided, it acts as a search query.
    ```bash
    prismdrive files list
    prismdrive files list "my important document"
    prismdrive files list --per-page 100 --page 2
    prismdrive files list --type folder
    ```

*   **`prismdrive files upload <local_path> [--parent-id PARENT_ID]`**: Uploads a local file to PrismDrive.
    ```bash
    prismdrive files upload ./my_local_file.txt
    prismdrive files upload ./another_file.jpg --parent-id 12345
    ```

*   **`prismdrive files filestream <local_path> [--parent-id PARENT_ID]`**: Uploads a local file to PrismDrive with a progress bar.
    ```bash
    prismdrive files filestream ./large_video.mp4
    prismdrive files filestream ./backup.zip --parent-id 67890
    ```

*   **`prismdrive files mkdir <folder_name> [--parent-id PARENT_ID]`**: Creates a new folder.
    ```bash
    prismdrive files mkdir "New Project Folder"
    prismdrive files mkdir "Subfolder" --parent-id 12345
    ```

*   **`prismdrive files update <entry_id> [--name NEW_NAME] [--description NEW_DESCRIPTION]`**: Updates the metadata (name and/or description) of a file or folder.
    ```bash
    prismdrive files update 98765 --name "Renamed Document"
    prismdrive files update 54321 --description "This is an important file."
    prismdrive files update 98765 --name "Final Report" --description "Updated version of the report."
    ```

## Known Issues

*   **Persistent AttributeError during Streaming Upload:** After a successful streaming upload (`files filestream`), an `AttributeError` related to accessing 'base_url' on the `ProgressFile` object may still appear. The upload itself completes successfully, but this error message is displayed afterward. This likely indicates an issue in the CLI's post-upload processing or cleanup and requires further debugging with a full traceback to pinpoint the exact cause.
*   **Slow Upload Speed:** Uploads may be slower than expected, even with a fast internet connection. Client-side processing overhead (like the progress bar) has been investigated and does not appear to be the primary cause. This issue is likely due to external factors such as PrismDrive API/server performance or network conditions.

## Development

(Details about running tests, linters, etc.)

## Contributing

(Guidelines for contributing to the project.)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (to be created).
