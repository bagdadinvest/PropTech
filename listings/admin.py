from django.contrib import admin
from .models import (
    Listing,
    DisplayConfig,
    ClosestStoresCache,
    ListingImage,
    ExternalListing,
    MapGenerationConfig,
)
from django import forms
from django.contrib.gis.geos import Point


@admin.register(DisplayConfig)
class DisplayConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Listings", {
            "fields": ("max_listings",)
        }),
        ("Closest Stores (Pre-computed per Listing)", {
            "fields": ("closest_grocery_stores", "closest_clothing_stores"),
            "description": "These numbers determine how many closest stores are pre-computed and cached for each listing."
        }),
        ("Legacy Store Limits (for frontend filtering)", {
            "fields": ("max_grocery_stores", "max_clothing_stores"),
            "classes": ("collapse",),
            "description": "These are kept for backward compatibility but mainly used for frontend filtering."
        }),
        ("Transit", {
            "fields": ("max_metro_stations",)   
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        # Allow add if no instance exists
        return self.model.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False


@admin.register(ClosestStoresCache)
class ClosestStoresCacheAdmin(admin.ModelAdmin):
    list_display = ("listing", "grocery_count", "clothing_count", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("listing__title",)
    readonly_fields = ("listing", "closest_grocery_ids", "closest_clothing_ids", "computed_at", "updated_at")
    
    def grocery_count(self, obj):
        return len(obj.closest_grocery_ids)
    grocery_count.short_description = "Closest Grocery Stores"
    
    def clothing_count(self, obj):
        return len(obj.closest_clothing_ids)
    clothing_count.short_description = "Closest Clothing Stores"
    
    def has_add_permission(self, request):
        # Cache is auto-generated
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Cache is auto-generated
        return False


# Inline admin for managing images within a listing
class ListingImageInline(admin.TabularInline):
    """Inline admin for managing images within a listing."""
    model = ListingImage
    extra = 1
    fields = ("image", "title", "description", "order", "is_primary", "created_at")
    readonly_fields = ("created_at",)
    ordering = ["order", "created_at"]


class ListingAdminForm(forms.ModelForm):
    coordinates = forms.CharField(
        max_length=100,
        required=False,
        help_text="Enter coordinates as 'latitude, longitude'. If provided, this will override the map location."
    )

    class Meta:
        model = Listing
        fields = '__all__'


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    form = ListingAdminForm
    list_display = ("title", "price", "size_sqm", "image_count", "cache_status")
    search_fields = ("title",)
    readonly_fields = ("cache_status", "image_count")
    inlines = [ListingImageInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'price', 'size_sqm', 'image')
        }),
        ('Location', {
            'fields': ('location', 'coordinates'),
        }),
    )
    
    def image_count(self, obj):
        count = obj.images.count()
        if count > 0:
            primary = obj.images.filter(is_primary=True).exists()
            primary_indicator = "★" if primary else ""
            return f"{count} image(s) {primary_indicator}"
        return "No images"
    image_count.short_description = "Images"
    
    def cache_status(self, obj):
        try:
            cache = obj.closest_stores_cache
            return f"✓ Cached ({len(cache.closest_grocery_ids)} grocery, {len(cache.closest_clothing_ids)} clothing)"
        except:
            return "⚠ Not cached"
    cache_status.short_description = "Cache Status"

    def save_model(self, request, obj, form, change):
        coordinates = form.cleaned_data.get('coordinates')
        if coordinates:
            try:
                lat_str, lon_str = coordinates.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
                obj.location = Point(lon, lat, srid=4326)
            except (ValueError, TypeError):
                # Silently ignore malformed coordinates
                pass
        super().save_model(request, obj, form, change)


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    """Standalone admin for managing listing images."""
    list_display = ("get_listing", "title", "image_preview", "order", "is_primary", "created_at")
    list_filter = ("is_primary", "created_at", "listing__title")
    search_fields = ("listing__title", "title", "description")
    readonly_fields = ("image_preview_large", "created_at", "updated_at")
    fieldsets = (
        ("Image Info", {
            "fields": ("listing", "image", "image_preview_large")
        }),
        ("Details", {
            "fields": ("title", "description", "order", "is_primary")
        }),
        ("Metadata", {
            "fields": ("uploaded_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    ordering = ["listing", "order", "created_at"]
    
    def get_listing(self, obj):
        return obj.listing.title
    get_listing.short_description = "Listing"
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" />'
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = "Preview"
    
    def image_preview_large(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 300px; max-height: 300px;" />'
        return "No image"
    image_preview_large.allow_tags = True
    image_preview_large.short_description = "Image Preview"



@admin.register(ExternalListing)
class ExternalListingAdmin(admin.ModelAdmin):
    list_display = ("source", "external_id", "title", "price", "city", "state", "fetched_at")
    list_filter = ("source", "city", "state", "fetched_at")
    search_fields = ("external_id", "title", "city", "state")
    readonly_fields = ("fetched_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("source", "external_id", "title", "price", "deal_type")}),
        ("Location", {"fields": ("lat", "lng", "location", "city", "state")}),
        ("Links", {"fields": ("url", "original_url")}),
        ("Payload", {"fields": ("payload",)}),
        ("Timestamps", {"fields": ("fetched_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(MapGenerationConfig)
class MapGenerationConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Layers", {"fields": ("enable_metro", "enable_metrobus", "enable_bus", "enable_grocery", "enable_clothing", "enable_pharmacy", "enable_minibus", "enable_malls", "enable_parks", "enable_taxi", "enable_bicycle")}),
        ("Radii (meters)", {"fields": ("radius_metro", "radius_metrobus", "radius_bus", "radius_grocery", "radius_clothing", "radius_pharmacy", "radius_minibus", "radius_malls", "radius_parks", "radius_taxi", "radius_bicycle")}),
        ("Max Counts", {"fields": ("max_metro", "max_metrobus", "max_bus", "max_grocery", "max_clothing", "max_pharmacy", "max_minibus", "max_malls", "max_parks", "max_taxi", "max_bicycle")}),
        ("Meta", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("updated_at",)
    
    def has_add_permission(self, request):
        return self.model.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        return False
