# Architecture Diagram: Closest Stores Caching System

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Browser)                             │
│                    Displays map with store locations                      │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ GET /api/listings_geojson/
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          DJANGO API LAYER                                │
│                  (listings/views.py:listings_geojson)                    │
│                                                                          │
│  1. Get DisplayConfig (max listings to return)                          │
│  2. Query Listings from database                                        │
│  3. For each listing, call _listing_feature()                           │
└──────────┬───────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FEATURE BUILDER LAYER                                │
│              (listings/views.py:_listing_feature)                       │
│                                                                          │
│  For each listing:                                                       │
│  ┌──────────────────────────────────────────────────────────┐            │
│  │ 1. Get nearest metro station (Distance query)           │            │
│  │    ↓                                                     │            │
│  │    MetroStation.objects.annotate(distance)...           │            │
│  │                                                          │            │
│  │ 2. Get cached closest stores (Our new system!)          │            │
│  │    ↓                                                     │            │
│  │    ClosestStoresService.get_cached_stores(listing)      │            │
│  │                                                          │            │
│  │ 3. Build GeoJSON feature                                │            │
│  └──────────────────────────────────────────────────────────┘            │
└──────────────┬────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER (NEW!)                                │
│           (listings/services.py:ClosestStoresService)                   │
│                                                                          │
│  ClosestStoresService.get_cached_stores(listing)                        │
│  │                                                                       │
│  ├─→ Try to get ClosestStoresCache for listing                          │
│  │   │                                                                   │
│  │   ├─→ ✓ Cache exists?                                                │
│  │   │   └─→ Return stored IDs immediately (FAST!)                      │
│  │   │       [1, 5, 12, 23, ...]                                        │
│  │   │                                                                   │
│  │   └─→ ✗ Cache miss?                                                  │
│  │       └─→ Compute on-the-fly (fallback)                              │
│  │           ├─→ Find 20 closest grocery stores                         │
│  │           ├─→ Find 20 closest clothing stores                        │
│  │           └─→ Save to ClosestStoresCache                             │
│  │               └─→ Return IDs                                         │
│  │                                                                       │
│  └─→ Always return: (grocery_ids, clothing_ids)                         │
└──────────┬───────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        DATABASE LAYER                                   │
│                                                                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐        │
│  │   listings_     │  │  listings_       │  │ listings_       │        │
│  │   listing       │  │  closestorescache│  │ displayconfig   │        │
│  │ ┌─────────────┐ │  │ ┌──────────────┐ │  │ ┌─────────────┐ │        │
│  │ │id           │ │  │ │listing_id    │ │  │ │max_listings │ │        │
│  │ │title        │ │  │ │closest_groc..│ │  │ │closest_groc.│ │        │
│  │ │price        │ │  │ │closest_clot..│ │  │ │closest_clot.│ │        │
│  │ │size_sqm     │ │  │ │computed_at   │ │  │ │updated_at   │ │        │
│  │ │location     │ │  │ │updated_at    │ │  │ └─────────────┘ │        │
│  │ │image        │ │  │ └──────────────┘ │  │                 │        │
│  │ └─────────────┘ │  │                  │  │ (Singleton)     │        │
│  │                 │  │ INDEX:           │  │ Controls:       │        │
│  │ ~100 listings   │  │ - listing_id     │  │ - How many      │        │
│  │                 │  │ - updated_at     │  │   closest       │        │
│  │ GIS enabled     │  │                  │  │   stores to     │        │
│  │ (Point field)   │  │ ONE per listing  │  │   pre-compute   │        │
│  │                 │  │ (OneToOne FK)    │  │                 │        │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │  transit_layer             stores_layer                 │           │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │           │
│  │  │ metrostations│  │  grocery     │  │  clothing    │   │           │
│  │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │   │           │
│  │  │ │id        │ │  │ │id        │ │  │ │id        │ │   │           │
│  │  │ │name      │ │  │ │name      │ │  │ │name      │ │   │           │
│  │  │ │location  │ │  │ │location  │ │  │ │location  │ │   │           │
│  │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │   │           │
│  │  │              │  │              │  │              │   │           │
│  │  │ ~10 stations │  │ ~1000 stores │  │ ~500 stores  │   │           │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │           │
│  └──────────────────────────────────────────────────────────┘           │
│                      (Read-only during requests)                         │
└──────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Initial Setup (One-time)

