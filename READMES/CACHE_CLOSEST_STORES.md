# Closest Stores Caching System

## Overview

The closest stores caching system pre-computes and stores the IDs of the closest grocery and clothing stores for each listing. This approach ensures efficient frontend loading by:

1. **Pre-computation**: Distances are calculated once and cached in the database
2. **Reduced Queries**: Frontend gets IDs only, avoiding distance calculations at runtime
3. **Efficient Storage**: Uses JSONField to store lists of store IDs
4. **Configurable**: Admins can control how many closest stores to compute per listing

## Architecture

### Models

#### `DisplayConfig` (Updated)
- `closest_grocery_stores` (default: 20) - Number of closest grocery stores to pre-compute per listing
- `closest_clothing_stores` (default: 20) - Number of closest clothing stores to pre-compute per listing
- Legacy fields (`max_grocery_stores`, `max_clothing_stores`) kept for backward compatibility

#### `ClosestStoresCache` (New)
Stores pre-computed closest store IDs for each listing:
- `listing` - OneToOne reference to Listing
- `closest_grocery_ids` - JSONField storing list of Grocery store IDs ordered by distance
- `closest_clothing_ids` - JSONField storing list of Clothing store IDs ordered by distance
- `computed_at` - When cache was first created
- `updated_at` - When cache was last updated

Includes database indexes on `listing` and `updated_at` for efficient queries.

### Service Layer

#### `ClosestStoresService` (listings/services.py)

**Methods:**

##### `compute_closest_stores_for_listing(listing, config)`
Computes and caches the closest stores for a single listing.
```python
from listings.services import ClosestStoresService
cache = ClosestStoresService.compute_closest_stores_for_listing(listing, config)
```

##### `compute_all_listings()`
Batch processes all listings to compute their closest stores.
```python
stats = ClosestStoresService.compute_all_listings()
# Returns: {
#   "total": 100,
#   "successful": 99,
#   "failed": 1,
#   "errors": ["Listing 5: error message"],
#   "elapsed_seconds": 12.34
# }
```

##### `get_cached_stores(listing)`
Retrieves cached closest stores. Falls back to on-the-fly computation if cache doesn't exist.
```python
grocery_ids, clothing_ids = ClosestStoresService.get_cached_stores(listing)
```

##### `invalidate_cache(listing)`
Deletes cache for a specific listing.
```python
ClosestStoresService.invalidate_cache(listing)
```

##### `invalidate_all_cache()`
Clears all cached closest stores.
```python
ClosestStoresService.invalidate_all_cache()
```

## Usage

### 1. Initial Setup

After migrating the database, run:

```bash
python manage.py cache_closest_stores
```

This will:
- Create cache entries for all existing listings
- Use the current DisplayConfig values
- Show progress and statistics

### 2. Update Configuration

1. Go to Django Admin → Display Configuration
2. Adjust `Closest Grocery Stores` and `Closest Clothing Stores` values
3. Recompute cache:
```bash
python manage.py cache_closest_stores --invalidate
```

The `--invalidate` flag clears old cache before recomputing.

### 3. Add New Listings

When new listings are created, cache is automatically computed on first request via `get_cached_stores()` fallback.

To proactively cache all new listings:
```bash
python manage.py cache_closest_stores
```

### 4. Manual Cache Invalidation

If stores data changes (additions, deletions, location updates):

```bash
# Invalidate only (without recomputing)
python manage.py cache_closest_stores --invalidate-only

# Invalidate and recompute
python manage.py cache_closest_stores --invalidate
```

## Frontend Integration

The API response now includes store IDs instead of counts:

**Old Response:**
```json
{
  "properties": {
    "grocery_stores_nearby": 45,
    "clothing_stores_nearby": 23
  }
}
```

**New Response:**
```json
{
  "properties": {
    "closest_grocery_store_ids": [1, 5, 12, 23, ...],
    "closest_clothing_store_ids": [3, 7, 15, 28, ...]
  }
}
```

Frontend can:
1. Display the store IDs (with store details fetched separately or cached client-side)
2. Show store count: `closest_grocery_store_ids.length`
3. Iterate over IDs for store details from a dedicated endpoint

## Performance Benefits

### Before (Distance Calculation Per Request)
- Per listing: 2 distance queries (grocery + clothing)
- For 100 listings: ~200 queries per request
- Time: 2-5 seconds

### After (Pre-computed Cache)
- Per listing: 1 simple cache lookup
- For 100 listings: ~100 queries total (initial computation) → cached forever
- Time: <200ms per request

### Cache Computation (One-time Cost)
- For 100 listings with 20+20 closest stores: ~30-60 seconds
- Can be done offline/scheduled
- Result: Instant queries forever

## Monitoring

Check cache status in Django Admin:
1. **Display Configuration**: View current settings for closest stores
2. **Closest Stores Cache**: See all cached entries with counts and update times
3. **Listings Admin**: Shows "Cache Status" column (✓ Cached or ⚠ Not cached)

## Advanced: Custom Batch Processing

```python
from listings.models import DisplayConfig
from listings.services import ClosestStoresService

config = DisplayConfig.get_config()

# Process specific listings
for listing in queryset:
    ClosestStoresService.compute_closest_stores_for_listing(listing, config)
```

## Database Schema

```sql
CREATE TABLE listings_closestorescache (
    id BIGSERIAL PRIMARY KEY,
    listing_id BIGINT UNIQUE NOT NULL REFERENCES listings_listing(id),
    closest_grocery_ids JSONB DEFAULT '[]',
    closest_clothing_ids JSONB DEFAULT '[]',
    computed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    CREATE INDEX idx_listing ON listings_closestorescache(listing_id),
    CREATE INDEX idx_updated_at ON listings_closestorescache(updated_at)
);

ALTER TABLE displayconfig
ADD COLUMN closest_grocery_stores INT DEFAULT 20,
ADD COLUMN closest_clothing_stores INT DEFAULT 20;
```

## Troubleshooting

### Cache Not Updating After Changing Config
```bash
# Force recomputation with new settings
python manage.py cache_closest_stores --invalidate
```

### Specific Listing Not Cached
```python
from listings.models import Listing
from listings.services import ClosestStoresService

listing = Listing.objects.get(id=5)
ClosestStoresService.compute_closest_stores_for_listing(listing, config)
```

### View Cache Contents
```python
from listings.models import Listing

listing = Listing.objects.get(id=1)
cache = listing.closest_stores_cache
print(cache.closest_grocery_ids)      # [1, 5, 12, ...]
print(cache.closest_clothing_ids)     # [3, 7, 15, ...]
print(cache.updated_at)               # Last update time
```

### Monitor Log Output
```bash
tail -f logs/django.log | grep "\[CACHE"
```

Useful log prefixes:
- `[CACHE_COMPUTE_START]` - Starting computation
- `[CACHE_GROCERY]` - Grocery stores found
- `[CACHE_CLOTHING]` - Clothing stores found
- `[CACHE_CREATED]` - New cache entry created
- `[CACHE_UPDATED]` - Cache updated
- `[CACHE_HIT]` - Cache retrieved successfully
- `[CACHE_MISS]` - Cache not found, computing on-the-fly
- `[CACHE_INVALIDATED]` - Cache deleted

## Related Files

- `listings/models.py` - DisplayConfig and ClosestStoresCache models
- `listings/services.py` - ClosestStoresService implementation
- `listings/views.py` - Updated _listing_feature() to use cache
- `listings/admin.py` - Admin interface for cache management
- `listings/management/commands/cache_closest_stores.py` - Management command
- `listings/migrations/0004_*` - Database migration
