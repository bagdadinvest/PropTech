# Store Filter - Implementation Notes

## Architecture Overview

### Data Flow
1. **Backend → Frontend**: GeoJSON with `store_type` and `name` properties
2. **Parsing**: JavaScript extracts unique types and names
3. **State Management**: `storeVisibility` object tracks what's visible
4. **Rendering**: Dynamic UI based on state
5. **Updates**: Map markers updated based on checked/unchecked items

### Component Structure

```
storeVisibility (State)
    ↓
renderStoreFilterUI() (Rendering)
    ↓
Store Type Header (Clickable)
    ├─ toggleStoreType() handler
    └─ Store Names List (Hidden/Shown)
        ├─ Individual Checkboxes
        └─ toggleStoreName() + updateStoreLayerVisibility() handler
    ↓
updateStoreLayerVisibility() (Map Update)
    ├─ Iterate through storesLayer
    ├─ Check: byType[type] AND byName[name]
    └─ setOpacity(1) or setOpacity(0)
```

## Key Design Decisions

### 1. **Opacity vs Visibility**
- **Using**: `layer.setOpacity(0)` to hide, `layer.setOpacity(1)` to show
- **Why**: 
  - Keeps markers in the layer (no performance hit)
  - Maintains popup bindings
  - Can easily apply effects (fade transitions)
  - Better UX than removing/adding

### 2. **State Duplication (Type + Name)**
```javascript
storeVisibility = {
  byType: { grocery: true, clothing: true },
  byName: { Migros: true, A101: false, ... }
}
```
- **Why**: 
  - Allows independent toggling of store type + specific store
  - Makes UI logic clearer (type header toggles all in type)
  - Easier to implement partial selection UI in future

### 3. **Dynamic Rendering on Every State Change**
```javascript
// After any toggle, re-render UI
renderStoreFilterUI()
```
- **Why**:
  - Ensures checkboxes always reflect current state
  - Simple, maintainable code
  - Performance is fine (small DOM)
  - Could be optimized later with virtual DOM if needed

### 4. **Set for Unique Store Names**
```javascript
const storesByType = {};
storesByType[type] = new Set() // Not array
```
- **Why**:
  - O(1) lookup time
  - Automatic deduplication
  - Array conversion for sorting: `Array.from(set).sort()`

## Extending to New Store Types

The system is **fully automatic** - no code changes needed to add new store types!

### Current Implementation
Backend returns: `store_type: "grocery"` or `store_type: "clothing"`

### To Add New Type
1. **Add model to backend** (`stores_layer/models.py`):
```python
class Electronics(Store):
    class Meta:
        verbose_name = "Electronics Store"
```

2. **Add to stores_geojson view** (`stores_layer/views.py`):
```python
# Electronics stores
for store in Electronics.objects.all():
    geom = store.location
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [geom.x, geom.y]},
        "properties": {
            "id": store.id,
            "name": store.name,
            "store_type": "electronics",  # NEW TYPE
        },
    })
```

3. **Frontend automatically detects it** ✅
   - `initializeStoreVisibility()` parses all types from GeoJSON
   - No JavaScript changes needed!
   - New type appears in filter panel

## Common Modifications

### Adding "Select All / Deselect All" Buttons

```javascript
// In renderStoreFilterUI(), after creating typeHeaderDiv:
const selectAllBtn = document.createElement('button');
selectAllBtn.textContent = 'All';
selectAllBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  storesByType[storeType].forEach(name => {
    storeVisibility.byName[name] = true;
  });
  storeVisibility.byType[storeType] = true;
  updateStoreLayerVisibility();
});
typeHeaderDiv.appendChild(selectAllBtn);
```

### Adding Search Filter

```javascript
// Add search input to filter panel HTML
const searchInput = document.createElement('input');
searchInput.type = 'text';
searchInput.placeholder = 'Search stores...';
searchInput.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  document.querySelectorAll('.store-name-item').forEach(item => {
    const label = item.querySelector('label').textContent.toLowerCase();
    item.style.display = label.includes(query) ? '' : 'none';
  });
});
container.insertBefore(searchInput, container.firstChild);
```

### Persisting Filter State to localStorage

```javascript
// Save state
function saveFilterState() {
  localStorage.setItem('storeVisibility', JSON.stringify(storeVisibility));
}

// Restore state
function loadFilterState() {
  const saved = localStorage.getItem('storeVisibility');
  if (saved) {
    storeVisibility = JSON.parse(saved);
  }
}

// Call after toggle
toggleStoreType() {
  // ... existing code ...
  saveFilterState();
}

toggleStoreName() {
  // ... existing code ...
  saveFilterState();
}

// Call on init
loadFilterState();
```

### Adding Store Count Indicators

```javascript
// Show "1/3" if only 1 of 3 grocery stores visible
function renderStoreFilterUI() {
  // ... existing code ...
  
  const visibleCount = storeNames.filter(name => 
    storeVisibility.byName[name]
  ).length;
  
  typeHeaderDiv.innerHTML = `
    <div class="store-type-toggle">${isExpanded ? '▼' : '▶'}</div>
    <div class="store-type-name">${storeType.charAt(0).toUpperCase()}</div>
    <div class="store-count">${visibleCount}/${storeNames.length}</div>
  `;
}
```

