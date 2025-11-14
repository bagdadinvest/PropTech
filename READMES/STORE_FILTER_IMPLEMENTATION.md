# Store Filter Implementation

## Overview
A hierarchical store filtering system has been added to the map view that allows users to:
- **Toggle store types** (Grocery, Clothing, etc.) - show/hide entire categories
- **Expand/collapse store types** - reveals submenu with all store names in that category
- **Select specific stores** - checkboxes to show/hide individual stores

## Changes Made

### 1. UI Styling (map_view.html - CSS Section)
Added comprehensive styling for the store filter panel:

- **`.store-filter-panel`**: Fixed positioned panel at top-right, responsive design
- **`.store-type-header`**: Clickable header with toggle arrow (▶/▼), store type name, and count badge
- **`.store-type-toggle`**: Visual indicator showing expand/collapse state
- **`.store-names-list`**: Container for individual store checkboxes, hidden by default, shows when expanded
- **`.store-name-item`**: Individual store checkbox with label
- Custom scrollbar styling for better UX

**Responsive breakpoints:**
- Desktop (normal)
- Tablet (max-width: 768px)
- Mobile (max-width: 480px)

### 2. HTML Structure (map_view.html - Body Section)
Added the store filter panel DOM element:
```html
<!-- Store Filter Panel -->
<div class="store-filter-panel" id="storeFilterPanel">
  <h3>🛍️ Store Filter</h3>
  <div id="storeTypesContainer"></div>
</div>
```

### 3. JavaScript Logic (map_view.html - Script Section)

#### Data Structure
```javascript
const storeVisibility = {
  byType: {},    // { 'grocery': true, 'clothing': true }
  byName: {},    // { 'Migros': true, 'A101': false, ... }
};
```

#### Key Functions

**`initializeStoreVisibility()`**
- Parses GeoJSON store data to extract unique store types and names
- Returns `storesByType` object: `{ 'grocery': Set['Migros', 'A101', ...], 'clothing': Set['Zara', 'Flo', ...] }`
- Initializes all stores as visible by default

**`renderStoreFilterUI()`**
- Dynamically generates the filter panel UI
- Creates expandable store type sections
- Generates checkboxes for each store name
- Updates toggle arrows based on expansion state
- Shows count badge for each store type

**`toggleStoreType(storeType)`**
- Toggles visibility of entire store type category
- Cascades toggle to all stores in that type
- Triggers UI update

**`toggleStoreName(storeName)`**
- Toggles visibility of individual store

**`updateStoreLayerVisibility()`**
- Iterates through all store markers on the map layer
- Shows/hides markers based on: `storeVisibility.byType[type] AND storeVisibility.byName[name]`
- Re-renders the UI to reflect current state

#### Layer Control Integration
- Renders filter UI on map initialization
- Shows filter panel when stores layer is added via layer control
- Hides all stores when layer is removed via layer control
- Maintains filter state even when layer is toggled

## User Interaction Flow

1. **User enables Stores layer** via layer control menu
2. **Filter panel appears** at top-right showing all store types
3. **User clicks on store type header** (e.g., "Grocery") to expand/collapse
4. **Submenu with store names appears** (e.g., "Migros", "A101", etc.)
5. **User checks/unchecks individual stores** to show/hide specific ones
6. **Map updates in real-time** showing only selected stores
7. **Toggle store type header** to quickly show/hide all stores of that type

## Example UI Structure

```
🛍️ Store Filter
━━━━━━━━━━━━━━━━━━━━━━━━
▼ Grocery          [3]
  ☑ A101
  ☑ Migros
  ☑ Carrefour
━━━━━━━━━━━━━━━━━━━━━━━━
▶ Clothing         [5]
  (hidden, click to expand)
```

## Technical Details

### Dependencies
- Leaflet.js (already in use for mapping)
- GeoJSON format with properties: `name`, `store_type`

### Store Type Enumeration
The system automatically discovers store types from the backend GeoJSON response:
- `store_type: "grocery"`
- `store_type: "clothing"`
- (extensible to new types without code changes)

### Performance Considerations
- Uses `Set()` for efficient unique store name lookups
- Efficient layer visibility updates using Leaflet's `setOpacity()`
- DOM rendering only on state changes, not on every interaction

### Browser Compatibility
- Modern browsers with ES6 support (sets, arrow functions)
- Leaflet layers and events compatibility

## Future Enhancements

1. **"Select All" / "Deselect All" buttons** for each type
2. **Search/filter** store names within the panel
3. **Store count indicators** showing how many are currently visible
4. **Color-coded store type icons** in the filter panel
5. **Persistence** of filter preferences using localStorage
6. **Integration with radius filter** to count stores within selected types
7. **Store details panel** showing additional info when store is clicked

## Files Modified

- `/listings/templates/listings/map_view.html`
  - Added CSS styling for store filter panel
  - Added HTML structure for filter panel
  - Added JavaScript logic for filtering, toggling, and UI rendering

## Files NOT Modified (No Changes Needed)

- `/stores_layer/models.py` - Already properly structured with `store_type` in GeoJSON
- `/stores_layer/views.py` - Already returns proper GeoJSON with store_type property
- No database migrations needed
