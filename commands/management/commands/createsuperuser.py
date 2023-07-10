from persons.models import Person
from users.models import UserManager

from django.db import DEFAULT_DB_ALIAS
from django.apps import apps as django_apps
from django.contrib.auth.management.commands.createsuperuser import (
    Command as CreateSuperuserCommand,
    PASSWORD_FIELD,
    NotRunningInTTYException,
)
from django.core import exceptions


class Command(CreateSuperuserCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PersonModel = django_apps.get_model("persons.Person", require_ready=False)

        self.models = [
            (self.UserModel, ["password"]),
            (
                self.PersonModel,
                ["email", "first_name", "last_name", "sex", "person_type"],
            ),
        ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is "default".',
        )

        for model, model_fields in self.models:
            for field_name in model_fields:
                if field_name == "person":
                    continue

                field = model._meta.get_field(field_name)
                if field.many_to_many:
                    if (
                        field.remote_field.through
                        and not field.remote_field.through._meta.auto_created
                    ):
                        raise CommandError(
                            "Required field '%s' specifies a many-to-many "
                            "relation through model, which is not supported."
                            % field_name
                        )
                    else:
                        parser.add_argument(
                            "--%s" % field_name,
                            action="append",
                            help=(
                                "Specifies the %s for the superuser. Can be used "
                                "multiple times." % field_name,
                            ),
                        )
                else:
                    parser.add_argument(
                        "--%s" % field_name,
                        help="Specifies the %s for the superuser." % field_name,
                    )

    def _handle_model_fields(self):
        for model, model_fields in self.models:
            for field_name in model_fields:
                field = self.UserModel._meta.get_field(field_name)
                user_data[field_name] = options[field_name]
                if user_data[field_name] is not None:
                    user_data[field_name] = field.clean(user_data[field_name], None)
                while user_data[field_name] is None:
                    message = self._get_input_message(field)
                    input_value = self.get_input_data(field, message)
                    user_data[field_name] = input_value
                    if field.many_to_many and input_value:
                        if not input_value.strip():
                            user_data[field_name] = None
                            self.stderr.write("Error: This field cannot be blank.")
                            continue
                        user_data[field_name] = [
                            pk.strip() for pk in input_value.split(",")
                        ]

                if not field.many_to_many:
                    fake_user_data[field_name] = user_data[field_name]
                # Wrap any foreign keys in fake model instances.
                if field.many_to_one:
                    fake_user_data[field_name] = field.remote_field.model(
                        user_data[field_name]
                    )

    def handle(self, *args, **options):
        database = options["database"]
        user_data = {}
        try:
            self.UserModel._meta.get_field(PASSWORD_FIELD)
        except exceptions.FieldDoesNotExist:
            pass
        else:
            # If not provided, create the user with an unusable password.
            user_data[PASSWORD_FIELD] = None
        try:
            fake_user_data = {}
            if hasattr(self.stdin, "isatty") and not self.stdin.isatty():
                raise NotRunningInTTYException

            for model, model_fields in self.models:
                for field_name in model_fields:
                    field = model._meta.get_field(field_name)
                    user_data[field_name] = options[field_name]
                    if user_data[field_name] is not None:
                        user_data[field_name] = field.clean(user_data[field_name], None)
                    while user_data[field_name] is None:
                        message = self._get_input_message(field)
                        input_value = self.get_input_data(field, message)
                        user_data[field_name] = input_value
                        if field.many_to_many and input_value:
                            if not input_value.strip():
                                user_data[field_name] = None
                                self.stderr.write("Error: This field cannot be blank.")
                                continue
                            user_data[field_name] = [
                                pk.strip() for pk in input_value.split(",")
                            ]

                    if not field.many_to_many:
                        fake_user_data[field_name] = user_data[field_name]
                    # Wrap any foreign keys in fake model instances.
                    if field.many_to_one:
                        fake_user_data[field_name] = field.remote_field.model(
                            user_data[field_name]
                        )

                # Prompt for a password if the model has one.
                while PASSWORD_FIELD in user_data and user_data[PASSWORD_FIELD] is None:
                    password = getpass.getpass()
                    password2 = getpass.getpass("Password (again): ")
                    if password != password2:
                        self.stderr.write("Error: Your passwords didn't match.")
                        # Don't validate passwords that don't match.
                        continue
                    if password.strip() == "":
                        self.stderr.write("Error: Blank passwords aren't allowed.")
                        # Don't validate blank passwords.
                        continue
                    try:
                        validate_password(password2, self.UserModel(**fake_user_data))
                    except exceptions.ValidationError as err:
                        self.stderr.write("\n".join(err.messages))
                        response = input(
                            "Bypass password validation and create user anyway? [y/N]: "
                        )
                        if response.lower() != "y":
                            continue
                    user_data[PASSWORD_FIELD] = password

            self.UserModel._default_manager.db_manager(database).create_superuser(
                **user_data
            )

            if options["verbosity"] >= 1:
                self.stdout.write("Superuser created successfully.")
        except KeyboardInterrupt:
            self.stderr.write("\nOperation cancelled.")
            sys.exit(1)
        except exceptions.ValidationError as e:
            raise CommandError("; ".join(e.messages))
        except NotRunningInTTYException:
            self.stdout.write(
                "Superuser creation skipped due to not running in a TTY. "
                "You can run `manage.py createsuperuser` in your project "
                "to create one manually."
            )