### Grouping Stores by Name Patterns

If you want to group stores (e.g., "Chain Stores" vs "Local Stores"):

```javascript
// Modify initializeStoreVisibility() return
const storesByTypeAndGroup = {};
storesData.features.forEach(feature => {
  const type = feature.properties.store_type;
  const name = feature.properties.name;
  const group = feature.properties.group || 'Uncategorized'; // NEW
  
  const key = `${type}__${group}`;
  if (!storesByTypeAndGroup[key]) {
    storesByTypeAndGroup[key] = new Set();
  }
  storesByTypeAndGroup[key].add(name);
});
```

## Performance Optimizations (If Needed)

### Current Performance
- 100+ stores: ✅ No issues
- 1000+ stores: ✅ Still fine (modern browsers)
- 10,000+ stores: ⚠️ Consider optimization

### Optimization Strategies

1. **Virtual Scrolling** (if >1000 stores)
```javascript
// Use a library like 'UpUp' or 'react-window'
// Only render visible items in scrollable container
```

2. **Debouncing** (if many rapid updates)
```javascript
const updateDebounced = debounce(updateStoreLayerVisibility, 100);
```

3. **Batch Updates**
```javascript
// Instead of updating after each toggle:
// - Collect all changes
// - Apply once
storesLayer.eachLayer((layer) => {
  // Single pass through all markers
  const { name, store_type } = layer.feature.properties;
  layer.setOpacity(storeVisibility.byType[store_type] && 
                   storeVisibility.byName[name] ? 1 : 0);
});
```

## Debugging Tips

### Check Current State
```javascript
console.log('Store Visibility:', storeVisibility);
console.log('Stores by Type:', storesByType);
```

### List All Markers and Their State
```javascript
storesLayer.eachLayer((layer) => {
  const name = layer.feature.properties.name;
  const type = layer.feature.properties.store_type;
  const isVisible = storeVisibility.byType[type] && 
                    storeVisibility.byName[name];
  console.log(`${name} (${type}): ${isVisible ? 'VISIBLE' : 'HIDDEN'}`);
});
```

### Test Visibility Toggle
```javascript
// In browser console:
storeVisibility.byType['grocery'] = false;
updateStoreLayerVisibility();
// Should hide all grocery stores
```

## Browser DevTools Tips

### Inspect Filter Panel
```javascript
// Expand/collapse store type programmatically
document.querySelector('.store-type-header').click();
```

### Monitor Layer Changes
```javascript
map.on('layeradd', (e) => console.log('Added:', e.layer));
map.on('layerremove', (e) => console.log('Removed:', e.layer));
```

### Check GeoJSON Data
```javascript
// In browser console after map loads:
console.log('Stores GeoJSON:', storesData);
console.log('Total features:', storesData.features.length);
```

## Future Enhancements Priority

### High Priority (User-Requested)
- [ ] "Clear All" button per type
- [ ] Show/hide all button
- [ ] Store count display (5/10 visible)

### Medium Priority (Nice-to-Have)
- [ ] Search/filter functionality
- [ ] localStorage persistence
- [ ] Color-coded store types
- [ ] Store info panel on click

### Low Priority (Advanced)
- [ ] Export filtered stores as CSV
- [ ] Route optimization between stores
- [ ] Store hours/reviews integration
- [ ] Analytics on filter usage

## Testing Checklist for Modifications

Before deploying changes:
- [ ] Filter panel renders correctly
- [ ] Store type headers expand/collapse
- [ ] Individual store checkboxes toggle
- [ ] Map markers show/hide correctly
- [ ] Partial selection works (e.g., 2 of 3 grocery stores)
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Layer control add/remove works
- [ ] No console errors
- [ ] Performance acceptable with current data

## Known Limitations

1. **No Search**: Must scroll through all stores to find one
   - *Workaround*: Implement search as described above

2. **No Persistence**: Filter state resets on page refresh
   - *Workaround*: Use localStorage approach above

3. **Fixed Panel Position**: Might overlap with layer control on small screens
   - *Workaround*: Could make panel draggable or minimize

4. **No Store Details**: Just name and type shown
   - *Workaround*: Add click handler to show more info

## Related Files

- `IstanbulPropTech/settings.py` - Django configuration
- `stores_layer/views.py` - API endpoint returning GeoJSON
- `stores_layer/models.py` - Store models (Grocery, Clothing, etc.)
- `listings/urls.py` - URL routing (if API endpoint needs configuration)

## Support & Issues

### Common Issues & Solutions

**Q: Filter panel not showing**
- A: Make sure "Stores" layer is enabled in layer control

**Q: Store markers not appearing on map**
- A: Check that stores actually exist in database with valid coordinates

**Q: Checkboxes don't update map**
- A: Check browser console for errors, verify storesLayer is added to map

**Q: Panel looks broken on mobile**
- A: Check viewport meta tag, refresh browser cache
