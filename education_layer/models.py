from django.contrib.gis.db import models


class School(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326, geography=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):  # pragma: no cover
        return self.name


class InternationalSchool(models.Model):
    """Represents high-value international curriculum schools."""

    name = models.CharField(max_length=255)
    address_text = models.CharField(max_length=255)
    location = models.PointField(srid=4326)
    curriculum = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):  # pragma: no cover
        return self.name


class Preschool(models.Model):
    """Represents kindergartens/preschools, primarily private/accredited."""

    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326)
    district = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["district", "name"]

    def __str__(self):  # pragma: no cover
        return f"{self.name} ({self.district})"
