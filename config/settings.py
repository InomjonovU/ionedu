"""
Django settings for config project.
"""

from pathlib import Path
from django.urls import reverse_lazy
from django.templatetags.static import static
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-_dr*x4+#-xqt3*uiyuqgscr8k!ppu6ozzb)u0ya%r#&*y^#3^s'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    # Unfold birinchi bo‘lishi shart
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.import_export',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'front',
    'teacher'
]

# UNFOLD SETTINGS
UNFOLD = {
    "SITE_TITLE": "ION EDU",
    "SITE_HEADER": "ION EDU Administration",
    "SITE_URL": "/",

    # ❌ Home page logosi olib tashlandi
    "SITE_ICON": {},

    "SITE_SYMBOL": "school",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,

    "THEME": "light",

    # Primary rang palitrasi (#00FF9C)
    "COLORS": {
        "primary": {
            "50": "230 255 242",
            "100": "204 255 229",
            "200": "153 255 204",
            "300": "102 255 179",
            "400": "51 255 153",
            "500": "0 255 156",   # Asosiy rang
            "600": "0 204 125",
            "700": "0 153 94",
            "800": "0 102 63",
            "900": "0 51 32",
            "950": "0 26 16",
        },
    },

    # Extensions
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "uz": "🇺🇿",
                "ru": "🇷🇺",
            },
        },
    },

    # Sidebar
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": False,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": lambda request: reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "User Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": lambda request: reverse_lazy("admin:front_customuser_changelist"),
                    },
                    {
                        "title": "Teacher Requests",
                        "icon": "school",
                        "link": lambda request: reverse_lazy("admin:front_requesttobecometeacher_changelist"),
                        # ❗ Badge admin.py ichida qo‘shiladi
                    },
                ],
            },
            {
                "title": "Courses",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "All Courses",
                        "icon": "book",
                        "link": lambda request: reverse_lazy("admin:front_course_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": lambda request: reverse_lazy("admin:front_coursecategory_changelist"),
                    },
                    {
                        "title": "Lessons",
                        "icon": "menu_book",
                        "link": lambda request: reverse_lazy("admin:front_lesson_changelist"),
                    },
                    {
                        "title": "Join Requests",
                        "icon": "person_add",
                        "link": lambda request: reverse_lazy("admin:front_requesttojoincourse_changelist"),
                        # ❗ Badge admin.py ichida qo‘shiladi
                    },
                ],
            },
        ],
    },

    # Tabs
    "TABS": [
        {
            "models": ["front.course"],
            "items": [
                {
                    "title": "General",
                    "link": lambda request, object_id=None: (
                        reverse_lazy("admin:front_course_change", args=[object_id])
                        if object_id else None
                    ),
                },
                {
                    "title": "Lessons",
                    "link": lambda request, object_id=None: (
                        reverse_lazy("admin:front_lesson_changelist") + f"?course__id__exact={object_id}"
                        if object_id else None
                    ),
                },
                {
                    "title": "Tests",
                    "link": lambda request, object_id=None: (
                        reverse_lazy("admin:front_coursetest_changelist") + f"?course__id__exact={object_id}"
                        if object_id else None
                    ),
                },
                {
                    "title": "Students",
                    "link": lambda request, object_id=None: (
                        reverse_lazy("admin:front_coursestudent_changelist") + f"?course__id__exact={object_id}"
                        if object_id else None
                    ),
                },
            ],
        },
    ],
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

AUTH_USER_MODEL = 'front.CustomUser'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ionedu',
        'USER': 'postgres',
        'PASSWORD': '2008',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static Files (optional, for production)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_PRESENTATION_EXTENSIONS = ['.pdf', '.ppt', '.pptx']