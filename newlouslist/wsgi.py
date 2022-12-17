"""
WSGI config for newlouslist project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import django 
from whitenoise import WhiteNoise

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'newlouslist.settings'
django.setup()

application = get_wsgi_application()
application = WhiteNoise(application, root="googleauthentication/static")