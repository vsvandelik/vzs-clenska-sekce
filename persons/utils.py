from google_integration import google_directory
from persons.models import Person


def sync_single_group_with_google(local_group):
    google_email = local_group.google_email

    local_emails = {p.email for p in local_group.members.all()}
    google_emails = {
        m["email"] for m in google_directory.get_group_members(google_email)
    }

    if not local_group.google_as_members_authority:
        members_to_add = local_emails - google_emails
        members_to_remove = google_emails - local_emails

        for email in members_to_add:
            google_directory.add_member_to_group(email, google_email)

        for email in members_to_remove:
            google_directory.remove_member_from_group(email, google_email)

    else:
        members_to_add = google_emails - local_emails
        members_to_remove = local_emails - google_emails

        for email in members_to_add:
            try:
                local_person = Person.objects.get(email=email)
                local_group.members.add(local_person)
            except Person.DoesNotExist:
                pass

        for email in members_to_remove:
            local_group.members.remove(Person.objects.get(email=email))