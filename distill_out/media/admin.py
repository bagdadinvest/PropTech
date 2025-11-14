from django.contrib import admin
from .models import Listing, DisplayConfig, ClosestStoresCache, ListingImage


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


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "size_sqm", "image_count", "cache_status")
    search_fields = ("title",)
    readonly_fields = ("cache_status", "image_count")
    inlines = [ListingImageInline]
    
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


