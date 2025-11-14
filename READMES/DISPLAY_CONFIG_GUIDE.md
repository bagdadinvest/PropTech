# Display Configuration Control Guide

## Overview

You now have a centralized **Display Configuration** system in the Django admin panel that allows you to control how many entries are displayed on the frontend for each data layer. This ensures a smooth experience for mobile users by limiting the amount of data loaded.

## Features

✅ **Singleton Configuration** - Only one settings instance exists (prevents duplication)  
✅ **Per-Table Limits** - Control entries separately for listings, grocery stores, clothing stores, and metro stations  
✅ **Safe Deletion Prevention** - Configuration cannot be accidentally deleted  
✅ **Easy Admin UI** - Clean admin interface with organized fieldsets  

## Configurable Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `max_listings` | 100 | Maximum listings to display on the map |
| `max_grocery_stores` | 200 | Maximum grocery stores to display |
| `max_clothing_stores` | 200 | Maximum clothing stores to display |
| `max_metro_stations` | 100 | Maximum metro stations to display |

## How to Access

1. **Go to Django Admin Panel**: `http://localhost:8902/admin/`
2. **Find "Display Configuration"** section under the Listings app
3. **Click** on "Display Settings (Singleton)"
4. **Adjust the values** for each layer as needed
5. **Save** - Changes take effect immediately

## How It Works

### Frontend Integration

The `listings_geojson()` view in `listings/views.py` now respects the configuration:

```python
def listings_geojson(request: HttpRequest) -> JsonResponse:
    config = DisplayConfig.get_config()
    listings = Listing.objects.all()[: config.max_listings]
    features: List[Dict[str, Any]] = [_listing_feature(l) for l in listings]
    return JsonResponse({"type": "FeatureCollection", "features": features})
```

### Getting the Configuration Programmatically

In any view or API endpoint:

```python
from listings.models import DisplayConfig

config = DisplayConfig.get_config()
print(config.max_listings)  # Access any limit
```

## Extending for Other Views

If you have other endpoints that return stores or metro data, update them similarly:

### Example for Grocery Stores API

```python
from listings.models import DisplayConfig

def grocery_stores_geojson(request):
    config = DisplayConfig.get_config()
    groceries = Grocery.objects.all()[: config.max_grocery_stores]
    features = [_store_feature(g) for g in groceries]
    return JsonResponse({"type": "FeatureCollection", "features": features})
```

### Example for Metro Stations API

```python
def metro_stations_geojson(request):
    config = DisplayConfig.get_config()
    stations = MetroStation.objects.all()[: config.max_metro_stations]
    features = [_station_feature(s) for s in stations]
    return JsonResponse({"type": "FeatureCollection", "features": features})
```

## Database Structure

The configuration is stored in a single database table:

```
DisplayConfig
├── id (PK)
├── max_listings
├── max_grocery_stores
├── max_clothing_stores
├── max_metro_stations
├── created_at
└── updated_at
```

Only one row ever exists (id=1), enforced by the `save()` method.

## Admin Permissions

- ✅ **Add**: Allowed only if no configuration exists (prevents accidental creation)
- ❌ **Delete**: Disabled to prevent data loss
- ✅ **Edit**: Always allowed (this is the main operation)

## Performance Tips

### For Mobile Users

- **Keep listings low** (50-100): Reduces initial load time
- **Adjust stores gradually**: Test with 150 for grocery, 150 for clothing
- **Monitor metrics**: Track page load time after each adjustment

### Recommended Starting Values

```
- Listings: 50 (initial load)
- Grocery Stores: 100
- Clothing Stores: 100
- Metro Stations: 50
```

Then increase gradually based on performance metrics.

## Troubleshooting

### Configuration Not Appearing in Admin

Run the initialization command:
```bash
python manage.py init_display_config
```

### Configuration Limits Not Applied

Ensure all views are updated to use `DisplayConfig.get_config()`:
```python
# ❌ Wrong
listings = Listing.objects.all()

# ✅ Correct
config = DisplayConfig.get_config()
listings = Listing.objects.all()[: config.max_listings]
```

### Changes Not Taking Effect

- **Clear browser cache** (Ctrl+Shift+Delete or Cmd+Shift+Delete)
- **Restart Django server** if changes don't reflect immediately
- **Check server logs** for any errors

## API Endpoints

If you expose these limits via API:

```python
from django.http import JsonResponse
from listings.models import DisplayConfig

def config_api(request):
    config = DisplayConfig.get_config()
    return JsonResponse({
        "max_listings": config.max_listings,
        "max_grocery_stores": config.max_grocery_stores,
        "max_clothing_stores": config.max_clothing_stores,
        "max_metro_stations": config.max_metro_stations,
    })
```

## Future Enhancements

Consider adding:
- Per-region limits (different limits for different areas)
- Time-based limits (different values for peak hours)
- User-preference limits (different for different user types)
- Analytics integration (track impact on page load time)

---

**Created**: November 14, 2025  
**Framework**: Django + GeoDjango  
**Status**: Active
