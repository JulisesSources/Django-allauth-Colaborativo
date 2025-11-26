"""
Django settings for SCA-B123 project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================
# SECURITY SETTINGS
# ==================================

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')


# ==================================
# APPLICATION DEFINITION
# ==================================

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requerido para allauth
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Local apps
    'apps.trabajadores',
    'apps.unidades',
    'apps.jornadas_laborales',
    'apps.asistencias',
    'apps.incidencias',
    'apps.accounts',
    'apps.reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Requerido para allauth
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Requerido por allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ==================================
# DATABASE
# ==================================

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}


# ==================================
# AUTHENTICATION
# ==================================

AUTHENTICATION_BACKENDS = [
    # Django backend
    'django.contrib.auth.backends.ModelBackend',
    # Allauth backend
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==================================
# ALLAUTH CONFIGURATION
# ==================================


# Configuración de autenticación
ACCOUNT_AUTHENTICATION_METHOD = config('ACCOUNT_AUTHENTICATION_METHOD', default='username_email')
ACCOUNT_EMAIL_REQUIRED = config('ACCOUNT_EMAIL_REQUIRED', default=True, cast=bool)
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default='mandatory')
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = config('ACCOUNT_LOGIN_ATTEMPTS_LIMIT', default=5, cast=int)
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = config('ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT', default=300, cast=int)

# Redirecciones
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'


# ==================================
# EMAIL CONFIGURATION
# ==================================

EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Email por defecto para el sistema
DEFAULT_FROM_EMAIL = 'noreply@sca-b123.com'


# ==================================
# INTERNATIONALIZATION
# ==================================

LANGUAGE_CODE = config('LANGUAGE_CODE', default='es-mx')
TIME_ZONE = config('TIME_ZONE', default='America/Mexico_City')
USE_I18N = True
USE_TZ = True


# ==================================
# STATIC FILES (CSS, JavaScript, Images)
# ==================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ==================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'