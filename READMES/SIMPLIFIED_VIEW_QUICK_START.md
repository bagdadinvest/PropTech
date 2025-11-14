# Simplified View - Quick Reference

## 🎯 What Was Created

A new simplified mapping view that displays **limited listings** with their **closest stations and stores** - all configurable from the top of `views.py`.

## ⚙️ Configuration (at top of `listings/views.py`)

```python
NUM_LISTINGS = 3                    # 👈 Change this
NUM_CLOSEST_STATIONS = 3            # 👈 Change this  
NUM_CLOSEST_GROCERY_STORES = 3      # 👈 Change this
NUM_CLOSEST_CLOTHING_STORES = 3     # 👈 Change this
```

## 🌐 Access Points

| What | URL | Purpose |
|------|-----|---------|
| **Map View** | `http://localhost:8902/simplified/` | Interactive map with markers and popups |
| **API Data** | `http://localhost:8902/api/listings-simplified.geojson` | Raw GeoJSON data |

## 📊 Data Flow

```
Browser
   ↓
[GET /simplified/]
   ↓
simplified_map_view()
   ↓
Returns: map_view_simplified.html
   ↓
JavaScript loads GeoJSON from API
   ↓
[GET /api/listings-simplified.geojson]
   ↓
simplified_geojson()
   ↓
_simplified_listing_feature() × NUM_LISTINGS
   ↓
Returns GeoJSON FeatureCollection
   ↓
Browser renders Leaflet map with all markers
```

## 🎨 Map Features

- **Blue markers**: Listings (configurable count)
- **Yellow markers**: Metro Stations (configurable count per listing)
- **Green markers**: Grocery Stores (configurable count per listing)
- **Pink markers**: Clothing Stores (configurable count per listing)

### Interactive Features
- Click any listing marker → See all details in popup
- Includes distances for all stations/stores
- Automatic zoom-to-fit all items
- Color-coded legend at bottom-left
- Info panel at top-right showing summary

## 🔧 How to Modify

### Change Number of Listings
Edit line in `listings/views.py`:
```python
NUM_LISTINGS = 5  # was 3, now 5
```

### Change Number of Closest Stores per Listing
Edit in `listings/views.py`:
```python
NUM_CLOSEST_GROCERY_STORES = 5  # was 3, now 5
NUM_CLOSEST_CLOTHING_STORES = 5  # was 3, now 5
```

### Restart Server
```bash
python manage.py runserver 0.0.0.0:8902
```

## 📁 Files Created/Modified

```
listings/
  ├── views.py                    ✏️ MODIFIED
  │   ├── Added: NUM_* constants
  │   ├── Added: simplified_map_view()
  │   ├── Added: _simplified_listing_feature()
  │   └── Added: simplified_geojson()
  └── templates/listings/
      └── map_view_simplified.html     ✅ CREATED (Leaflet map)

IstanbulPropTech/
  └── urls.py                     ✏️ MODIFIED
      ├── Added: simplified_map_view import
      ├── Added: simplified_geojson import
      ├── Added: /simplified/ route
      └── Added: /api/listings-simplified.geojson route
```

## 📝 Example Response Format

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [28.98, 41.01] },
      "properties": {
        "id": 1,
        "title": "Beautiful Istanbul Apartment",
        "price": 1500000,
        "size_sqm": 150,
        "closest_stations": [
          { "name": "Taksim", "distance_m": 450.5 },
          { "name": "Kabataş", "distance_m": 820.3 },
          { "name": "Galata", "distance_m": 1200.0 }
        ],
        "closest_grocery_stores": [
          { "name": "Migros", "distance_m": 200.0 },
          { "name": "A101", "distance_m": 350.0 },
          { "name": "Carrefour", "distance_m": 500.0 }
        ],
        "closest_clothing_stores": [
          { "name": "Zara", "distance_m": 300.0 },
          { "name": "H&M", "distance_m": 450.0 },
          { "name": "Flo", "distance_m": 600.0 }
        ]
      }
    }
  ],
  "config": {
    "num_listings": 3,
    "num_stations": 3,
    "num_grocery_stores": 3,
    "num_clothing_stores": 3
  }
}
```

## 🚀 Ready to Use!

1. The view is **production-ready**
2. No migrations needed
3. No database changes
4. Uses existing models only
5. Full error handling
6. Comprehensive logging

## 📖 Detailed Documentation

See `SIMPLIFIED_VIEW_GUIDE.md` for complete documentation including:
- Detailed configuration options
- Logging information
- How it works internally
- Response format specifications
