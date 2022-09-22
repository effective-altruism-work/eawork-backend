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
            "https://23439f9b986c4be68697d4b11da25235@o1376636.ingest.sentry.io/6690029",
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
        "backend.eawork.org",
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
    "django_filters",
    "algoliasearch_django",
    "eawork",
    "eawork.apps.job_alerts",
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

# CORS is required by all browsers, but only needed for cookie auth, hence useless for our API
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r"^/api/.*$"

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

if DJANGO_ENV == DjangoEnv.DOCKER_BUILDER:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
else:
    DATABASES = {"default": dj_database_url.config(conn_max_age=600)}

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
    MEDIA_ROOT = env.str("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

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
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", "team@80000hours.org")
ADMINS = [("Victor", DEFAULT_FROM_EMAIL)]
SERVER_EMAIL = DEFAULT_FROM_EMAIL
DEFAULT_BCC_ADDRESSES = ["bcc@80000hours.org"] if DJANGO_ENV == DjangoEnv.PROD else []

# if DJANGO_ENV == DjangoEnv.PROD:
EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"
EMAIL_USE_TLS = True

ANYMAIL = {
    "POSTMARK_SERVER_TOKEN": env.str("POSTMARK_SERVER_TOKEN", "stub"),
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
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
        ],
    },
    {
        "label": "Jobs",
        "app": "eawork",
        "models": [
            {"model": "eawork.JobAlert", "label": "Email alerts"},
            {"model": "eawork.JobPost", "label": "Posts"},
            {"model": "eawork.JobPostVersion", "label": "Post versions"},
            {"model": "eawork.Comment", "label": "Post comments"},
            {"model": "eawork.Company", "label": "Companies"},
        ],
    },
    {
        "label": "Tags",
        "app": "eawork",
        "models": [
            {"model": "eawork.JobPostTag", "label": "Tags"},
            {"model": "eawork.JobPostTagType", "label": "Tag types"},
        ],
    },
    {
        "app": "eawork",
        "label": "Admin",
        "models": [
            "sites.Site",
            "auditlog.LogEntry",
            "socialaccount.SocialApp",
        ],
    },
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

FRONTEND_URL = "https://jobs.80000hours.org"
BASE_URL = "https://backend.eawork.org"

IS_ENABLE_ALGOLIA = env.bool("IS_ENABLE_ALGOLIA", default=False)
ALGOLIA = {
    "APPLICATION_ID": env.str("ALGOLIA_APPLICATION_ID", default="S2T38ZKE0P"),
    "API_KEY": env.str("ALGOLIA_API_KEY", default="d1c9139b2271e35f44a29b12dddb4b06"),
    "API_KEY_READ_ONLY": env.str(
        "API_KEY_READ_ONLY", default="b0e9cd27b37d64ac5bbb0b0671e1e84b"
    ),
    "INDEX_NAME_JOBS": env.str(
        "ALGOLIA_INDEX_NAME_JOBS",
        default="jobs_prod",
    ),
    "INDEX_NAME_TAGS": env.str(
        "ALGOLIA_INDEX_NAME_TAGS",
        default="tags_prod",
    ),
}
