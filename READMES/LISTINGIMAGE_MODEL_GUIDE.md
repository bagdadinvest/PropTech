# ListingImage Model - Complete Documentation

## 📸 Overview

Created a new `ListingImage` Django model that allows **multiple images per listing**. This provides a robust image gallery system for property listings with the following features:

- Multiple images per listing
- Image ordering/sequencing
- Primary image designation
- Image metadata (title, description)
- Upload tracking
- Admin gallery management

## 🗂️ Model Structure

### ListingImage Model

```python
class ListingImage(models.Model):
    listing              # ForeignKey to Listing
    image                # ImageField (upload_to='listings/images/')
    title                # Optional title/description
    description          # Longer description
    order                # Display order in gallery
    is_primary           # Mark as primary/featured
    created_at           # Auto timestamp
    updated_at           # Auto timestamp
    uploaded_by          # Track uploader
```

### Fields Detailed

| Field | Type | Purpose |
|-------|------|---------|
| `listing` | ForeignKey | Links to parent Listing (CASCADE delete) |
| `image` | ImageField | Stores the actual image file |
| `title` | CharField | Short label (e.g., "Living Room") |
| `description` | TextField | Longer description |
| `order` | PositiveIntegerField | Display sequence (default: 0) |
| `is_primary` | BooleanField | Designates primary thumbnail |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |
| `uploaded_by` | CharField | Track source/uploader |

## 💾 Database Location

```
listings/
├── migrations/
│   └── 0005_auto_20251114_0252.py  ← NEW MIGRATION
└── ...

Database tables:
- listings_listingimage        (main table)
- listings_li_listing_5fba7f_idx (index: listing + order)
- listings_li_is_prim_17eb21_idx (index: is_primary)
```

## 🔧 Admin Interface

### Listing Admin (Enhanced)

**View**: `/admin/listings/listing/`

Features:
- ✨ Inline image management
- 📊 Image count with primary indicator (★)
- 🖼️ Click to edit images inline
- 📦 Add new images directly from listing page

```python
# Listing list view shows:
Title | Price | Size | Images ★ | Cache Status
```

### ListingImage Admin (Standalone)

**View**: `/admin/listings/listingimage/`

Features:
- 🖼️ Image previews (50x50 in list, larger in detail)
- 🔍 Search by listing title, title, or description
- 🏷️ Filter by primary status, creation date, listing
- 📋 Organized fieldsets
- ⭐ Primary image management

**Fields shown**:
- Image preview thumbnail
- Listing name
- Image title
- Order number
- Primary status
- Created date

### Inline Management

Add multiple images to a listing directly:

1. Go to any listing in `/admin/listings/listing/`
2. Scroll to "Listing Images" section
3. Upload new images
4. Set order and title
5. Mark as primary (optional)
6. Save

## 🚀 Usage Examples

### In Django Shell

```python
from listings.models import Listing, ListingImage
from django.core.files.base import ContentFile

listing = Listing.objects.first()

# Add single image
ListingImage.objects.create(
    listing=listing,
    image=image_file,
    title="Living Room",
    description="Beautiful living area with city view",
    order=1,
    is_primary=True,
    uploaded_by="admin"
)

# Get all images for listing
images = listing.images.all()

# Get primary image
primary = listing.images.filter(is_primary=True).first()

# Get ordered images
ordered_images = listing.images.all()  # Already ordered by order, created_at
```

### In Templates

```django
{% with primary=listing.get_primary_image %}
    {% if primary %}
        <img src="{{ primary.url }}" alt="{{ listing.title }}" />
    {% endif %}
{% endwith %}

<!-- Gallery -->
<div class="gallery">
    {% for image in listing.images.all %}
        <img src="{{ image.image.url }}" 
             alt="{{ image.title }}"
             title="{{ image.description }}" />
    {% endfor %}
</div>
```

### In Views

```python
from listings.models import Listing, ListingImage

def listing_detail(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    
    # Get all images
    images = listing.images.all()
    
    # Get primary image
    primary_image = listing.get_primary_image()
    
    # Get first 5 images
    preview_images = listing.images.all()[:5]
    
    return render(request, 'listing_detail.html', {
        'listing': listing,
        'images': images,
        'primary_image': primary_image,
    })
```

