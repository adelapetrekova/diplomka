from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import GeoData

class GeoDataView(APIView):
    def get(self, request):
        geodata = GeoData.objects.all()
        return Response([{'name': g.name, 'geometry': g.geometry} for g in geodata])
