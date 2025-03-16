from django.contrib import admin
from .models import Instrument

admin.site.register(Instrument)
# Compare this snippet from instruments/urls.py:
