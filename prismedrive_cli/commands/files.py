import click
from prismedrive_cli.auth import ensure_authenticated # Corrected import path
import os
from pathlib import Path
from tqdm import tqdm

# This will be a group for file and folder related commands
@click.group("files")
@click.pass_context
def files_group(ctx):
    """Commands for managing files and folders."""
    if 'api_client' not in ctx.obj:
        click.echo("API client not initialized in context.", err=True)
        ctx.exit(1)
    # Further checks like ensuring authentication can be done per command or here
    pass

@files_group.command("list")
@click.argument("remote_path", required=False, default=None) # Default to None to signify root or all
@click.option('--page', type=int, help="Page number for pagination.")
@click.option('--per-page', type=int, default=50, show_default=True, help="Number of entries per page.")
@click.option('--type', 'entry_type', type=click.Choice(['folder', 'image', 'text', 'audio', 'video', 'pdf'], case_sensitive=False), help="Filter by entry type.")
@click.option('--deleted', 'deleted_only', is_flag=True, help="Show only trashed entries.")
@click.option('--starred', 'starred_only', is_flag=True, help="Show only starred entries.")
@click.option('--recent', 'recent_only', is_flag=True, help="Show only recent entries.")
@click.option('--shared', 'shared_only', is_flag=True, help="Show only entries shared with you.")
@click.option('--workspace-id', type=str, help="Workspace ID to filter by.")
@ensure_authenticated # Ensures user is logged in (or token is available)
@click.pass_context
def list_entries(ctx, remote_path, page, per_page, entry_type, deleted_only, starred_only, recent_only, shared_only, workspace_id):
    """
    List files and folders.
    If REMOTE_PATH is provided, it will be used as a search query.
    To list contents of a specific folder by ID, future enhancements will be needed.
    """
    api_client = ctx.obj['api_client']
    
    query_params = {
        "page": page,
        "per_page": per_page,
        "entry_type": entry_type,
        "deleted_only": deleted_only if deleted_only else None, # Pass None if False to avoid "false" string
        "starred_only": starred_only if starred_only else None,
        "recent_only": recent_only if recent_only else None,
        "shared_only": shared_only if shared_only else None,
        "query": remote_path if remote_path and remote_path != "/" else None, # Use remote_path as query
        "workspace_id": workspace_id
        # parent_id handling would require path-to-ID resolution first.
        # For now, if remote_path is provided, it acts as a general search query.
        # If remote_path is None or "/", it lists root/all accessible items based on other filters.
    }
    # Filter out None values from params before passing to API client
    active_params = {k: v for k, v in query_params.items() if v is not None}

    click.echo(f"Fetching entries... (Query: {active_params.get('query', 'All')}, Workspace ID: {active_params.get('workspace_id', 'None')})")
    
    response = api_client.list_entries(**active_params)

    # Debug the response structure
    if isinstance(response, dict):
        # Check if this is our custom error dictionary
        if response.get("error"):
            error_msg = response.get("message", "Unknown error")
            click.echo(f"Error listing entries: {error_msg}", err=True)
            return
            
        # Check for common API response envelope patterns
        if "data" in response and isinstance(response["data"], list):
            entries = response["data"]
            # Optionally print pagination info if available
            if "meta" in response:
                meta = response["meta"]
                click.echo(f"Page {meta.get('current_page', 1)} of {meta.get('last_page', 1)}, "
                          f"showing {len(entries)} of {meta.get('total', len(entries))} entries")
        elif "entries" in response and isinstance(response["entries"], list):
            entries = response["entries"]
        elif "files" in response and isinstance(response["files"], list):
            entries = response["files"]
        elif "items" in response and isinstance(response["items"], list):
            entries = response["items"]
        else:
            # If we can't find a list in common envelope fields, print the response structure
            click.echo(f"Response structure: {list(response.keys())}", err=True)
            click.echo("Cannot find entries list in response. Please check API documentation.")
            return
    elif isinstance(response, list):
        entries = response
    else:
        click.echo(f"Failed to fetch entries. Unexpected response format: {type(response)}", err=True)
        return
        
    if not entries:
        click.echo("No entries found.")
        return

    click.echo("-----------------------------------------------------")
    click.echo(f"{'ID':<7} {'Type':<10} {'Size':<12} Name")
    click.echo("-----------------------------------------------------")
    for entry in entries:
        entry_id = entry.get('id', 'N/A')
        name = entry.get('name', 'N/A')
        etype = entry.get('type', 'N/A')
        
        size_bytes = entry.get('file_size')
        if etype == 'folder' or size_bytes is None:
            size_str = "-"
        elif size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024**2:
            size_str = f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            size_str = f"{size_bytes/1024**2:.1f} MB"
        else:
            size_str = f"{size_bytes/1024**3:.1f} GB"
        
        deleted_str = " (deleted)" if entry.get('deleted_at') else ""
        click.echo(f"{str(entry_id):<7} {etype:<10} {size_str:<12} {name}{deleted_str}")
    click.echo("-----------------------------------------------------")


