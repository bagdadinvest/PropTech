# Simplified View - Complete Architecture

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Browser                                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         http://localhost:8902/simplified/              │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │    LEAFLET MAP (Interactive)                     │ │   │
│  │  │                                                  │ │   │
│  │  │  🔵 Listings (18px)                             │ │   │
│  │  │  🟡 Metro Stations (14px)   <- Clickable!      │ │   │
│  │  │  🟢 Grocery Stores (14px)   <- Clickable!      │ │   │
│  │  │  🩷 Clothing Stores (14px)  <- Clickable!      │ │   │
│  │  │                                                  │ │   │
│  │  │  Legend (bottom-left)  Info Panel (top-right)   │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ▲                                     │
│                            │                                     │
│                    GET /api/listings-simplified.geojson          │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Django View   │
                    │   (Backend)     │
                    └────────┬────────┘
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
      ▼                      ▼                      ▼
  ┌─────────┐          ┌─────────┐          ┌─────────┐
  │ Listing │          │  Metro  │          │ Stores  │
  │ Objects │ (1-3)    │ Stations│ (3 each) │ (6 each)│
  └─────────┘          └─────────┘          └─────────┘
      │                     │                      │
      └─────────────────────┼──────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  GeoJSON with  │
                    │  Coordinates   │
                    │  & Distances   │
                    └────────────────┘
```

## 📊 Data Flow

```
1. USER LOADS PAGE
   └─> http://localhost:8902/simplified/
       └─> simplified_map_view()
           └─> Returns: map_view_simplified.html

2. JAVASCRIPT BOOTS UP
   └─> DOMContentLoaded event fires
       └─> loadData() function executes
           └─> Fetches: /api/listings-simplified.geojson

3. API PROCESSES REQUEST
   └─> simplified_geojson() endpoint
       ├─> Gets NUM_LISTINGS (default: 3) listings
       │
       └─> For each listing:
           ├─> Gets NUM_CLOSEST_STATIONS (default: 3) stations
           │   └─> Fetches coordinates from MetroStation table
           │
           ├─> Gets NUM_CLOSEST_GROCERY_STORES (default: 3) groceries
           │   └─> Fetches coordinates from Grocery table
           │
           └─> Gets NUM_CLOSEST_CLOTHING_STORES (default: 3) clothing
               └─> Fetches coordinates from Clothing table

4. API RETURNS GEOJSON
   └─> Contains all listings & associated items with coordinates
       └─> JavaScript receives JSON

5. JAVASCRIPT RENDERS MAP
   ├─> Creates listing markers (blue)
   ├─> Creates station markers (yellow)
   ├─> Creates grocery markers (green)
   ├─> Creates clothing markers (pink)
   └─> Fits map bounds to show all markers

6. USER INTERACTION
   └─> Click marker
       └─> Popup shows details
           └─> For listings: Full details with all related items
           └─> For stations/stores: Name + distance
```

## 🔧 Configuration Points

```
listings/views.py (Line 22-25)
│
├─ NUM_LISTINGS = 3
│  └─ Controls how many listings to fetch from database
│
├─ NUM_CLOSEST_STATIONS = 3
│  └─ For each listing, get 3 closest metro stations
│
├─ NUM_CLOSEST_GROCERY_STORES = 3
│  └─ For each listing, get 3 closest grocery stores
│
└─ NUM_CLOSEST_CLOTHING_STORES = 3
   └─ For each listing, get 3 closest clothing stores
```

## 📈 Response Sizes (Example)

```
With NUM_LISTINGS=3, NUM_CLOSEST_STATIONS=3, NUM_CLOSEST_GROCERY=3, NUM_CLOSEST_CLOTHING=3:

Listings:                    3 markers
Stations:     3 per listing = 9 markers (3 × 3)
Grocery:      3 per listing = 9 markers (3 × 3)
Clothing:     3 per listing = 9 markers (3 × 3)
                              ──────────
TOTAL:                        30 markers on map

