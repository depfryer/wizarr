from typing import Optional

from pydantic import HttpUrl
from requests import RequestException, get, post, delete
from logging import info
from io import BytesIO

from .invitation import get_invitation
from .libraries import get_libraries_ids
from .settings import get_settings
from .users import get_users, create_user, get_user_by_token

from models.jellyfin.user import JellyfinUser
from models.jellyfin.user_policy import JellyfinUserPolicy
from models.jellyfin.library import JellyfinLibraryItem

# INDEX OF FUNCTIONS
# - Jellyfin Get Request
# - Jellyfin Post Request
# - Jellyfin Delete Request
# - Jellyfin Scan Libraries
# - Jellyfin Get Policy
# - Jellyfin Invite User
# - Jellyfin Get Users
# - Jellyfin Get User
# - Jellyfin Delete User
# - Jellyfin Sync Users


# ANCHOR - Jellyfin Get Request
def get_jellyfin(api_path: str, as_json: Optional[bool] = True, server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None):
    """Get data from Jellyfin.
    :param api_path: API path to get data from
    :type api_path: str

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: Jellyfin API response
    """

    # Get required settings
    if not server_api_key or not server_url:
        settings = get_settings(["server_api_key", "server_url"])
        server_url = server_url or settings.get("server_url", None)
        server_api_key = server_api_key or settings.get("server_api_key", None)

    # If server_url does not end with a slash, add one
    if not server_url.__str__().endswith("/"):
        server_url = server_url.__str__() + "/"

    # If api_path starts with a slash, remove it
    if api_path.startswith("/"):
        api_path = api_path[1:]

    # Add api_path to Jellyfin URL
    api_url = str(server_url) + api_path

    # Set headers for Jellyfin API
    headers = {
        "X-Emby-Token": server_api_key,
        "Accept": "application/json, profile=\"PascalCase\""
    }

    # Get data from Jellyfin
    response = get(url=api_url, headers=headers, timeout=30)

    # Raise exception if Jellyfin API returns non-200 status code
    if response.status_code != 200:
        raise RequestException(
            f"Jellyfin API returned {response.status_code} status code."
        )

    # Return response
    if as_json:
        return response.json()
    else:
        return response


# ANCHOR - Jellyfin Post Request
def post_jellyfin(api_path: str, server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None, data: Optional[dict] = None) -> dict:
    """Post data to Jellyfin.
    :param api_path: API path to post data to
    :type api_path: str

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :param data: Data to post to Jellyfin
    :type data: Optional[dict]

    :return: Jellyfin API response
    """

    # Get required settings
    if not server_api_key or not server_url:
        settings = get_settings(["server_api_key", "server_url"])
        server_url = server_url or settings.get("server_url", None)
        server_api_key = server_api_key or settings.get("server_api_key", None)

    # Add api_path to Jellyfin URL
    api_url = str(server_url) + api_path

    # Set headers for Jellyfin API
    headers = {
        "X-Emby-Token": server_api_key,
        "Accept": "application/json, profile=\"PascalCase\""
    }

    # Post data to Jellyfin
    response = post(url=api_url, headers=headers, data=data, timeout=30)

    # Raise exception if Jellyfin API returns non-200 status code
    if response.status_code != 200:
        raise RequestException(
            f"Jellyfin API returned {response.status_code} status code."
        )

    response.raise_for_status()

    return response.json()


# ANCHOR - Jellyfin Delete Request
def delete_jellyfin(api_path: str, server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None) -> None:
    """Delete data from Jellyfin.
    :param api_path: API path to delete data from
    :type api_path: str

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: None
    """

    # Get required settings
    if not server_api_key or not server_url:
        settings = get_settings(["server_api_key", "server_url"])
        server_url = server_url or settings.get("server_url", None)
        server_api_key = server_api_key or settings.get("server_api_key", None)

    # Add api_path to Jellyfin URL
    api_url = str(server_url) + api_path

    # Set headers for Jellyfin API
    headers = {
        "X-Emby-Token": server_api_key,
        "Accept": "application/json, profile=\"PascalCase\""
    }

    # Delete data from Jellyfin
    response = delete(url=api_url, headers=headers, timeout=30)

    # Raise exception if Jellyfin API returns non-200 status code
    if response.status_code != 200:
        raise RequestException(
            f"Jellyfin API returned {response.status_code} status code."
        )

    return response.json()


# ANCHOR - Jellyfin Scan Libraries
def scan_jellyfin_libraries(server_api_key: Optional[str], server_url: Optional[str or HttpUrl]) -> list[JellyfinLibraryItem]:
    """Scan Jellyfin libraries and return list of libraries.
    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: List of libraries
    """

    # Get libraries from Jellyfin
    response = get_jellyfin(
        api_path="/Library/MediaFolders", server_api_key=server_api_key, server_url=server_url
    )

    # Check if items exist
    if response["Items"] is None:
        raise ValueError("No libraries found.")

    # Return list of libraries
    return response["Items"]


# ANCHOR - Jellyfin Get Policy
def get_jellyfin_policy(user_id: str, server_api_key: Optional[str], server_url: Optional[str or HttpUrl]) -> JellyfinUserPolicy:
    """Get policy from Jellyfin.

    :param user_id: ID of the user to get policy for
    :type user_id: str

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: Jellyfin API response
    """

    # Get user from Jellyfin
    response = get_jellyfin(
        api_path=f"/Users/{user_id}", server_api_key=server_api_key, server_url=server_url
    )

    # Check if user has a policy
    if response["Policy"] is None:
        raise ValueError("User does not have a policy.")

    return response["Policy"]