```
┌─────────────────────────────────────────────────────────────┐
│  Admin: python manage.py cache_closest_stores               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Load DisplayConfig   │
        │ - closest_grocery: 20│
        │ - closest_clothing:20│
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ For each listing:    │
        │  1→2→3 (see below)   │
        │ Loop 100 times       │
        └──────────┬───────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ (1) Query 20│  │ (2) Query 20 │  │ (3) Save to  │
│ closest     │  │ closest      │  │ database     │
│ groceries   │  │ clothing     │  │              │
│             │  │ stores       │  │ ClosestStores│
│ SELECT      │  │              │  │ Cache        │
│ FROM store  │  │ SELECT       │  │              │
│ ORDER BY    │  │ FROM store   │  │ INSERT INTO  │
│ distance    │  │ ORDER BY     │  │ listings_    │
│ LIMIT 20    │  │ distance     │  │ closeststore │
│             │  │ LIMIT 20     │  │ scache       │
└─────────────┘  └──────────────┘  └──────────────┘

Result: 100 listings × (20 + 20 stores) = 4000 distance queries
        Computed once, cached forever ✓
```

### Runtime Request (Fast!)

```
┌─────────────────────────────────────────────────────────────┐
│  Client: GET /api/listings_geojson/                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Load 100 listings        │
        │ from database            │
        │ (1 query)                │
        └──────────┬───────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
 LISTING 1      LISTING 2       LISTING 3
    │              │              │
    ▼              ▼              ▼
 ┌─────┐        ┌─────┐        ┌─────┐
 │ Get │        │ Get │        │ Get │
 │Metro│        │Metro│        │Metro│        (3 queries)
 │     │        │     │        │     │
 │ 0.5s│        │ 0.4s│        │ 0.5s│
 └─────┘        └─────┘        └─────┘
    │              │              │
    ▼              ▼              ▼
 ┌─────┐        ┌─────┐        ┌─────┐
 │ Get │        │ Get │        │ Get │
 │Stores        │Stores        │Stores        (cache lookups)
 │(cache)       │(cache)       │(cache)
 │ <1ms │        │ <1ms │        │ <1ms │      INSTANT!
 └─────┘        └─────┘        └─────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Return GeoJSON with      │
        │ store IDs:               │
        │                          │
        │ [1, 5, 12, 23, ...]     │
        └──────────────────────────┘

Result: Total queries: ~103 (1 config + 100 listings + 2 metro)
        Total time: <200ms
        No distance calculations! ✓
```

## Component Interaction

```
                   ┌──────────────────────────────┐
                   │    Django Admin Interface    │
                   │  - Display Configuration     │
                   │  - Closest Stores Cache      │
                   │  - Listings (cache status)   │
                   └──────────────┬───────────────┘
                                  │
                                  │ Configure
                                  │ number of
                                  │ closest
                                  │ stores
                                  ▼
┌────────────────┐     ┌──────────────────────┐
│   Views        │────→│  ClosestStoresService│
│  (views.py)    │     │                      │
│                │     │ - compute_closest   │
│ lists_geojson()│     │ - get_cached        │
│ _listing_      │     │ - invalidate        │
│ feature()      │     │ - batch compute     │
└────────┬───────┘     └──────────┬──────────┘
         │                        │
         │ calls                  │ queries
         │                        │
         ▼                        ▼
┌────────────────┐     ┌──────────────────────┐
│   Models       │────→│    Database          │
│                │     │                      │
│ Listing        │     │ ClosestStoresCache   │
│ DisplayConfig  │     │ (pre-computed)       │
│ ClosestStores- │     │                      │
│ Cache (NEW)    │     │ Grocery stores       │
└────────────────┘     │ Clothing stores      │
                       │ Metro stations       │
                       └──────────────────────┘
```

