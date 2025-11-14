# Setup Guide: Closest Stores Caching System

## Overview

This guide walks you through setting up and deploying the closest stores caching system for your Django application.

## Prerequisites

- Django 3.2+
- PostGIS database
- GeoDjango
- Existing `Listing`, `Grocery`, and `Clothing` models

## Installation Steps

### Step 1: Verify Files Are in Place

Check that all these files exist:

```
listings/
├── models.py (updated with ClosestStoresCache)
├── views.py (updated to use service)
├── admin.py (updated with new admins)
├── services.py (NEW - ClosestStoresService)
├── signals.py (NEW - optional automatic invalidation)
├── management/
│   └── commands/
│       └── cache_closest_stores.py (NEW - management command)
└── migrations/
    └── 0004_displayconfig_closest_stores_and_closestorescache.py (NEW)

Documentation:
├── CACHE_CLOSEST_STORES.md (technical reference)
├── CACHE_CLOSEST_STORES_QUICKSTART.md (quick reference)
├── IMPLEMENTATION_SUMMARY.md (overview)
└── SETUP_GUIDE.md (this file)
```

### Step 2: Run Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

Verify:
```bash
python manage.py dbshell
\dt listings_*  # Should show: displayconfig, listing, closestorescache
```

### Step 3: Initialize Configuration

```bash
python manage.py shell
>>> from listings.models import DisplayConfig
>>> config = DisplayConfig.get_config()
>>> config.closest_grocery_stores
20
>>> config.closest_clothing_stores
20
```

The singleton configuration is auto-created with defaults.

### Step 4: Pre-compute Cache for All Listings

```bash
python manage.py cache_closest_stores
```

Expected output:
```
================================================================================
Closest Stores Cache Management
================================================================================

✓ Configuration loaded:
  - Closest grocery stores per listing: 20
  - Closest clothing stores per listing: 20

⏳ Computing cache for all listings...

✓ Cache computation complete!
  - Total listings: 100
  - Successful: 100
  - Failed: 0
  - Elapsed time: 45.67s

================================================================================
```

### Step 5: Verify Cache in Admin

1. Go to Django Admin: `http://localhost:8000/admin/`
2. Navigate to **Listings** → **Closest Stores Cache**
3. Should see one entry per listing showing cached stores and update time
4. Go to **Listings** → **Listing**
5. Each listing should show "✓ Cached (20 grocery, 20 clothing)"

### Step 6: Test API Response

```bash
curl http://localhost:8000/api/listings_geojson/ | jq '.features[0].properties'
```

Expected response:
```json
{
  "id": 1,
  "title": "Beautiful Apartment in Kadıköy",
  "price": 5000000,
  "size_sqm": 120,
  "closest_station_name": "Kadıköy Metro Station",
  "distance_to_station_m": 450.5,
  "closest_grocery_store_ids": [1, 5, 12, 23, 34, 45, 56, 67, 78, 89, 101, 112, 123, 134, 145, 156, 167, 178, 189, 200],
  "closest_clothing_store_ids": [3, 7, 15, 28, 41, 54, 67, 80, 93, 106, 119, 132, 145, 158, 171, 184, 197, 210, 223, 236],
  "image_url": "/media/listings/building_1.jpg"
}
```

Note the **`closest_*_store_ids`** fields instead of counts.

## Optional: Enable Automatic Cache Invalidation

To automatically invalidate cache when stores change, enable signals:

### Step 1: Update `listings/apps.py`

```python
# listings/apps.py

from django.apps import AppConfig


class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'
    
    def ready(self):
        # Import signals to register them
        import listings.signals  # noqa
```

### Step 2: Test Signals

```bash
# Watch logs in another terminal
tail -f logs/django.log | grep "\[SIGNAL"

# In Django shell or admin, update a store
python manage.py shell
>>> from stores_layer.models import Grocery
>>> store = Grocery.objects.first()
>>> store.name = "Updated Store"
>>> store.save()  # Should see [SIGNAL] log
```

You should see log entries like:
```
[SIGNAL] Grocery store 5 updated, invalidating all caches (expensive operation)
```

## Configuration

### Change Number of Closest Stores

1. Go to Django Admin → **Display Configuration**
2. Update values:
   - **Closest Grocery Stores**: Default 20, can increase/decrease
   - **Closest Clothing Stores**: Default 20, can increase/decrease
3. Click **Save**
4. Recompute cache:
   ```bash
   python manage.py cache_closest_stores --invalidate
   ```

### Monitor Cache Age

```bash
python manage.py shell
>>> from listings.models import ClosestStoresCache
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> now = timezone.now()
>>> stale = ClosestStoresCache.objects.filter(
...     updated_at__lt=now - timedelta(days=7)
... ).count()
>>> print(f"Stale cache entries (>7 days): {stale}")
```

### Batch Recompute Without Invalidation

For when you add new listings but don't want to clear existing cache:

```bash
python manage.py cache_closest_stores
```

Only computes cache for listings that don't have it.

### Force Full Recomputation

```bash
python manage.py cache_closest_stores --invalidate
```

Clears all cache and recomputes from scratch.

## Monitoring

### View Cache Statistics

```bash
python manage.py shell
>>> from listings.models import ClosestStoresCache, Listing
>>> total_listings = Listing.objects.count()
>>> cached_listings = ClosestStoresCache.objects.count()
>>> print(f"Listings: {total_listings}")
>>> print(f"Cached: {cached_listings}")
>>> print(f"Coverage: {100*cached_listings/total_listings:.1f}%")
```

### Check Individual Listing Cache

```python
>>> from listings.models import Listing
>>> listing = Listing.objects.get(id=1)
>>> cache = listing.closest_stores_cache
>>> print(f"Grocery stores: {len(cache.closest_grocery_ids)}")
>>> print(f"Clothing stores: {len(cache.closest_clothing_ids)}")
>>> print(f"Last updated: {cache.updated_at}")
>>> print(f"First 5 grocery IDs: {cache.closest_grocery_ids[:5]}")
```

### Monitor Performance

```bash
# Watch cache operations in logs
tail -f logs/django.log | grep -E "\[CACHE|\[FEATURE_COMPLETE"

# Sample output:
# [CACHE_HIT] Listing 1: Retrieved 20 grocery, 20 clothing
# [FEATURE_COMPLETE] Listing 1: Total time: 0.0023s | Queries: 1 | Breakdown - Metro: 0.0001s, Cache: 0.0022s
```

## Troubleshooting

### Problem: "ClosestStoresCache not found" error

**Cause**: Cache not computed yet

**Solution**:
```bash
python manage.py cache_closest_stores
```

### Problem: Some listings are cached, some are not

**Cause**: New listings added after cache computation

**Solution**:
```bash
python manage.py cache_closest_stores
```

Auto-computes cache for uncached listings only.

### Problem: Stale cache after stores changed

**Cause**: Store data modified but cache not invalidated

**Solution**:
```bash
# If signals enabled, cache auto-invalidates on save
# If signals not enabled:
python manage.py cache_closest_stores --invalidate
```

### Problem: Too many/too few stores in response

**Cause**: DisplayConfig set to wrong value

**Solution**:
1. Go to Django Admin → Display Configuration
2. Adjust `closest_grocery_stores` or `closest_clothing_stores`
3. Run: `python manage.py cache_closest_stores --invalidate`

### Problem: Performance issue during cache computation

**Cause**: Computing cache for too many listings at once

**Solution**:
- Increase server resources (CPU/RAM)
- Or compute during off-peak hours
- Or increase `closest_*_stores` value cautiously

## Migration Checklist

- [ ] Database migration applied (`python manage.py migrate`)
- [ ] Configuration initialized (check Django Admin)
- [ ] Cache computed for all listings (`python manage.py cache_closest_stores`)
- [ ] Admin interfaces visible
- [ ] API response tested and shows store IDs
- [ ] Frontend updated to use store IDs instead of counts
- [ ] Signals enabled (optional) for automatic invalidation
- [ ] Monitoring set up (logs, admin checks)
- [ ] Documentation reviewed

## Expected Outcomes

### Performance
- **Before**: 2-5 seconds to load 100 listings
- **After**: <200ms to load 100 listings
- **Setup**: ~1 minute one-time cost

### API Response Size
- Slightly smaller (IDs instead of counts)
- Highly efficient for frontend processing

### Admin Interface
- New "Closest Stores Cache" section
- "Cache Status" column on Listings
- Easy reconfiguration via Display Configuration

## Files Reference

| File | Purpose |
|------|---------|
| `listings/models.py` | ClosestStoresCache model + updated DisplayConfig |
| `listings/services.py` | ClosestStoresService with all logic |
| `listings/views.py` | Updated _listing_feature() to use service |
| `listings/admin.py` | Admin interfaces for cache management |
| `listings/signals.py` | Optional auto-invalidation signals |
| `listings/management/commands/cache_closest_stores.py` | Management command |
| `listings/migrations/0004_*` | Database migration |

## Next Steps

1. ✅ Complete installation steps above
2. ✅ Update frontend to use store IDs
3. ✅ Monitor performance improvements
4. ✅ Set up scheduled cache refresh if needed
5. ✅ Document in deployment playbooks

## Support & Questions

For detailed information:
- Technical details: See `CACHE_CLOSEST_STORES.md`
- Quick reference: See `CACHE_CLOSEST_STORES_QUICKSTART.md`
- Implementation details: See `IMPLEMENTATION_SUMMARY.md`

For issues:
- Check logs: `tail -f logs/django.log | grep "\[CACHE"`
- Admin status: Django Admin → Closest Stores Cache
- Manual verification: Run `python manage.py shell` commands above