@files_group.command("upload")
@click.argument("local_path", type=click.Path(exists=True, readable=True, resolve_path=True))
@click.option('--parent-id', help="ID of the parent folder to upload to. Defaults to root folder.")
@ensure_authenticated
@click.pass_context
def upload_file(ctx, local_path, parent_id):
    """
    Upload a file to PrismDrive.
    
    LOCAL_PATH is the path to the local file to upload.
    """
    api_client = ctx.obj['api_client']
    
    # Get file info for display
    file_path = Path(local_path)
    file_name = file_path.name
    file_size = os.path.getsize(file_path)
    
    # Format file size for display
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024**2:
        size_str = f"{file_size/1024:.1f} KB"
    elif file_size < 1024**3:
        size_str = f"{file_size/1024**2:.1f} MB"
    else:
        size_str = f"{file_size/1024**3:.1f} GB"

    click.echo(f"Uploading {file_name} ({size_str}) to PrismDrive...")
    
    # Show destination info
    destination = "root folder"
    if parent_id:
        destination = f"folder with ID: {parent_id}"
    
    click.echo(f"Destination: {destination}")
    
    # Indicate that the upload is in progress
    click.echo("Upload in progress...")
    
    # Call API client to upload file
    response = api_client.upload_file(
        file_path=local_path,
        parent_id=parent_id
    )
    
    # Handle response
    if isinstance(response, dict) and response.get("error"):
        error_msg = response.get("message", "Unknown error")
        click.echo(f"Error uploading file: {error_msg}", err=True)
        return
    
    # Check for successful upload
    if isinstance(response, dict):
        # Try to extract file info from response
        if "data" in response and isinstance(response["data"], dict):
            file_info = response["data"]
        else:
            file_info = response
        
        # Display success message with file ID if available
        file_id = file_info.get("id", "N/A")
        click.echo(f"✓ File uploaded successfully! File ID: {file_id}")
        
        # Display additional file info if available
        if "name" in file_info:
            click.echo(f"Name: {file_info['name']}")
        if "type" in file_info:
            click.echo(f"Type: {file_info['type']}")
        if "file_size" in file_info:
            size_bytes = file_info["file_size"]
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024**2:
                size_str = f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                size_str = f"{size_bytes/1024**2:.1f} MB"
            else:
                size_str = f"{size_bytes/1024**3:.1f} GB"
            click.echo(f"Size: {size_str}")
    else:
        click.echo("File uploaded, but couldn't parse response details.")

@files_group.command("filestream")
@click.argument("local_path", type=click.Path(exists=True, readable=True, resolve_path=True))
@click.option('--parent-id', help="ID of the parent folder to upload to. Defaults to root folder.")
@ensure_authenticated
@click.pass_context
def filestream_file(ctx, local_path, parent_id):
    """
    Upload a file to PrismDrive with real-time progress.
    
    LOCAL_PATH is the path to the local file to upload.
    """
    api_client = ctx.obj['api_client']
    
    file_path = Path(local_path)
    file_name = file_path.name
    file_size = os.path.getsize(file_path)

    # Format file size for display
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024**2:
        size_str = f"{file_size/1024:.1f} KB"
    elif file_size < 1024**3:
        size_str = f"{file_size/1024**2:.1f} MB"
    else:
        size_str = f"{file_size/1024**3:.1f} GB"

    click.echo(f"Preparing to stream upload {file_name} ({size_str}) to PrismDrive...")

    destination = "root folder"
    if parent_id:
        destination = f"folder with ID: {parent_id}"
    click.echo(f"Destination: {destination}")

    # Use tqdm for progress bar
    with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {file_name}") as pbar:
        def progress_callback(bytes_sent, total_bytes):
            pbar.update(bytes_sent - pbar.n) # Update by the difference

        response = None # Initialize response before the try block
        try:
            # Call the new streaming upload method
            response = api_client.upload_file_streamed(
                file_path=local_path,
                parent_id=parent_id,
                progress_callback=progress_callback
            )
        except Exception as e:
            # Catch any exception during the streaming upload call
            click.echo(f"\nError during streaming upload call: {type(e).__name__} - {e}", err=True)
            # Return an error dictionary consistent with the expected format
            response = {"error": True, "message": f"Streaming upload failed: {type(e).__name__} - {e}"}


    # Handle response after the progress bar is finished (and after the try/except)
    if isinstance(response, dict) and response.get("error"):
        error_msg = response.get("message", "Unknown error")
        click.echo(f"\nError streaming file upload: {error_msg}", err=True) # Add newline after progress bar
        return

    if isinstance(response, dict):
        if "data" in response and isinstance(response["data"], dict):
            file_info = response["data"]
        else:
            file_info = response

        file_id = file_info.get("id", "N/A")
        click.echo(f"\n✓ File streamed and uploaded successfully! File ID: {file_id}") # Add newline after progress bar

        if "name" in file_info:
            click.echo(f"Name: {file_info['name']}")
        if "type" in file_info:
            click.echo(f"Type: {file_info['type']}")
        if "file_size" in file_info:
            size_bytes = file_info["file_size"]
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024**2:
                size_str = f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                size_str = f"{size_bytes/1024**2:.1f} MB"
            else:
                size_str = f"{size_bytes/1024**3:.1f} GB"
            click.echo(f"Size: {size_str}")
    else:
        click.echo("\nFile streamed and uploaded, but couldn't parse response details.") # Add newline