Info Panel shows all 30 items with:
- Listing number and details
- Station/store name
- Distance in kilometers
```

## 🎨 Visual Representation

```
┌─ LISTING (ID: 1) ─────────────────────────┐
│ 🔵 Title: Beautiful Apartment             │
│ ₺1,500,000 • 150 m²                       │
│                                            │
│ 🚇 Closest Stations (3):                  │
│   1. Taksim        │ 0.45 km              │
│   2. Kabataş       │ 0.82 km              │
│   3. Galata        │ 1.20 km              │
│                                            │
│ 🛒 Closest Grocery Stores (3):            │
│   1. Migros        │ 0.20 km              │
│   2. A101          │ 0.35 km              │
│   3. Carrefour     │ 0.50 km              │
│                                            │
│ 👕 Closest Clothing Stores (3):           │
│   1. Zara          │ 0.30 km              │
│   2. H&M           │ 0.45 km              │
│   3. Flo           │ 0.60 km              │
└────────────────────────────────────────────┘
      All visible as MARKERS on the map!
```

## 🔍 Marker Details

### Listing Marker (🔵 Blue, 18px)
```
┌─ Popup Content ──────────────────┐
│ Title: Beautiful Apartment       │
│ ₺1,500,000                       │
│ 150 m²                           │
│ [Image]                          │
│                                  │
│ 🚇 Closest Metro Stations        │
│ - Taksim (0.45 km)               │
│ - Kabataş (0.82 km)              │
│ - Galata (1.20 km)               │
│                                  │
│ 🛒 Closest Grocery Stores        │
│ - Migros (0.20 km)               │
│ - A101 (0.35 km)                 │
│ - Carrefour (0.50 km)            │
│                                  │
│ 👕 Closest Clothing Stores       │
│ - Zara (0.30 km)                 │
│ - H&M (0.45 km)                  │
│ - Flo (0.60 km)                  │
└──────────────────────────────────┘
```

### Station/Store Marker (🟡🟢🩷, 14px)
```
┌─ Popup ────────────────┐
│ 🚇 Taksim               │
│ 0.45 km                │
└────────────────────────┘
```

## 📝 File Structure

```
IstanbulPropTech/
├── listings/
│   ├── views.py
│   │   ├── NUM_LISTINGS = 3 ◄── CONFIG
│   │   ├── NUM_CLOSEST_STATIONS = 3 ◄── CONFIG
│   │   ├── NUM_CLOSEST_GROCERY_STORES = 3 ◄── CONFIG
│   │   ├── NUM_CLOSEST_CLOTHING_STORES = 3 ◄── CONFIG
│   │   │
│   │   ├── simplified_map_view()
│   │   │   └─> Returns: HTML template
│   │   │
│   │   ├── _simplified_listing_feature()
│   │   │   ├─> Queries MetroStation objects
│   │   │   ├─> Queries Grocery objects
│   │   │   ├─> Queries Clothing objects
│   │   │   └─> Returns: Feature with coordinates
│   │   │
│   │   └── simplified_geojson()
│   │       └─> Returns: FeatureCollection (GeoJSON)
│   │
│   └── templates/listings/
│       └── map_view_simplified.html
│           ├─> Leaflet map initialization
│           ├─> Marker creation logic
│           ├─> Popup templates
│           ├─> Legend rendering
│           └─> Info panel updates
│
└── IstanbulPropTech/
    └── urls.py
        ├─> path("simplified/", simplified_map_view)
        └─> path("api/listings-simplified.geojson", simplified_geojson)
```

## 🚀 Quick Reference

| What | Where | How |
|------|-------|-----|
| **Change number of listings** | `views.py:24` | Edit `NUM_LISTINGS` |
| **Change number of stations** | `views.py:25` | Edit `NUM_CLOSEST_STATIONS` |
| **Change number of grocery stores** | `views.py:26` | Edit `NUM_CLOSEST_GROCERY_STORES` |
| **Change number of clothing stores** | `views.py:27` | Edit `NUM_CLOSEST_CLOTHING_STORES` |
| **View the map** | Browser | Visit `/simplified/` |
| **Get raw data** | API | Call `/api/listings-simplified.geojson` |
| **Edit map styling** | Template | Edit `map_view_simplified.html` |

---

**Ready to use!** All items display as interactive markers on the Leaflet map. 🗺️✨