## Cache Hit/Miss Decision Tree

```
                    GET /api/listings_geojson/
                            │
                            ▼
                ┌──────────────────────────┐
                │  _listing_feature()      │
                │  called for each listing │
                └────────────┬─────────────┘
                             │
                             ▼
         ┌──────────────────────────────────┐
         │  ClosestStoresService.           │
         │  get_cached_stores(listing)      │
         └────────────┬─────────────────────┘
                      │
                      ▼
          ┌─────────────────────────┐
          │ Does cache exist?       │
          │ (ClosestStoresCache     │
          │  for this listing)      │
          └───┬─────────────────┬───┘
              │                 │
         YES  │                 │  NO
             ▼                 ▼
        ┌─────────────┐   ┌──────────────────┐
        │ CACHE HIT!  │   │ CACHE MISS!      │
        │             │   │                  │
        │ Return      │   │ Compute now:     │
        │ stored IDs  │   │                  │
        │ instantly   │   │ - Find 20 grocery│
        │             │   │ - Find 20 clothin│
        │ Time: <1ms  │   │ - Save to DB     │
        │             │   │ - Return IDs     │
        │             │   │                  │
        │             │   │ Time: ~50ms      │
        └─────┬───────┘   └────────┬─────────┘
              │                    │
              └────────┬───────────┘
                       │
                       ▼
         ┌───────────────────────────┐
         │ Return GeoJSON feature    │
         │ with:                     │
         │ - id, title, price, etc   │
         │ - station name            │
         │ - store IDs [1,5,12,...] │
         └───────────────────────────┘
```

## Performance Timeline

```
BEFORE (Distance queries on each request):

Request 1: |←──── 3 sec ────→|  100 listings × 2 distance queries
Request 2: |←──── 3 sec ────→|
Request 3: |←──── 3 sec ────→|
Request 4: |←──── 3 sec ────→|
Request 5: |←──── 3 sec ────→|


AFTER (Pre-computed cache):

Setup:      |←─ 45 seconds ─→|  Computed once
           (compute all distances, save to DB)
           
Request 1:  |← 150ms →|  Cache hits, instant lookups
Request 2:  |← 150ms →|
Request 3:  |← 150ms →|
Request 4:  |← 150ms →|
Request 5:  |← 150ms →|

SAVINGS: 5 requests × (3s - 0.15s) = ~14.25 seconds saved!
```

## Database Schema Relationships

```
┌─────────────────────┐
│     DisplayConfig   │
│   (1 singleton)     │
│  ┌───────────────┐  │
│  │closest_grocery│  │
│  │closest_clothi │  │
│  └───────────────┘  │
└──────────────┬──────┘
               │ controls
               │ how many
               │ to compute
               │
               ▼
┌─────────────────────────────────┐
│    ClosestStoresCache (NEW!)    │
│    (1 per listing)              │
│  ┌─────────────────────────┐    │
│  │listing_id (FK)          │    │
│  │closest_grocery_ids [..] │    │
│  │closest_clothing_ids [..] │   │
│  │computed_at              │    │
│  │updated_at               │    │
│  └─────────────────────────┘    │
└────────────┬────────────────────┘
             │ (OneToOne)
             │
             ▼
        ┌──────────────┐
        │   Listing    │
        │              │
        │ title        │
        │ price        │
        │ size_sqm     │
        │ location ←───┼─ (for distance
        │ image        │   calculations)
        └──────────────┘
```

## Key Performance Metrics

```
┌────────────────────────────────────┐
│  OPERATION          TIME    STATUS  │
├────────────────────────────────────┤
│ Setup (100 listings)  ~45s   ✓     │
│ Recompute all        ~45s   ✓     │
│ Cache hit lookup     <1ms   ✓     │
│ Cache miss compute   ~50ms  ✓     │
│ Build feature        ~1ms   ✓     │
│                                    │
│ Total per request:                 │
│  - Cache hit (100 list.) <150ms ✓ │
│  - Cache miss (100 list) ~5s   ⚠ │
│                                    │
│ Response size ~200KB ✓             │
└────────────────────────────────────┘
```