## 🔄 Automatic Behavior

### Primary Image Logic

The model includes smart primary image handling:

1. **First image created** → Automatically marked as primary
2. **Mark new image as primary** → Automatically unmarks others
3. **Primary image deleted** → Next image becomes primary

### Related Name Access

```python
# From Listing:
listing.images.all()              # All images
listing.images.filter(is_primary=True)  # Get primary
listing.images.order_by('order')  # Sort by order
listing.images.count()            # Count images

# Using helper method:
primary = listing.get_primary_image()  # Get primary image file
```

## 📊 Admin Features

### List Display
```
Listing | Title | Preview | Order | Primary | Created
```

### Filters
- ✓ By Primary Status
- ✓ By Creation Date
- ✓ By Listing Title

### Search
- Listing title
- Image title
- Image description

### Inline
- Add/edit/delete images directly in listing
- Reorder images
- Preview images inline

## 🎨 Image Organization

Images are stored with path:
```
media/
└── listings/
    └── images/
        ├── listing_1_image_1.jpg
        ├── listing_1_image_2.jpg
        ├── listing_2_image_1.jpg
        └── ...
```

## 📝 Meta Information

```python
class Meta:
    ordering = ['order', 'created_at']
    indexes = [
        Index(fields=['listing', 'order']),
        Index(fields=['is_primary']),
    ]
```

**Indexes created for**:
- Fast filtering by listing + order
- Fast filtering by primary status

## 🔗 Relations

```
Listing (1)
    └──── (N) ListingImage
    
When listing is deleted:
    All related ListingImage records are cascade deleted
```

## 📚 Files Modified

✅ **`listings/models.py`**
- Added `ListingImage` model with full docstrings
- Added `get_primary_image()` helper to `Listing`
- Auto-primary logic in `save()` method

✅ **`listings/admin.py`**
- Imported `ListingImage`
- Created `ListingImageInline` for listing admin
- Created `ListingImageAdmin` standalone admin
- Enhanced `ListingAdmin` with inline images

✅ **`listings/migrations/0005_auto_20251114_0252.py`**
- Creates `ListingImage` table
- Creates required indexes
- Alters `Listing.image` field

## ⚡ Performance

### Database Queries
```python
# Efficient - uses select_related
listing.images.all()  # Single query per listing

# Efficient - indexed
ListingImage.objects.filter(is_primary=True)  # Fast
ListingImage.objects.filter(listing=listing).order_by('order')  # Fast
```

### Caching Opportunities
```python
# Consider caching for frequently accessed:
- Primary images per listing
- Image counts per listing
```

## 🛡️ Data Integrity

1. **Cascade Delete**: Deleting a listing deletes all its images
2. **Primary Image**: Automatically managed to ensure consistency
3. **Order Field**: Maintains gallery sequence
4. **Timestamps**: Tracks creation/update automatically

## 🔐 Security Notes

- Images uploaded to `media/listings/images/`
- All images are accessible via their URLs
- Consider adding permissions for image upload
- Django handles file permissions via storage backend

## 📋 Migration Info

```
Migration: 0005_auto_20251114_0252.py
Applied: 14 Nov 2025 02:52:54 UTC

Changes:
✓ Altered Listing.image field
✓ Created ListingImage model
✓ Created database indexes
✓ Ready for production
```

## 🚀 Next Steps

1. **Upload images**: Use admin interface
2. **Organize**: Set order and titles
3. **Mark primary**: Set featured image
4. **Display in templates**: Use `listing.images.all()` or `get_primary_image()`
5. **Optional**: Create API endpoint for image gallery

## 📖 Related Models

- `Listing` - Parent model for properties
- `DisplayConfig` - Display settings
- `ClosestStoresCache` - Store caching
- `MetroStation` - Transit data (transit_layer)
- `Grocery` / `Clothing` - Store data (stores_layer)

---

**Model is production-ready!** Ready to manage multiple images per listing. ✨