@files_group.command("mkdir")
@click.argument("folder_name", type=str)
@click.option('--parent-id', help="ID of the parent folder. Defaults to root folder.")
@ensure_authenticated
@click.pass_context
def create_folder(ctx, folder_name, parent_id):
    """
    Create a new folder in PrismDrive.
    
    FOLDER_NAME is the name of the folder to create.
    """
    api_client = ctx.obj['api_client']
    
    click.echo(f"Creating folder '{folder_name}'...")
    
    # Show destination info
    destination = "root folder"
    if parent_id:
        destination = f"folder with ID: {parent_id}"
    
    # Call API client to create folder
    response = api_client.create_folder(
        name=folder_name,
        parent_id=parent_id
    )
    
    # Handle response
    if isinstance(response, dict) and response.get("error"):
        error_msg = response.get("message", "Unknown error")
        click.echo(f"Error creating folder: {error_msg}", err=True)
        return
    
    # Check for successful folder creation
    if isinstance(response, dict):
        # Try to extract folder info from response
        if "data" in response and isinstance(response["data"], dict):
            folder_info = response["data"]
        else:
            folder_info = response
        
        # Display success message with folder ID if available
        folder_id = folder_info.get("id", "N/A")
        click.echo(f"✓ Folder created successfully! Folder ID: {folder_id}")
        
        # Display additional folder info if available
        if "name" in folder_info:
            click.echo(f"Name: {folder_info['name']}")
        if "created_at" in folder_info:
            click.echo(f"Created at: {folder_info['created_at']}")
    else:
        click.echo("Folder created, but couldn't parse response details.")

@files_group.command("update")
@click.argument("entry_id", type=int)
@click.option('--name', help="New name for the file or folder.")
@click.option('--description', help="New description for the file or folder.")
@ensure_authenticated
@click.pass_context
def update_entry(ctx, entry_id, name, description):
    """
    Update an existing file or folder.
    
    ENTRY_ID is the ID of the file or folder to update.
    """
    api_client = ctx.obj['api_client']
    
    if not name and not description:
        click.echo("Error: At least one of --name or --description must be provided.", err=True)
        return

    click.echo(f"Updating entry with ID: {entry_id}...")
    
    response = api_client.update_entry(
        entry_id=entry_id,
        name=name,
        description=description
    )
    
    # Handle response
    if isinstance(response, dict) and response.get("error"):
        error_msg = response.get("message", "Unknown error")
        click.echo(f"Error updating entry: {error_msg}", err=True)
        return
    
    # Check for successful update
    if isinstance(response, dict):
        # Try to extract entry info from response
        if "data" in response and isinstance(response["data"], dict):
            entry_info = response["data"]
        else:
            entry_info = response
        
        # Display success message with entry ID and updated info
        updated_id = entry_info.get("id", "N/A")
        click.echo(f"✓ Entry updated successfully! Entry ID: {updated_id}")
        
        # Display updated info if available
        if "name" in entry_info:
            click.echo(f"New Name: {entry_info['name']}")
        if "description" in entry_info:
            click.echo(f"New Description: {entry_info['description']}")
    else:
        click.echo("Entry updated, but couldn't parse response details.")


# We will add other file commands here: download, rm, mv, cp, etc.

if __name__ == '__main__':
    # This allows testing the command group directly if needed, though typically run via main.py
    # For direct testing, a mock context would be needed.
    pass
