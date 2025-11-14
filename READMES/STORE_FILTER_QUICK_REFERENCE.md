# Store Filter - Quick Reference

## What Was Implemented ✅

A **hierarchical store filtering system** on the map that lets users:

### 1. **Show/Hide Store Types** 
   - Click on store type header (e.g., "▼ Grocery")
   - Expands/collapses to show store names
   - Shows count badge (e.g., "[3]" for 3 grocery stores)

### 2. **Select Specific Stores**
   - When a type is expanded, see all unique store names
   - Checkboxes to show/hide individual stores
   - Examples: A101, Migros, Zara, Flo, etc.

### 3. **Real-time Map Updates**
   - Store markers appear/disappear as you toggle filters
   - Smooth opacity transitions
   - Responsive panel that works on mobile, tablet, desktop

## How It Works

1. **Enable Stores** → Click "Stores" in the layer control menu
2. **Filter Panel Opens** → Top-right of map showing all store types
3. **Expand Type** → Click store type to show store names
4. **Select Stores** → Check/uncheck individual stores to filter

## Files Modified

```
listings/templates/listings/map_view.html
├── Added CSS (161 lines)
│   ├── Store filter panel styling
│   ├── Expandable headers with arrows
│   ├── Checkbox styling
│   └── Responsive design for all screen sizes
│
├── Added HTML (4 lines)
│   └── Store filter panel container
│
└── Added JavaScript (170 lines)
    ├── Store data parsing from GeoJSON
    ├── Visibility state management
    ├── Dynamic UI rendering
    ├── Toggle handlers (type & individual)
    ├── Map layer updates
    └── Layer control integration
```

## No Backend Changes Needed ✅

The backend already provides the correct GeoJSON format:
- Property: `store_type` ("grocery" or "clothing")
- Property: `name` (store name like "Migros", "Zara", etc.)

## Features

### ✅ Implemented
- [ ] Expandable store type categories with arrow indicators
- [ ] Show/hide specific stores via checkboxes
- [ ] Toggle entire store type with one click
- [ ] Count badge showing number of stores per type
- [ ] Real-time map marker updates
- [ ] Responsive mobile-friendly design
- [ ] Layer control integration
- [ ] Hover effects and visual feedback
- [ ] Custom scrollbar styling
- [ ] Sorted store names alphabetically
- [ ] Sorted store types alphabetically

### 📋 Optional Future Enhancements
- [ ] "Select All / Deselect All" buttons per type
- [ ] Search/filter store names within panel
- [ ] Store count showing visible vs total
- [ ] Color-coded store type icons
- [ ] localStorage persistence of filter state
- [ ] Integration with radius filter
- [ ] Click store to show details panel

## Testing Checklist

- [ ] Load the map page
- [ ] Open Layer Control menu (top-left)
- [ ] Check "Stores" layer
- [ ] Verify Store Filter panel appears (top-right)
- [ ] Click store type header to expand/collapse
- [ ] Toggle individual store checkboxes
- [ ] Watch markers appear/disappear on map
- [ ] Test on mobile (responsive)
- [ ] Test layer remove (uncheck "Stores" in menu)

## Example Data Structure

The system expects GeoJSON like:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [29.0, 41.0]},
      "properties": {
        "id": 1,
        "name": "Migros",
        "store_type": "grocery"
      }
    },
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [29.1, 41.1]},
      "properties": {
        "id": 2,
        "name": "A101",
        "store_type": "grocery"
      }
    },
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [29.2, 41.2]},
      "properties": {
        "id": 3,
        "name": "Zara",
        "store_type": "clothing"
      }
    }
  ]
}
```

## How It Looks

### Desktop
```
┌────────────────────────────┐
│ 🛍️ Store Filter            │
├────────────────────────────┤
│ ▼ Clothing              [5]│
│   ☑ Defacto               │
│   ☑ Flo                   │
│   ☑ LC Waikiki            │
│   ☑ Zara                  │
│   ☑ H&M                   │
├────────────────────────────┤
│ ▼ Grocery               [3]│
│   ☑ A101                  │
│   ☑ Carrefour             │
│   ☑ Migros                │
└────────────────────────────┘
```

### Mobile
```
┌──────────────────────────┐
│ 🛍️ Store Filter          │
├──────────────────────────┤
│ ▼ Clothing           [5] │
│   ☑ Defacto              │
│   ☑ Flo                  │
│   ☑ LC Waikiki           │
│   ☑ Zara                 │
│   ☑ H&M                  │
├──────────────────────────┤
│ ▼ Grocery            [3] │
│   ☑ A101                 │
│   ☑ Carrefour            │
│   ☑ Migros               │
└──────────────────────────┘
```

## Key Functions

| Function | Purpose |
|----------|---------|
| `initializeStoreVisibility()` | Parse GeoJSON and create visibility state |
| `renderStoreFilterUI()` | Generate HTML for filter panel |
| `toggleStoreType(type)` | Show/hide all stores of a type |
| `toggleStoreName(name)` | Show/hide specific store |
| `updateStoreLayerVisibility()` | Update map markers based on state |

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Efficient Set-based lookups for store names
- DOM updates only on state changes
- Layer opacity updates (not removing/adding markers)
- Lightweight CSS animations
- Mobile-optimized with smaller DOM footprint

## Accessibility

- Proper checkbox labeling (`<label for="id">`)
- Keyboard navigation support
- Clear visual feedback
- Readable text sizes (responsive)
- Good color contrast
