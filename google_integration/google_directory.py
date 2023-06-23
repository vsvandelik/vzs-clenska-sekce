"""
TUTORIAL HOW TO MAKE ENABLE GOOGLE ADMIN SDK

1. On Google Cloud Platform enable Google Admin SDK.
2. Create new service account in GCP.
3. Download a credentials json file to this folder.
4. In Google Workplace Admin add created service account as an admin for managing users and groups.

"""


from google.oauth2 import service_account
from googleapiclient.discovery import build

from vzs import settings

USER_SCOPE = "https://www.googleapis.com/auth/admin.directory.user"
GROUP_SCOPE = "https://www.googleapis.com/auth/admin.directory.group"
GROUP_MEMBERS_SCOPE = "https://www.googleapis.com/auth/admin.directory.group.member"


def _get_service(scopes):
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    return build("admin", "directory_v1", credentials=credentials)


def get_list_of_users():
    service = _get_service([USER_SCOPE])
    users_list = []
    page_token = None

    while True:
        results = (
            service.users()
            .list(domain=settings.GOOGLE_DOMAIN, pageToken=page_token)
            .execute()
        )

        for user in results.get("users", []):
            users_list.append(
                {
                    "id": user.get("id"),
                    "email": user.get("primaryEmail"),
                    "name": user.get("name")["fullName"],
                }
            )

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return users_list


def get_list_of_groups():
    service = _get_service([GROUP_SCOPE])
    groups_lists = []
    page_token = None

    while True:
        results = (
            service.groups()
            .list(domain=settings.GOOGLE_DOMAIN, pageToken=page_token)
            .execute()
        )

        for group in results.get("groups", []):
            groups_lists.append(
                {
                    "id": group.get("id"),
                    "email": group.get("email"),
                    "name": group.get("name"),
                }
            )

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return groups_lists


def get_group_members(group_email):
    service = _get_service([GROUP_MEMBERS_SCOPE])
    members_list = []
    page_token = None

    while True:
        results = (
            service.members().list(groupKey=group_email, pageToken=page_token).execute()
        )

        for member in results.get("members", []):
            members_list.append(
                {
                    "id": member.get("id"),
                    "email": member.get("email"),
                    "role": member.get("role"),
                    "type": member.get("type"),
                }
            )

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return members_list


def add_member_to_group(member_email, group_email):
    service = _get_service([GROUP_MEMBERS_SCOPE])

    member_body = {"email": member_email, "role": "MEMBER"}

    try:
        service.members().insert(groupKey=group_email, body=member_body).execute()
    except Exception:
        pass


def remove_member_from_group(member_email, group_email):
    service = _get_service([GROUP_MEMBERS_SCOPE])

    try:
        service.members().delete(groupKey=group_email, memberKey=member_email).execute()
    except Exception:
        pass
