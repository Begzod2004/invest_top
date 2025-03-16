from django.db import models

# Create your models here.

class Instrument(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title
