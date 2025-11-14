import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    # Third-party
    "django_distill",
    "leaflet",
    # Local apps
    "listings",
    "transit_layer",
    "education_layer",
    "stores_layer",
    'django_extensions',  # Add this line
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "IstanbulPropTech.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "IstanbulPropTech.wsgi.application"


############ Database: PostGIS

###settings.py
"""DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        # NOTE: You MUST replace the placeholder values below with your actual Supabase data
        "NAME": os.environ.get("POSTGRES_DB", "postgres"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "pOqud40h1ufOgKRf"), # <<< IMPORTANT!
        "HOST": os.environ.get("POSTGRES_HOST", "db.ztwcuqrhvmlfdquanxoc.supabase.co"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
"""
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "istanbul_proptech"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "12345"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Only include app-level static dir if it exists to avoid warnings in export
_candidate_static = BASE_DIR / "static"
STATICFILES_DIRS = [p for p in [_candidate_static] if p.exists()]

# Media files (for uploaded images)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "listings"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Leaflet default configuration (center Kadıköy approx)
LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (40.991, 29.036),
    "DEFAULT_ZOOM": 13,
    "MIN_ZOOM": 3,
    "MAX_ZOOM": 19,
}

# Static export options
# If True, embed simplified GeoJSON into the simplified map template.
SIMPLIFIED_INLINE_DATA = os.environ.get("SIMPLIFIED_INLINE_DATA", "0") == "1"

# Logging Configuration for Debug Statements
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG" if DEBUG else "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "listings": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "transit_layer": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "stores_layer": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Ensure logs directory exists
import os as _os
_logs_dir = BASE_DIR / "logs"
if not _logs_dir.exists():
    _logs_dir.mkdir(exist_ok=True)
