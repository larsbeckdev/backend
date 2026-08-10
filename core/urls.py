"""URL configuration for the core project.

All application routes are included below the ``/api/`` prefix. Every app
keeps its own ``urls.py`` inside its ``api`` package.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
