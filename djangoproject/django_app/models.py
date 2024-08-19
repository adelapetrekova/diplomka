
# Create your models here.
from django.db import models

class GeoData(models.Model):
    name = models.CharField(max_length=255)
    geometry = models.GeometryField()