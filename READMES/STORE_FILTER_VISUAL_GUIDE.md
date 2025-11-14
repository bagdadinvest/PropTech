# Store Filter - Visual Guide

## UI Layout on Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         Istanbul PropTech Map                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐                                        │
│  │ 🛍️ Store Filter      │                                        │
│  ├──────────────────────┤                                        │
│  │ ▼ Grocery        [3] │                                        │
│  │   ☑ A101             │                                        │
│  │   ☑ Migros           │                                        │
│  │   ☑ Carrefour        │                                        │
│  │ ▶ Clothing       [5] │                                        │
│  │                      │  Map View                              │
│  │                      │  (Listings, Transit, Stores)           │
│  │                      │                                        │
│  │                      │  📍 Listings (always visible)          │
│  │                      │  🚇 Transit (zoom level 12+)          │
│  │                      │  🛒 Stores (toggled via layer ctrl)   │
│  │                      │                                        │
│  └──────────────────────┘                                        │
│                                                                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📍 Search Radius                                         │   │
│  │ [━━━━●━━━━━━━━━━━━━━━━━]  Distance: 2.0 km             │   │
│  │ 150 listings | 45 transit | 12 stores                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Interaction Flow Diagram

```
┌──────────────────────────────────────────────────────┐
│  User opens Layer Control menu                       │
└─────────────────────────┬──────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│  User checks "Stores" checkbox in layer control     │
└─────────────────────────┬──────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│  storesLayer is added to map                        │
│  layeradd event triggers                            │
└─────────────────────────┬──────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│  Store Filter Panel becomes visible                 │
│  renderStoreFilterUI() called                       │
│  All store types displayed (expanded by default)    │
└─────────────────────────┬──────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌──────────────────────┐         ┌──────────────────────┐
│ User clicks on       │         │ User checks/unchecks │
│ store type header    │         │ individual store     │
│ (e.g., "Grocery")    │         │                      │
└──────────────┬───────┘         └──────────┬───────────┘
               │                            │
               ▼                            ▼
    toggleStoreType()              toggleStoreName()
               │                            │
               └──────────────┬─────────────┘
                              │
                              ▼
                    updateStoreLayerVisibility()
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            Update opacity of      Re-render UI
            store markers          checkboxes
```

## Data Flow

```
Backend (Django)
    │
    ├─ stores_layer/views.py
    │  └─ stores_geojson() → GeoJSON FeatureCollection
    │     └─ Properties: id, name, store_type ("grocery"/"clothing")
    │
    └─ /api/stores.geojson endpoint
         │
         ▼
Frontend (JavaScript)
    │
    ├─ fetchJSON('/api/stores.geojson')
    │  └─ storesData = { type: 'FeatureCollection', features: [...] }
    │
    ├─ initializeStoreVisibility()
    │  └─ Parse storesData into storesByType
    │     └─ { grocery: Set['A101', 'Migros', ...], 
    │          clothing: Set['Zara', 'Flo', ...] }
    │
    ├─ renderStoreFilterUI()
    │  └─ Generate HTML for each type and store name
    │
    └─ updateStoreLayerVisibility()
       └─ Show/hide markers based on state
```

## State Management

```
storeVisibility Object
├── byType: {
│   ├── 'grocery': true/false    (Show/hide all grocery stores)
│   ├── 'clothing': true/false   (Show/hide all clothing stores)
│   └── ... (any future types)
│
└── byName: {
    ├── 'A101': true/false        (Show/hide A101 specifically)
    ├── 'Migros': true/false      (Show/hide Migros specifically)
    ├── 'Carrefour': true/false   (Show/hide Carrefour specifically)
    ├── 'Zara': true/false        (Show/hide Zara specifically)
    ├── 'Flo': true/false         (Show/hide Flo specifically)
    └── ... (all unique store names)
```

**Visibility Logic:**
```javascript
shouldShow = storeVisibility.byType[storeType] AND storeVisibility.byName[storeName]
```

A store is only shown if BOTH its type is visible AND its specific name is checked.

## Checkbox State Logic

### When User Clicks Store Type Header
```
Before: ▼ Grocery [3]  (expanded, all stores visible)
  ☑ A101
  ☑ Migros
  ☑ Carrefour

Action: User clicks "Grocery" header

After: ▶ Grocery [3]  (collapsed, all stores hidden)
  ☐ A101
  ☐ Migros
  ☐ Carrefour
```

**Effect:**
- `storeVisibility.byType['grocery']` → `false`
- All `storeVisibility.byName[storeName]` for grocery stores → `false`
- All grocery store markers disappear from map

### When User Clicks Specific Store Checkbox
```
Before: ▼ Grocery [3]
  ☑ A101
  ☑ Migros
  ☑ Carrefour

Action: User unchecks "Migros"

After: ▼ Grocery [3]
  ☑ A101
  ☐ Migros (unchecked, marker hidden)
  ☑ Carrefour
```

**Effect:**
- `storeVisibility.byName['Migros']` → `false`
- Only Migros markers disappear
- Type remains expanded
- Other stores remain visible

## Responsive Behavior

### Desktop (> 768px)
- Panel: 320px wide, top-right corner
- Padding: 15px
- Full scrollbar visible

### Tablet (481px - 768px)
- Panel: 280px wide, top-right corner
- Padding: 12px

### Mobile (< 480px)
- Panel: 95vw wide (almost full width)
- Top-right corner with minimal margins
- Reduced font sizes
- More compact padding
- Limited height to prevent blocking entire screen
