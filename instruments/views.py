from django.shortcuts import render
from rest_framework import viewsets
from .models import Instrument
from .serializers import InstrumentSerializer

# Create your views here.

class InstrumentViewSet(viewsets.ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
