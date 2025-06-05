import requests
from urllib.parse import urlparse
import os

# Placeholder for the actual API base URL
# This should be configurable, e.g., via environment variable or config file
PRISMDRIVE_API_BASE_URL = "https://app.prismdrive.com" # Set to root domain based on new findings

class PrismDriveAPIClient:
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or PRISMDRIVE_API_BASE_URL
        self.token = token
        self.session = requests.Session()
        self.session.proxies = {"http": None, "https": None}
        self._update_headers()

    def _update_headers(self):
        # Set a more specific User-Agent and ensure Accept is always application/json
        self.session.headers.clear() # Clear all session headers first
        self.session.headers.update({
            "Accept": "application/json, */*;q=0.8", # Prioritize JSON
            "User-Agent": "PrismDriveCLI/0.1.0",
            # Content-Type will be set per request by the _request or login methods
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
        else:
            # Ensure Authorization header is removed if no token
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]

    def set_token(self, token):
        self.token = token
        self._update_headers()

    def clear_token(self):
        self.token = None
        self._update_headers()

    # Example of a generic request method (can be expanded)
    def _request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = None # Initialize response to None
        
        # Ensure 'Accept' header is explicitly set for this request,
        # overriding session default if necessary, to strongly signal we want JSON.
        request_headers = self.session.headers.copy() # Start with session headers
        request_headers["Accept"] = "application/json"
        
        # If 'headers' are passed in kwargs, merge them, with kwargs taking precedence
        passed_headers = kwargs.pop('headers', None)
        if passed_headers:
            request_headers.update(passed_headers)

        # Special handling for login: ensure no Authorization header is sent
        if endpoint.endswith("auth/login") and method.upper() == "POST":
            if "Authorization" in request_headers:
                # print("DEBUG: Removing Authorization header for /auth/login POST in _request") # Debug
                del request_headers["Authorization"]
        
        try:
            # Use the modified request_headers for this specific call
            print(f"Making {method} request to {url} with params/data: {kwargs.get('params') or kwargs.get('json') or kwargs.get('data')}") # Debug
            print(f"Request Headers for this call: {request_headers}") # Debug
            response = self.session.request(method, url, headers=request_headers, **kwargs)
            print(f"Response Status Code: {response.status_code}") # Debug
            # print(f"Response Headers: {response.headers}") # Debug (can be very verbose)
            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
            
            if response.status_code == 204: # No Content
                return None
            
            # Try to parse JSON, include raw text in error if it fails
            try:
                json_response = response.json()
                return json_response
            except requests.exceptions.JSONDecodeError as json_e:
                print(f"JSONDecodeError: {json_e} - Server response was not valid JSON.")
                print(f"Raw response text (first 500 chars): {response.text[:500]}")
                return {"error": True, "status_code": response.status_code, "message": "Invalid JSON response from server.", "raw_response": response.text}
            except AttributeError as e:
                 # Catch AttributeError specifically during response processing
                 print(f"AttributeError during response processing in _stream_request: {e}")
                 return {"error": True, "status_code": response.status_code if response is not None else None, "message": f"AttributeError during response processing in _stream_request: {e}"}
            except Exception as e:
                 # Catch any other unexpected errors during response processing
                 print(f"Unexpected error during response processing: {type(e).__name__} - {e}")
                 return {"error": True, "status_code": response.status_code if response is not None else None, "message": f"Unexpected error during response processing: {type(e).__name__} - {e}"}


        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code}")
            # Try to get more details from the response text, even if it's an error
            error_text = e.response.text
            print(f"Error Response Text: {error_text[:500]}") # Print first 500 chars
            return {"error": True, "status_code": e.response.status_code, "message": error_text}
        except requests.exceptions.RequestException as e:
            # Handle other request exceptions (e.g., connection error, timeout)
            print(f"Request Exception: {e}")
            # If response object exists (e.g. from a timeout that still got some response info)
            status_code = response.status_code if response is not None else None
            raw_text = response.text if response is not None else None
            return {"error": True, "status_code": status_code, "message": str(e), "raw_response": raw_text}

    def _stream_request(self, method, endpoint, progress_callback=None, **kwargs):
        """
        Makes a streaming request to the API, with optional progress callback.
        Used for uploading large files with progress reporting.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = None # Initialize response to None

        request_headers = self.session.headers.copy() # Start with session headers

        # If 'headers' are passed in kwargs, merge them, with kwargs taking precedence
        passed_headers = kwargs.pop('headers', None)
        if passed_headers:
            request_headers.update(passed_headers)

        # Handle file streaming with progress callback
        files = kwargs.get('files')
        if files and progress_callback:
            # Assuming 'files' is a dictionary like {'file': ('filename', file_object)}
            # Wrap the file object with a progress reporting wrapper
            for key, (filename, file_obj) in files.items():
                files[key] = (filename, ProgressFile(file_obj, progress_callback))
            kwargs['files'] = files # Update kwargs with the wrapped file object

        try:
            print(f"Making streaming {method} request to {url}") # Debug
            print(f"Request Headers for this call: {request_headers}") # Debug

            # Use stream=True for streaming uploads (though requests handles this with file-like objects)
            # The key is that the file-like object provided in 'files' is read in chunks.
            response = self.session.request(method, url, headers=request_headers, **kwargs)

            print(f"Response Status Code: {response.status_code}") # Debug
            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)

            if response.status_code == 204: # No Content
                return None

            # Try to parse JSON, include raw text in error if it fails
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError as json_e:
                print(f"JSONDecodeError: {json_e} - Server response was not valid JSON.")
                print(f"Raw response text (first 500 chars): {response.text[:500]}")
                return {"error": True, "status_code": response.status_code, "message": "Invalid JSON response from server.", "raw_response": response.text}

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code}")
            error_text = e.response.text
            print(f"Error Response Text: {error_text[:500]}") # Print first 500 chars
            return {"error": True, "status_code": e.response.status_code, "message": error_text}
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            status_code = response.status_code if response is not None else None
            raw_text = response.text if response is not None else None
            return {"error": True, "status_code": status_code, "message": str(e), "raw_response": raw_text}
        finally:
            # Ensure the wrapped file object is closed
            if files:
                 for _, (_, file_obj) in files.items():
                     if hasattr(file_obj, 'close'):
                         file_obj.close()


    def upload_file_streamed(self, file_path, parent_id=None, relative_path=None, progress_callback=None):
        """Upload a file to PrismDrive with real-time progress reporting.

        Args:
            file_path (str): Path to the local file to upload.
            parent_id (int, optional): ID of the parent folder. Defaults to None (root).
            relative_path (str, optional): Relative path within the parent folder (for folder uploads).
            progress_callback (callable, optional): A function to call with (bytes_sent, total_bytes).

        Returns:
            dict: Server response.
        """
        import os
        from pathlib import Path

        endpoint = "/api/v1/uploads"

        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": True, "message": f"File not found: {file_path}"}

        file_name = file_path.name
        file_size = os.path.getsize(file_path)

        print(f"Preparing to upload file: {file_name} ({file_size} bytes) with streaming progress.")

        # Prepare the 'files' dictionary for multipart/form-data
        # The file object will be wrapped by _stream_request if progress_callback is provided
        files = {'file': (file_name, file_path.open('rb'))} # Pass the file object directly

        # Prepare the 'data' dictionary for other form-data fields
        data = {}
        if parent_id is not None:
            data['parentId'] = parent_id
        if relative_path is not None:
            data['relativePath'] = relative_path

        # Headers for the upload request
        headers = {
            'accept': 'application/json',
            # Content-Type: multipart/form-data is automatically set by requests when 'files' is used
            # Authorization header is handled by _update_headers if self.token is present
        }

        try:
            # Use the new _stream_request method
            response = self._stream_request(
                "POST",
                endpoint,
                data=data, # Other form fields
                files=files, # The file part (will be wrapped for progress)
                headers=headers,
                progress_callback=progress_callback # Pass the callback
            )
            return response
        except Exception as e:
            return {"error": True, "message": f"Streaming upload failed: {str(e)}"}
        finally:
             # The file object is closed by the ProgressFile wrapper in _stream_request's finally block
             pass

# Simple wrapper to add progress reporting to a file-like object
class ProgressFile:
    def __init__(self, file_obj, progress_callback):
        self._file_obj = file_obj
        self._progress_callback = progress_callback
        self._bytes_read = 0
        self._total_bytes = os.path.getsize(file_obj.name) # Assuming file_obj has a 'name' attribute

    def read(self, size=-1):
        chunk = self._file_obj.read(size)
        self._bytes_read += len(chunk)
        if self._progress_callback:
            self._progress_callback(self._bytes_read, self._total_bytes)
        return chunk

    def __getattr__(self, attr):
        # Delegate only specific file object attributes/methods required by requests
        if attr in ['read', 'seek', 'tell', 'close', 'name']: # Added 'name' as it's used in __init__
             return getattr(self._file_obj, attr)
        # Raise AttributeError for other attributes to prevent unexpected access
        raise AttributeError(f"'{self.__class__.__name__}' object or its underlying file object has no attribute '{attr}'. This likely indicates an issue in the calling code attempting to access an unexpected attribute on the file object wrapper after the upload.")

    def close(self):
        self._file_obj.close()
        """
        Logs in the user by first hitting /login to get cookies, then POSTing credentials.
        """
        # Manually set activeWorkspaceId cookie before the GET /login - REMOVED as per new findings
        # The domain should match the base_url's domain for the cookie to be sent.
        # try:
        #     parsed_url = urlparse(self.base_url)
        #     cookie_domain = parsed_url.hostname
        #     if cookie_domain:
        #         self.session.cookies.set("activeWorkspaceId", "2170", domain=cookie_domain, path="/")
        #         print(f"DEBUG: Manually set activeWorkspaceId=2170 for domain '{cookie_domain}' in session cookies before GET /login.")
        #     else:
        #         # Fallback or error if hostname can't be parsed, though base_url should always be valid.
        #         print(f"WARNING: Could not parse hostname from base_url '{self.base_url}' to set activeWorkspaceId cookie domain. Cookie might not be set correctly.")
        # except Exception as e:
        #     print(f"ERROR: Exception while trying to set activeWorkspaceId cookie: {e}")

        # --- Step 1: Initial GET Request to /login ---
        login_page_url = f"{self.base_url}/login"
        print(f"DEBUG: Attempting initial GET to: {login_page_url} to establish session and get cookies.")

        get_login_page_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }

        # Temporarily modify session headers for this specific GET request.
        # We need to ensure no 'Authorization' or API-specific 'Accept' headers are sent.
        original_session_headers = self.session.headers.copy()
        self.session.headers.clear() # Clear all current session headers
        self.session.headers.update(get_login_page_headers) # Set specific headers for the GET /login

        try:
            initial_get_response = self.session.get(login_page_url, timeout=15) # Increased timeout slightly
            print(f"DEBUG: Initial GET to {login_page_url} status: {initial_get_response.status_code}.")
            # Cookies are automatically handled by self.session.cookies
            print(f"DEBUG: Cookies in session after GET {login_page_url}: {self.session.cookies.get_dict()}")
        except requests.exceptions.RequestException as e:
            print(f"WARNING: Initial GET to {login_page_url} failed: {e}")
            # Continue anyway, the login POST might still work or provide a more specific error.
        finally:
            # Restore session headers to their previous state (or a known good state for API calls)
            self.session.headers.clear()
            self.session.headers.update(original_session_headers) # Restore what was there before this GET
            # Then, ensure headers are correctly set for subsequent API calls (e.g. if a token was already loaded)
            self._update_headers() # This re-applies CLI User-Agent, API Accept, and Auth if self.token exists.

        # --- Step 2: Prepare Login POST Request Data ---
        login_endpoint = "/auth/login"  # Path relative to base_url
        payload = {
            "email": email,
            "password": password,
            "device_name": device_name
        }

        # --- Step 3: Prepare Login POST Headers ---
        login_specific_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json", # Server expects JSON response for login API
            "Referer": f"{self.base_url}/login",
            "Origin": self.base_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "x-kl-saas-ajax-request": "Ajax_Request" # Added new header
        }
        
        xsrf_token_cookie = self.session.cookies.get('XSRF-TOKEN')
        if xsrf_token_cookie:
            print(f"DEBUG: Found XSRF-TOKEN cookie from session: {xsrf_token_cookie}. Adding X-XSRF-TOKEN header.")
            login_specific_headers['X-XSRF-TOKEN'] = xsrf_token_cookie
        else:
            print("DEBUG: XSRF-TOKEN cookie not found in session. Proceeding without X-XSRF-TOKEN header.")

        # NEW: Explicitly construct and add Cookie header from session cookies
        all_session_cookies = self.session.cookies.get_dict()
        if all_session_cookies:
            cookie_header_value = "; ".join([f"{name}={value}" for name, value in all_session_cookies.items()])
            print(f"DEBUG: Explicitly adding Cookie header: {cookie_header_value}")
            login_specific_headers['Cookie'] = cookie_header_value
        else:
            print("DEBUG: No cookies in session to add to explicit Cookie header for login POST.")

        # --- Step 4: Execute Login POST Request ---
        # The self._request method and the subsequent try/finally block in this login method
        # will handle ensuring no 'Authorization: Bearer' token is sent with this login request.
        
        # Temporarily remove Authorization from session headers if it exists,
        # as _request copies self.session.headers as a base.
        auth_header_backup = self.session.headers.pop('Authorization', None)
        
        response_data = None
        try:
            print(f"DEBUG: Attempting POST to {login_endpoint} with payload: {payload}")
            print(f"DEBUG: Headers for POST {login_endpoint}: {login_specific_headers}")
            print(f"DEBUG: Current session cookies before POST: {self.session.cookies.get_dict()}")
            
            response_data = self._request("POST", login_endpoint, headers=login_specific_headers, json=payload)
        finally:
            # Restore Authorization header to session if it was backed up
            if auth_header_backup:
                self.session.headers['Authorization'] = auth_header_backup
            
            # --- Step 5: Handle Response and Token ---
            # If login was successful, auth.py (or caller) will call self.set_token(), which calls self._update_headers().
            # This will correctly set/update the 'Authorization: Bearer <new_token>' in self.session.headers.
            # If login failed, self.token remains as it was. Calling _update_headers() here ensures
            # the session reflects the state of self.token (either the old one or None).
            self._update_headers() # Ensures session headers are consistent with self.token state.

        return response_data

    def list_entries(self, parent_id=None, per_page=50, deleted_only=None,
                     starred_only=None, recent_only=None, shared_only=None,
                     query=None, entry_type=None, parent_ids=None, page=None, workspace_id=None):
        """
        Get file entries from PrismDrive.
        Maps to GET /api/v1/file-entries endpoint.
        """
        # Correct endpoint based on the provided curl command
        endpoint = "/api/v1/file-entries"
        params = {}
        
        # Parameters based on the provided curl command and swagger
        if per_page is not None:
            params["perPage"] = per_page
        if page is not None:
            params["page"] = page
        
        # Handle parent_id or parent_ids based on how the API expects it
        # The curl command doesn't specify parent_id, so we'll stick to swagger's parentIds if needed
        if parent_ids is not None:
             params["parentIds"] = parent_ids
        # If a single parent_id is needed for listing a folder's contents,
        # we might need to add a specific parameter for that, but for now,
        # the curl command only shows listing all entries with pagination.

        if query is not None:
            params["query"] = query
        if entry_type is not None:
            params["type"] = entry_type
        if deleted_only is not None:
            params["deletedOnly"] = "true" if deleted_only else "false"
        if starred_only is not None:
            params["starredOnly"] = "true" if starred_only else "false"
        if recent_only is not None:
            params["recentOnly"] = "true" if recent_only else "false"
        if shared_only is not None:
            params["sharedOnly"] = "true" if shared_only else "false"
        if workspace_id is not None:
            params["workspaceId"] = workspace_id

        # Headers based on the provided curl command
        headers = {
            'accept': 'application/json',
            # Authorization header is handled by _update_headers if self.token is present
        }

        return self._request("GET", endpoint, params=params, headers=headers)

    def upload_file(self, file_path, parent_id=None, relative_path=None):
        """Upload a file to PrismDrive.

        Args:
            file_path (str): Path to the local file to upload.
            parent_id (int, optional): ID of the parent folder. Defaults to None (root).
            relative_path (str, optional): Relative path within the parent folder (for folder uploads).
        Returns:
            dict: Server response.
        """
        import os
        from pathlib import Path

        # Correct endpoint based on the provided curl command
        endpoint = "/api/v1/uploads"

        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": True, "message": f"File not found: {file_path}"}

        file_name = file_path.name
        file_size = os.path.getsize(file_path)

        print(f"Uploading file: {file_name} ({file_size} bytes)")

        # Use 'files' parameter for multipart/form-data upload
        files = {'file': (file_name, open(file_path, 'rb'))}

        # Use 'data' parameter for other form-data fields
        data = {}
        if parent_id is not None: # Include parentId if provided (can be null)
            data['parentId'] = parent_id
        if relative_path is not None: # Include relativePath if provided
            data['relativePath'] = relative_path
        # If parentId or relativePath are None, they will be omitted from 'data',
        # which matches the curl command where they are not included if empty.

        # Headers based on the provided curl command
        headers = {
            'accept': 'application/json',
            # Authorization header is handled by _update_headers if self.token is present
            # Content-Type: multipart/form-data is automatically set by requests when 'files' is used
        }

        try:
            # Use _request method with files and data
            response = self._request("POST", endpoint, headers=headers, data=data, files=files)
            return response
        except Exception as e:
            return {"error": True, "message": f"Upload failed: {str(e)}"}
        finally:
            # Ensure file is closed
            if 'file' in files and hasattr(files['file'][1], 'close'):
                files['file'][1].close()
