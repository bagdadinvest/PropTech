from django.contrib.gis.db import models


class MetroStation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # geography=True gives meter-based distances for Distance()
    location = models.PointField(srid=4326, geography=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class BusStop(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326, geography=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class MetrobusStation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.PointField(srid=4326, geography=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class TaxiStand(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326, geography=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name
