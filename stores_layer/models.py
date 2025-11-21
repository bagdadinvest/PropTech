from django.contrib.gis.db import models as gis_models
from django.db import models

# 1. Define the Abstract Base Class
# The Meta class abstract = True tells Django not to create a database
# table for this model, but to use its fields for inheritance.
class Store(models.Model):
    """
    Abstract base class for all store types to share common attributes.
    This model will not be created in the database.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Store Name"
    )

    # Use GeoDjango's PointField for location data.
    # srid=4326 is the standard WGS 84 geographic coordinate system (latitude/longitude).
    # geography=True is recommended for calculating distances/areas on a sphere (like Earth).
    location = gis_models.PointField(
        srid=4326,
        geography=True,
        verbose_name="Geographic Location (Point)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        # pragma: no cover
        return self.name

# 2. Concrete Model: Grocery Stores
class Grocery(Store):
    """
    Represents a specific grocery store location (e.g., Migros, A101).
    Inherits all fields from Store.
    """
    # No need to define additional fields unless specific grocery-only data is required.
    class Meta:
        verbose_name = "Grocery Store"
        verbose_name_plural = "Grocery Stores"
        # Since it inherits Meta ordering, it will also be ordered by name.

# 3. Concrete Model: Clothing Stores
class Clothing(Store):
    """
    Represents a specific clothing store location (e.g., Zara, Flo).
    Inherits all fields from Store.
    """
    # No need to define additional fields unless specific clothing-only data is required.
    class Meta:
        verbose_name = "Clothing Store"
        verbose_name_plural = "Clothing Stores"


# 4. Concrete Model: Malls
class Mall(Store):
    class Meta:
        verbose_name = "Mall"
        verbose_name_plural = "Malls"


# 5. Concrete Model: Parks
class Park(Store):
    class Meta:
        verbose_name = "Park"
        verbose_name_plural = "Parks"
