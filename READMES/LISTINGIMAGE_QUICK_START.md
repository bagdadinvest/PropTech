# ListingImage Model - Quick Reference

## 🎯 What Was Created

A new **ListingImage** Django model that allows storing **multiple images per listing** with:
- Image gallery support
- Primary/featured image designation
- Image ordering
- Metadata storage
- Admin integration

## 📊 Model Fields

```python
class ListingImage(models.Model):
    listing         # ForeignKey → Listing
    image           # ImageField (required)
    title           # CharField (optional) - e.g., "Living Room"
    description     # TextField (optional)
    order           # PositiveIntegerField (default: 0)
    is_primary      # BooleanField (default: False)
    created_at      # DateTimeField (auto)
    updated_at      # DateTimeField (auto)
    uploaded_by     # CharField (optional)
```

## 📍 Access Points

| What | Where |
|------|-------|
| **Admin Panel** | `/admin/listings/listingimage/` |
| **Inline in Listing** | `/admin/listings/listing/` |
| **Python Model** | `from listings.models import ListingImage` |

## 🔧 Basic Usage

### Add Image to Listing

```python
from listings.models import Listing, ListingImage

listing = Listing.objects.first()

ListingImage.objects.create(
    listing=listing,
    image=image_file,
    title="Living Room",
    description="Beautiful living area",
    order=1,
    is_primary=True,
)
```

### Get Images

```python
# All images for listing
listing.images.all()

# Primary image (file)
listing.get_primary_image()

# Primary image (object)
listing.images.filter(is_primary=True).first()

# Ordered images
listing.images.all()  # auto-ordered by order, created_at

# Count
listing.images.count()
```

### In Templates

```django
<!-- Primary image -->
<img src="{{ listing.get_primary_image.url }}" alt="{{ listing.title }}" />

<!-- Gallery -->
{% for image in listing.images.all %}
    <img src="{{ image.image.url }}" alt="{{ image.title }}" />
{% endfor %}
```

## 🏢 Admin Features

### Listing Admin
- Shows image count with ★ for primary
- Inline image management
- Add images directly from listing page

### ListingImage Admin
- Image preview thumbnails
- Search by listing, title, description
- Filter by primary, date, listing
- Organize display and primary status

## 🔄 Smart Behavior

1. **First image** automatically marked as primary
2. **Marking new image as primary** auto-unmarks others
3. **Deleting listing** cascade-deletes all images
4. **Images auto-ordered** by order field, then creation date

## 📂 File Storage

```
media/listings/images/
├── listing_1_photo_1.jpg
├── listing_1_photo_2.jpg
└── ...
```

## 📋 Database

- Table: `listings_listingimage`
- Indexes: `(listing, order)` and `(is_primary)`
- Migration: `0005_auto_20251114_0252.py` ✅ Applied

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **Multiple Images** | Store unlimited images per listing |
| **Ordering** | Define gallery sequence |
| **Primary Image** | Mark featured/thumbnail image |
| **Metadata** | Title, description per image |
| **Tracking** | Know when/who uploaded |
| **Admin UI** | Inline and standalone management |
| **Indexes** | Fast queries |

## 🚀 Usage Examples

### Django Shell
```python
listing = Listing.objects.first()
listing.images.all()
listing.images.count()
```

### Python Code
```python
for image in listing.images.all():
    print(f"{image.title}: {image.image.url}")
```

### Templates
```django
<div class="gallery">
  {% for img in listing.images.all %}
    <img src="{{ img.image.url }}" title="{{ img.title }}" />
  {% endfor %}
</div>
```

## 📝 Admin Tips

1. **Upload in Listing**: Go to listing admin, scroll to images section
2. **Manage Images**: Click on ListingImage in admin to manage all
3. **Set Primary**: Click checkbox on one image (auto-unmarks others)
4. **Reorder**: Change order field and save
5. **Search**: Filter by listing or search by image title

## 🔗 Relations

```
Listing (1) ──→ (N) ListingImage
```

Delete listing = Delete all images (CASCADE)

## 💡 Best Practices

- Set title for each image (helpful for users)
- Mark one image as primary per listing
- Use order field to arrange gallery
- Track uploader in `uploaded_by` field

## ⚡ Performance

- Indexed for fast queries
- Efficient with select_related
- Lazy-loaded by default

## 🛠️ Migration Status

✅ **Migration created**: `0005_auto_20251114_0252.py`
✅ **Migration applied**: 14 Nov 2025
✅ **Ready to use**: Yes

## 📚 Related Files

- `listings/models.py` - Model definition
- `listings/admin.py` - Admin interface
- `listings/migrations/0005_auto_20251114_0252.py` - Database migration

---

**Ready to use!** Upload images through Django admin. ✨
