# Cache Closest Stores - Quick Reference

## Quick Start

### 1. Run Initial Cache Setup
```bash
python manage.py cache_closest_stores
```

### 2. Configure via Admin
```
Django Admin → Display Configuration
├── Closest Grocery Stores: 20 (default)
└── Closest Clothing Stores: 20 (default)
```

### 3. Check Cache Status
```
Django Admin → Closest Stores Cache
```
Shows all cached listings with store counts and update times.

---

## Common Tasks

### Update Cache After Changing Config
```bash
python manage.py cache_closest_stores --invalidate
```

### Rebuild Cache Only (No Invalidate First)
```bash
python manage.py cache_closest_stores
```

### Delete All Cache (Keep Database)
```bash
python manage.py cache_closest_stores --invalidate-only
```

### Check Specific Listing Cache
```python
python manage.py shell
>>> from listings.models import Listing
>>> listing = Listing.objects.get(id=1)
>>> cache = listing.closest_stores_cache
>>> len(cache.closest_grocery_ids)
20
>>> cache.closest_grocery_ids
[1, 5, 12, 23, ...]
```

---

## Data Flow

```
POST /api/listings_geojson/
    ↓
_listing_feature(listing)
    ↓
ClosestStoresService.get_cached_stores(listing)
    ├─ Cache hit? → Return stored IDs immediately ✓ FAST
    └─ Cache miss? → Compute & store, return IDs
    ↓
Return GeoJSON with:
  - closest_grocery_store_ids: [1, 5, 12, ...]
  - closest_clothing_store_ids: [3, 7, 15, ...]
```

---

## API Response Format

**Before:**
```json
{
  "properties": {
    "grocery_stores_nearby": 45,
    "clothing_stores_nearby": 23
  }
}
```

**After:**
```json
{
  "properties": {
    "closest_grocery_store_ids": [1, 5, 12, 23, 34, 45, ...],
    "closest_clothing_store_ids": [3, 7, 15, 28, 41, ...]
  }
}
```

---

## Performance Impact

| Metric | Before | After |
|--------|--------|-------|
| Queries per request | ~200 | ~100 (one-time) |
| Time per 100 listings | 2-5s | <200ms |
| Setup cost | N/A | ~1 min (one-time) |
| Cache hit | N/A | ~1ms |

---

## Monitoring

### View Logs
```bash
tail -f logs/django.log | grep "\[CACHE"
```

### Admin Locations
- **Display Config**: `/admin/listings/displayconfig/`
- **Cache Status**: `/admin/listings/closestorescache/`
- **Listings**: `/admin/listings/listing/` (shows cache status)

### Check Cache Age
```python
>>> from listings.models import ClosestStoresCache
>>> from django.utils import timezone
>>> cache = ClosestStoresCache.objects.order_by('updated_at').first()
>>> timezone.now() - cache.updated_at
datetime.timedelta(seconds=12345)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Cache not showing in admin | Run: `python manage.py cache_closest_stores` |
| Getting too many stores | Lower `closest_*_stores` in Display Config + recompute |
| Getting too few stores | Raise `closest_*_stores` in Display Config + recompute |
| Stale cache | Run: `python manage.py cache_closest_stores --invalidate` |
| New stores not showing | Run cache command or wait for new listing |

---

## Key Files

| File | Purpose |
|------|---------|
| `listings/models.py` | DisplayConfig, ClosestStoresCache, Listing |
| `listings/services.py` | ClosestStoresService class |
| `listings/views.py` | Updated _listing_feature() |
| `listings/admin.py` | Admin interface |
| `listings/management/commands/cache_closest_stores.py` | Management command |
| `listings/migrations/0004_*` | Database migration |
| `CACHE_CLOSEST_STORES.md` | Full documentation |

---

## Example Usage

### Django Admin
1. Go to Display Configuration
2. Set `Closest Grocery Stores` = 15
3. Set `Closest Clothing Stores` = 25
4. Save
5. Run: `python manage.py cache_closest_stores --invalidate`
6. Check Closest Stores Cache admin to verify

### Programmatic
```python
from listings.models import Listing, DisplayConfig
from listings.services import ClosestStoresService

# Get config
config = DisplayConfig.get_config()

# Compute for one listing
listing = Listing.objects.first()
cache = ClosestStoresService.compute_closest_stores_for_listing(listing, config)

# Get cached stores
grocery_ids, clothing_ids = ClosestStoresService.get_cached_stores(listing)
print(f"Closest grocery stores: {grocery_ids}")
print(f"Closest clothing stores: {clothing_ids}")

# Batch compute
stats = ClosestStoresService.compute_all_listings()
print(f"Computed {stats['successful']} listings in {stats['elapsed_seconds']:.2f}s")
```

---

## Logging Examples

### Successful Computation
```
[CACHE_COMPUTE_START] Listing 5 (Beautiful Apartment)
[CACHE_GROCERY] Listing 5: Found 20 stores | Time: 0.0234s
[CACHE_CLOTHING] Listing 5: Found 20 stores | Time: 0.0198s
[CACHE_CREATED] Listing 5: 20 grocery + 20 clothing | Time: 0.0567s
```

### Cache Hit
```
[CACHE_HIT] Listing 5: Retrieved 20 grocery, 20 clothing
[FEATURE_COMPLETE] Listing 5: Total time: 0.0012s
```

### Cache Miss (Fallback Computation)
```
[CACHE_MISS] Listing 6: Computing on-the-fly
[CACHE_COMPUTE_START] Listing 6 (New Listing)
[CACHE_CLOTHING] Listing 6: Found 20 stores | Time: 0.0215s
[CACHE_CREATED] Listing 6: 20 grocery + 20 clothing | Time: 0.0482s
```
