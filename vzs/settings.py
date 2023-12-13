"""
Django settings for vzs project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from datetime import datetime
from pathlib import Path

import environ
from dateutil.relativedelta import relativedelta
from django.conf.locale.cs import formats as cs_formats
from django.utils.timezone import make_aware, now

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Application definition

INSTALLED_APPS = [
    "overridden_django_commands",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Extensions
    "macros",
    "active_link",
    "crispy_forms",
    "crispy_bootstrap4",
    "widget_tweaks",
    "tinymce",
    "django_select2",
    "mptt",
    "tempus_dominus",
    "rest_framework",
    "django_crontab",
    # Local apps
    "users.apps.UsersConfig",
    "persons.apps.PersonsConfig",
    "events.apps.EventsConfig",
    "one_time_events.apps.OneTimeEventsConfig",
    "trainings.apps.TrainingsConfig",
    "positions.apps.PositionsConfig",
    "pages.apps.PagesConfig",
    "transactions.apps.TransactionsConfig",
    "features.apps.FeaturesConfig",
    "groups.apps.GroupsConfig",
    "api.apps.APIConfig",
    # Template tags
    "vzs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "users.middleware.ActivePersonMiddleware",
    "users.middleware.LogoutRememberMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "vzs.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "users.context_processors.active_person",
                "users.context_processors.logout_remember",
            ],
        },
    },
]

WSGI_APPLICATION = "vzs.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = (
    "users.backends.PasswordBackend",
    "users.backends.GoogleBackend",
)

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "users.validators.MinimumNumericValidator",
    },
    {
        "NAME": "users.validators.MinimumCapitalValidator",
    },
]

# Encoding
DEFAULT_CHARSET = "UTF-8"

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "cs"

TIME_ZONE = "Europe/Prague"

USE_I18N = True

USE_TZ = True

# Date and time formats
cs_formats.DATE_FORMAT = "j. n. Y"
cs_formats.DATETIME_FORMAT = "j. n. Y H:i"
cs_formats.TIME_FORMAT = "H:i"

DATETIME_PRECISE_FORMAT = "j. n. Y H:i:s"

current_datime_from_env = os.environ.get("CURRENT_DATETIME")
if current_datime_from_env:
    _CURRENT_DATETIME = make_aware(
        datetime.fromisoformat(current_datime_from_env.strip())
    )

    def CURRENT_DATETIME():
        return _CURRENT_DATETIME

else:

    def CURRENT_DATETIME():
        return now()


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = env.str("STATIC_ROOT", default=BASE_DIR / "staticfiles")

STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "node_modules",
]

# TinyMCE

TINYMCE_DEFAULT_CONFIG = {
    "menubar": "file edit view insert format tools table help",
    "plugins": "advlist autolink lists link image charmap preview anchor searchreplace  code "
    "fullscreen  media table paste code help wordcount spellchecker",
    "toolbar": "undo redo | bold italic underline strikethrough | fontsizeselect formatselect | alignleft "
    "aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor "
    "backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | "
    "insertfile image media pageembed template link anchor codesample | "
    "a11ycheck ltr rtl",
    "custom_undo_redo_levels": 10,
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Settings for app django-active-link

ACTIVE_LINK_STRICT = True

# Settings for authentication

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "pages:home"
LOGOUT_REDIRECT_URL = "users:login"
RESET_PASSWORD_TOKEN_TTL_HOURS = 24

# Settings for CrispyForms

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Settings for message type level

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: "primary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

SERVER_DOMAIN = env.str("SERVER_DOMAIN", default="localhost:8000")
SERVER_PROTOCOL = env.str("SERVER_PROTOCOL", default="http")

# Emails

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ADMIN_EMAIL = "system@vzs-praha15.cz"

# Settings for Google Integration

GOOGLE_SERVICE_ACCOUNT_PATH = BASE_DIR / "google_integration/service_account_file.json"
GOOGLE_SECRETS_FILE = BASE_DIR / "google_integration/secrets_file.json"
GOOGLE_DOMAIN = env.str("GOOGLE_DOMAIN", default="vzs-praha15.cz")
GOOGLE_MAPS_API_KEY = env.str("GOOGLE_MAPS_API_KEY", default=None)

# Settings for FIO bank

FIO_ACCOUNT_NUMBER = "2601743175"
FIO_BANK_NUMBER = "2010"
FIO_TOKEN = env.str("FIO_TOKEN")

FIO_ACCOUNT_PRETTY = FIO_ACCOUNT_NUMBER + "/" + FIO_BANK_NUMBER

# Settings for Datepicker Tempus Dominus

TEMPUS_DOMINUS_LOCALIZE = True
TEMPUS_DOMINUS_DATE_FORMAT = "D. M. YYYY"
TEMPUS_DOMINUS_DATETIME_FORMAT = "D. M. YYYY HH:mm"
TEMPUS_DOMINUS_TIME_FORMAT = "HH:mm"

# Transactions settings

VZS_DEFAULT_DUE_DATE = relativedelta(months=1)

# Settings for Select2

SELECT2_CSS = ["/static/select2/dist/css/select2.min.css"]
SELECT2_JS = ["/static/select2/dist/js/select2.min.js"]
SELECT2_I18N_PATH = "/static/select2/dist/js/i18n"

# Constants
VALUE_MISSING_HTML = '<i class="fas fa-times"></i>'
VALUE_PRESENT_HTML = '<i class="fas fa-check"></i>'
ORGANIZER_UNENROLL_DEADLINE_DAYS = 21
ORGANIZER_ENROLL_DEADLINE_DAYS = 1
ORGANIZER_EXCUSE_DEADLINE_DAYS = 21
PARTICIPANT_EXCUSE_DEADLINE_DAYS = 21
PARTICIPANT_UNENROLL_DEADLINE_DAYS = 21
PARTICIPANT_ENROLL_DEADLINE_DAYS = 1
NOTIFICATION_SENDER_EMAIL = "noreply@vzs-praha15.cz"
MIN_PARTICIPANT_ABSENCE_SEND_MAIL = 3
FEATURE_EXPIRE_HOURS_SEND_MAIL = 72

# REST
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ]
}

# CRONTAB
CRONJOBS = [("0 3 * * *", "features.cron.features_expiry_send_mails")]