# ANCHOR - Jellyfin Invite User
def invite_jellyfin_user(username: str, password: str, code: str, email: str) -> JellyfinUser:
    """Invite user to Jellyfin.

    :param username: Username of the user to invite
    :type username: str

    :param password: Password of the user to invite
    :type password: str

    :param code: Invitation code
    :type code: str

    :param email: Email of the user to invite
    :type email: str

    :return: Jellyfin API response
    """

    # Validate user input
    if not username or not password or not code or not email:
        raise ValueError("Missing required user input.")

    # Get Invitation from Database
    invitation = get_invitation(code=code)

    # Get libraries from invitation
    sections = (
        get_libraries_ids()
        if invitation.specific_libraries is None
        else invitation.specific_libraries.split(",")
    )

    # Create user object
    new_user = { "Name": str(username), "Password": str(password) }

    # Create user in Jellyfin
    response = post_jellyfin(api_path="/Users/New", data=new_user)

    # Create policy object
    new_policy = { "EnableAllFolders": False, "EnabledFolders": sections }

    # Merge policy with user policy
    new_policy.update(response["Policy"])

    # Update user policy
    response = post_jellyfin(api_path=f"/Users/{response['Id']}/Policy", data=new_policy)

    # Return response
    return response


# ANCHOR - Jellyfin Get Users
def get_jellyfin_users(server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None) -> list[JellyfinUser]:
    """Get users from Jellyfin.

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: Jellyfin API response
    """

    # Get users from Jellyfin
    response = get_jellyfin(api_path="/Users", server_api_key=server_api_key, server_url=server_url)

    # Return users
    return response


# ANCHOR - Jellyfin Get User
def get_jellyfin_user(user_id: str, server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None) -> JellyfinUser:
    """Get user from Jellyfin.

    :param user_id: ID of the user to get
    :type user_id: str

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: Jellyfin API response
    """

    # Get user from Jellyfin
    response = get_jellyfin(api_path=f"/Users/{user_id}", server_api_key=server_api_key, server_url=server_url)

    # Return user
    return response


# ANCHOR - Jellyfin Delete User
def delete_jellyfin_user(user_id: str, server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None) -> None:
    """Delete user from Jellyfin.
    :param user_id: ID of the user to delete
    :type user_id: str

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: None
    """

    # Delete user from Jellyfin
    delete_jellyfin(api_path=f"/Users/{user_id}/Delete", server_api_key=server_api_key, server_url=server_url)


# ANCHOR - Jellyfin Sync Users
def sync_jellyfin_users(server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None) -> list[JellyfinUser]:
    """Sync users from Jellyfin to database.

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: None
    """

    # Get users from Jellyfin
    jellyfin_users = get_jellyfin_users(server_api_key=server_api_key, server_url=server_url)


    # Get users from database
    database_users = get_users(False)

    # If jellyfin_users.id not in database_users.token, add to database
    for jellyfin_user in jellyfin_users:
        if jellyfin_user["Id"] not in [database_user.token for database_user in database_users]:
            create_user(username=jellyfin_user["Name"], token=jellyfin_user["Id"])
            info(f"User {jellyfin_user['Name']} successfully imported to database.")

    # If database_users.token not in jellyfin_users.id, delete from database
    for database_user in database_users:
        if database_user.token not in [jellyfin_user["Id"] for jellyfin_user in jellyfin_users]:
            database_user.delete_instance()
            info(f"User {database_user.username} successfully deleted from database.")

    # Return users
    return get_jellyfin_users(server_api_key=server_api_key, server_url=server_url)


# ANCHOR - Jellyfin Get Profile Picture
def get_jellyfin_profile_picture(user_id: str, max_height: Optional[int] = 150, max_width: Optional[int] = 150, quality: Optional[int] = 30, server_api_key: Optional[str] = None, server_url: Optional[str or HttpUrl] = None):
    """Get profile picture from Jellyfin.

    :param user_id: ID of the user to get profile picture for
    :type user_id: str

    :param username: Username for backup profile picture using ui-avatars.com
    :type username: str

    :param max_height: Maximum height of profile picture
    :type max_height: Optional[int] - Default: 150

    :param max_width: Maximum width of profile picture
    :type max_width: Optional[int] - Default: 150

    :param quality: Quality of profile picture
    :type quality: Optional[int] - Default: 30

    :param server_api_key: Jellyfin API key
    :type server_api_key: Optional[str] - If not provided, will get from database.

    :param server_url: Jellyfin URL
    :type server_url: Optional[str or HttpUrl] - If not provided, will get from database.

    :return: Jellyfin API response
    """

    # Response object
    response = None

    try:
        # Get profile picture from Jellyfin
        response = get_jellyfin(api_path=f"/Users/{user_id}/Images/Primary?maxHeight={max_height}&maxWidth={max_width}&quality={quality}", as_json=False, server_api_key=server_api_key, server_url=server_url)
    except RequestException:
        # Backup profile picture using ui-avatars.com if Jellyfin fails
        user = get_user_by_token(user_id, verify=False)
        username = f"{user.username}&length=1" if user else "ERROR&length=60&font-size=0.28"
        response = get(url=f"https://ui-avatars.com/api/?uppercase=true&name={username}", timeout=30)

    # Raise exception if either Jellyfin or ui-avatars.com fails
    if response.status_code != 200:
        raise RequestException("Failed to get profile picture.")

    # Extract image from response
    image = response.content

    # Convert image bytes to read image
    image = BytesIO(image)

    # Return profile picture
    return image