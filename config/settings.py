"""
Django settings for SCA-B123 project.
"""

from pathlib import Path
from decouple import config
import os
from django.urls import reverse_lazy

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
	'apps.incidencias',
    'apps.accounts',
    'apps.trabajadores',
    'apps.unidades',
    'apps.jornadas_laborales',
    'apps.asistencias',
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
    'allauth.account.middleware.AccountMiddleware',  # Requerido por allauth
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
                'django.template.context_processors.request',  # Requerido por allauth
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
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================================
# ALLAUTH CONFIGURATION
# ==================================

ACCOUNT_AUTHENTICATION_METHOD = config('ACCOUNT_AUTHENTICATION_METHOD', default='username_email')
ACCOUNT_EMAIL_REQUIRED = config('ACCOUNT_EMAIL_REQUIRED', default=True, cast=bool)
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default='mandatory')
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = config('ACCOUNT_LOGIN_ATTEMPTS_LIMIT', default=5, cast=int)
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = config('ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT', default=300, cast=int)

LOGIN_REDIRECT_URL = 'accounts:dashboard'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
# Para usuarios que no están logueados
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/accounts/login/'

# Para usuarios que ya están logueados
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/accounts/dashboard/'


# ==================================
# EMAIL CONFIGURATION (MailHog)
# ==================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sca_b123_mailhog'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'SCA-B123 <noreply@sca-b123.local>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ==================================
# INTERNATIONALIZATION
# ==================================

LANGUAGE_CODE = config('LANGUAGE_CODE', default='es-mx')
TIME_ZONE = config('TIME_ZONE', default='America/Mexico_City')
USE_I18N = True
USE_TZ = True

# ==================================
# STATIC FILES
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

# Formulario de registro personalizado
ACCOUNT_SIGNUP_FORM_CLASS = "apps.accounts.forms.CustomSignupForm"
