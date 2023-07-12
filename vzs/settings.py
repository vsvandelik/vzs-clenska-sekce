"""
Django settings for vzs project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

import environ
from dateutil.relativedelta import relativedelta

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
    "tempus_dominus",
    # Local apps
    "users.apps.UsersConfig",
    "persons.apps.PersonsConfig",
    "events.apps.EventsConfig",
    "pages.apps.PagesConfig",
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
            ],
        },
    },
]

WSGI_APPLICATION = "vzs.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {"default": env.db()}

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

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "cs"

TIME_ZONE = "Europe/Prague"

USE_I18N = True

USE_TZ = True

# Date and time formats

DATE_INPUT_FORMATS = "%Y-%m-%d"

DATE_FORMAT = "j. n. Y"
DATETIME_FORMAT = "j. n. Y H:i"
TIME_FORMAT = "H:i"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

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

# Settings for Django authenticator

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "pages:home"
LOGOUT_REDIRECT_URL = "users:login"

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

# Emails

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ADMIN_EMAIL = "system@vzs-praha15.cz"

# Settings for Google Integration

GOOGLE_SERVICE_ACCOUNT_FILE = BASE_DIR / "google_integration/service_account_file.json"
GOOGLE_SECRETS_FILE = BASE_DIR / "google_integration/secrets_file.json"
GOOGLE_DOMAIN = env.str("GOOGLE_DOMAIN", default="vzs-praha15.cz")

# Settings for FIO bank

FIO_ACCOUNT_NUMBER = "2601743175"
FIO_BANK_NUMBER = "2010"
FIO_TOKEN = env.str("FIO_TOKEN")

# Settings for Datepicker Tempus Dominus

TEMPUS_DOMINUS_LOCALIZE = True
TEMPUS_DOMINUS_DATE_FORMAT = "DD. MM. YYYY"
TEMPUS_DOMINUS_DATETIME_FORMAT = "DD. MM. YYYY HH:mm"
TEMPUS_DOMINUS_TIME_FORMAT = "HH:mm"

# Transactions settings

VZS_DEFAULT_DUE_DATE = relativedelta(months=1)
