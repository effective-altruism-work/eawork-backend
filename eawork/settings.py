import os.path
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from pathlib import Path

import dj_database_url
import environ
import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.django import DjangoIntegration


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()


class DjangoEnv(Enum):
    LOCAL = "local"
    STAGE = "stage"
    PROD = "prod"
    DOCKER_BUILDER = "docker_builder"


DJANGO_ENV_ENUM = DjangoEnv
DJANGO_ENV = DjangoEnv(env.str("DJANGO_ENV", DjangoEnv.LOCAL.value))
if DJANGO_ENV == DjangoEnv.LOCAL:
    load_dotenv(os.path.join(BASE_DIR, ".env.common"))
    load_dotenv(os.path.join(BASE_DIR, ".env.local"))
    load_dotenv(os.path.join(BASE_DIR, ".env.local.override"))

if DJANGO_ENV in (DjangoEnv.STAGE, DjangoEnv.PROD):
    sentry_sdk.init(
        dsn=env.str(
            "SENTRY_DSN",
            "https://6ee12a58dd8241a7ad70886c32322ea682@o329384.ingest.sentry.io/5948898",
        ),
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACE_SAMPLE_RATE", 1.0),
        send_default_pii=True,
        environment=DJANGO_ENV.value,
    )

SECRET_KEY = env.str("SECRET_KEY", "P(*J)_(WQPL:ZK{_V)CX:P)(UF(WE*FHLSIUDHx7=9bcf2zka1yn#aid#")

DEBUG = env.bool("DJANGO_DEBUG", DJANGO_ENV not in (DjangoEnv.STAGE, DjangoEnv.PROD))

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "host.docker.internal",
        ".localhost",
        "127.0.0.1",
        "[::1]",
        "eawork.org",
    ],
)
RENDER_EXTERNAL_HOSTNAME = env.str("RENDER_EXTERNAL_HOSTNAME", "")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.sites",
    "solo",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework.authtoken",
    "allauth",
    "allauth.account",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "admin_reorder",
    "drf_yasg",
    "import_export",
    "django_select2",
    "django_select2_admin_filters",
    "django_json_widget",
    "auditlog",
    "tinymce",
    "nested_inline",
    "django_object_actions",
    "adminsortable2",
    "adminutils",
    "fieldsignals",
    "corsheaders",
    "anymail",
    "django_jsonform",
    "eawork",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "admin_reorder.middleware.ModelAdminReorder",
]

SITE_ID = 1

ROOT_URLCONF = "eawork.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["eawork/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

POSTGRES_DB_NAME = env.str("POSTGRES_DB_NAME", "db")
POSTGRES_USER = env.str("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD", "")
POSTGRES_PRIMARY_HOST = env.str("POSTGRES_PRIMARY_HOST", "db")
POSTGRES_PORT = env.str("POSTGRES_PORT", "5432")

if DJANGO_ENV == DjangoEnv.DOCKER_BUILDER:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
else:
    DATABASES = {
        "default": {dj_database_url.config(conn_max_age=600)}
    }

RECAPTCHA_V2_SECRET = env.str("RECAPTCHA_V2_SECRET", "6La342IxAcTAAAAAGG-vFI1TnRWx2353jJ4WifJWe")
RECAPTCHA_V3_SECRET = env.str("RECAPTCHA_V3_SECRET", "6LfJE3AAAAAO-rrTo4636491ZMRh234eL7")

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static_collected")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"

if env.str("AWS_STORAGE_BUCKET_NAME", ""):
    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_VERIFY = True
    AWS_QUERYSTRING_AUTH = False
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_CUSTOM_DOMAIN = env.str("AWS_CLOUDFRONT_DEFAULT_DOMAIN", "public.eawork.org")
    if DJANGO_ENV == DjangoEnv.PROD:
        AWS_LOCATION = f"eawork-backend-{DJANGO_ENV.value}/"
    else:
        AWS_LOCATION = f"eawork-backend-{DjangoEnv.STAGE.value}/"
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

SELECT2_CACHE_BACKEND = "select2"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "TIMEOUT": 60 * 60 * 24,
    },
    SELECT2_CACHE_BACKEND: {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_select2_cache",
        "TIMEOUT": 60 * 60 * 2,
    },
}

AUTH_USER_MODEL = "eawork.User"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = f"account/review"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = (
    ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL
)
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "VERIFIED_EMAIL": True,
    }
}
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 7
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
if DJANGO_ENV == DjangoEnv.PROD or DJANGO_ENV == DjangoEnv.STAGE:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# removes frustrating validations, eg `too similar to your email`
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 1,
        },
    },
]
DEFAULT_FROM_EMAIL = "support@eawork.org"
DEFAULT_BCC_ADDRESSES = ["bcc@eawork.org"] if DJANGO_ENV == DjangoEnv.PROD else []

if DJANGO_ENV == DjangoEnv.PROD:
    # In production, send emails using Mailgun.
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "django@eawork.org")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "")
    EMAIL_HOST = env.str("EMAIL_HOST", "smtp.mailgun.org")
    EMAIL_PORT = env.int("EMAIL_PORT", 587)
    EMAIL_USE_TLS = True
else:
    # In other environments (development, staging, etc.) send them to Mailtrap.
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.mailtrap.io"
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "rgsegsd")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "ergsdfgsfg")
    EMAIL_PORT = "2525"

ANYMAIL = {
    "MAILGUN_API_KEY": env.str(
        "MAILGUN_API_KEY", "8a571fb2f15ab1449f4b81eedce25822-16ffd509-45f56420"
    ),
    "MAILGUN_SENDER_DOMAIN": env.str(
        "MAIL_DOMAIN", "sandboxe1fddd2132d34b3998bdec51993a835c.mailgun.org"
    ),
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
REST_USE_JWT = True


ADMIN_REORDER = [
    {
        "label": "Users",
        "app": "auth",
        "models": [
            "eawork.User",
            "account.EmailAddress",
            "auth.Group",
            "socialaccount.SocialApp",
        ],
    },
    "eawork",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
