# Simplified View Implementation Guide

## Overview
Created a new simplified view that displays a limited number of listings with their closest metro stations and stores using a clean Leaflet-based interface.

## Configuration
All configurable numbers are at the top of `listings/views.py`:

```python
NUM_LISTINGS = 3                    # Number of listings to display
NUM_CLOSEST_STATIONS = 3            # Number of closest metro stations per listing
NUM_CLOSEST_GROCERY_STORES = 3      # Number of closest grocery stores
NUM_CLOSEST_CLOTHING_STORES = 3     # Number of closest clothing stores
```

**To adjust these numbers**, simply edit the values at the top of `listings/views.py` and restart the server.

## URLs and Endpoints

### View Page
- **URL**: `http://localhost:8902/simplified/`
- **Template**: `listings/templates/listings/map_view_simplified.html`
- **View Function**: `simplified_map_view()`

### API Endpoint
- **URL**: `http://localhost:8902/api/listings-simplified.geojson`
- **View Function**: `simplified_geojson()`
- **Response**: GeoJSON FeatureCollection with listings and their closest items

## Response Format

The API returns a GeoJSON response with this structure:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [lon, lat]
      },
      "properties": {
        "id": 1,
        "title": "Listing Title",
        "price": 1000000,
        "size_sqm": 120,
        "image_url": "...",
        "closest_stations": [
          {
            "id": 1,
            "name": "Station Name",
            "distance_m": 450.5
          }
        ],
        "closest_grocery_stores": [
          {
            "id": 1,
            "name": "Store Name",
            "distance_m": 200.3
          }
        ],
        "closest_clothing_stores": [
          {
            "id": 1,
            "name": "Store Name",
            "distance_m": 320.8
          }
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

## Frontend Features

The simplified map (`map_view_simplified.html`) includes:

1. **Clean Leaflet Map**
   - Centered on Istanbul
   - Color-coded markers for different item types
   - Automatic bounds fitting for all markers

2. **Color Legend**
   - Blue: Listings
   - Yellow: Metro Stations
   - Green: Grocery Stores
   - Pink: Clothing Stores

3. **Interactive Popups**
   - Click any listing marker to see:
     - Title and price
     - Size in sqm
     - Closest metro stations with distances
     - Closest grocery stores with distances
     - Closest clothing stores with distances

4. **Info Panel** (top right)
   - Shows data summary
   - Displays current configuration
   - Loading status

5. **Error Handling**
   - Displays friendly error messages if data fails to load
   - Console logging for debugging

## How It Works

1. **View Rendering** (`simplified_map_view`)
   - Returns the HTML template

2. **Data Loading** (JavaScript on page load)
   - Fetches data from `/api/listings-simplified.geojson`
   - Creates markers for listings

3. **API Processing** (`simplified_geojson`)
   - Retrieves limited listings using `NUM_LISTINGS`
   - For each listing, queries:
     - `NUM_CLOSEST_STATIONS` closest metro stations
     - `NUM_CLOSEST_GROCERY_STORES` closest grocery stores
     - `NUM_CLOSEST_CLOTHING_STORES` closest clothing stores
   - Returns all data in GeoJSON format

## Logging

Both views include comprehensive logging:
- API calls are logged with `[SIMPLIFIED_API_START]` and `[SIMPLIFIED_API_COMPLETE]` markers
- Individual listing processing: `[SIMPLIFIED]`
- Errors are logged with `[SIMPLIFIED_ERROR]` or `[SIMPLIFIED_API_FAILED]`

Check your Django logs to see detailed timing information.

## Quick Start

1. **Start the server**:
   ```bash
   python manage.py runserver 0.0.0.0:8902
   ```

2. **Open the map**:
   - Visit: `http://localhost:8902/simplified/`

3. **Adjust numbers** (optional):
   - Edit `NUM_*` constants at the top of `listings/views.py`
   - Restart the server

## Files Modified/Created

- ✅ `listings/views.py` - Added configuration constants, `simplified_map_view()`, `_simplified_listing_feature()`, `simplified_geojson()`
- ✅ `IstanbulPropTech/urls.py` - Added routes for `/simplified/` and `/api/listings-simplified.geojson`
- ✅ `listings/templates/listings/map_view_simplified.html` - Complete Leaflet-based template

## No Database Changes
- No migrations needed
- No model changes
- Uses existing models: `Listing`, `MetroStation`, `Clothing`, `Grocery`
