import click
import os
from dotenv import load_dotenv

# Assuming api_client.py and auth.py are in the same directory (prismedrive_cli)
from .api_client import PrismDriveAPIClient, PRISMDRIVE_API_BASE_URL
from .auth import login as auth_login_action, logout as auth_logout_action, get_token as auth_get_token
from .commands.files import files_group

# Load environment variables from .env file if it exists
# Useful for PRISMDRIVE_API_BASE_URL or other configurations
load_dotenv()

@click.group()
@click.option('--api-base-url', envvar='PRISMDRIVE_API_BASE_URL', default=PRISMDRIVE_API_BASE_URL, help='Base URL for the PrismDrive API.')
@click.pass_context
def cli(ctx, api_base_url):
    """
    PrismDrive CLI Tool
    """
    # Initialize context object
    ctx.ensure_object(dict)
    
    # Initialize API client
    client = PrismDriveAPIClient(base_url=api_base_url)
    ctx.obj['api_client'] = client
    
    # Attempt to load token and set it in the client
    # The auth_get_token function now also ensures the client has the token if found
    token = auth_get_token(api_client=client)
    if token:
        # click.echo("Token loaded into API client.", err=True) # Debug
        pass
    else:
        # click.echo("No existing token found or loaded.", err=True) # Debug
        pass

@cli.command("login")
@click.option('--email', envvar='PRISMDRIVE_EMAIL', help="Your PrismDrive email address. Can also be set via PRISMDRIVE_EMAIL env var.")
@click.option('--password', envvar='PRISMDRIVE_PASSWORD', help="Your PrismDrive password. Can also be set via PRISMDRIVE_PASSWORD env var.")
@click.option('--device-name', default='prismdrive-cli', show_default=True, envvar='PRISMDRIVE_DEVICE_NAME', help="Device name to register with the API.")
@click.pass_context
def login_command(ctx, email, password, device_name):
    """Login to PrismDrive and save the session token."""
    final_email = email
    final_password = password

    if not final_email:
        final_email = click.prompt("Email", type=str)
    
    if not final_password:
        final_password = click.prompt("Password", hide_input=True, confirmation_prompt=False, type=str)

    api_client = ctx.obj['api_client']
    auth_login_action(api_client, final_email, final_password, device_name)

@cli.command("logout")
@click.pass_context
def logout_command(ctx):
    """Logout from PrismDrive and clear the session token."""
    api_client = ctx.obj.get('api_client') # api_client might not be there if init failed
    auth_logout_action(api_client)

# Add command groups
cli.add_command(files_group)

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        # Catch any unexpected exceptions and print a generic error message
        click.echo(f"An unexpected error occurred: {type(e).__name__} - {e}", err=True)
        # Avoid accessing specific attributes on the exception object here
        # If you need more detailed logging, you would do it here without
        # assuming the exception object has specific attributes like 'base_url'.
        # For now, just printing the type and message is sufficient for a top-level handler.
        exit(1) # Exit with a non-zero status code to indicate failure
