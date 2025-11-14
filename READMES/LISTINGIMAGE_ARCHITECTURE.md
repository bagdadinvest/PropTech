# ListingImage Architecture & Usage

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Django Admin Interface                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐      ┌──────────────────────────────┐ │
│  │   Listing Admin      │      │  ListingImage Admin          │ │
│  │  /admin/listing/     │      │  /admin/listingimage/        │ │
│  ├──────────────────────┤      ├──────────────────────────────┤ │
│  │ - Title              │      │ - Image preview              │ │
│  │ - Price              │      │ - Title                      │ │
│  │ - Size               │      │ - Description                │ │
│  │ - Image (legacy)     │      │ - Order                      │ │
│  │ - [Images ★] count   │      │ - Primary (checkbox)         │ │
│  │                      │      │ - Created/Updated dates      │ │
│  │ ┌────────────────┐   │      │ - Uploader                   │ │
│  │ │ Inline Images  │   │      └──────────────────────────────┘ │
│  │ │ (Inline Admin) │   │                                        │
│  │ │ - Add images   │   │      ┌──────────────────────────────┐ │
│  │ │ - Edit         │   │      │  Filtering & Search          │ │
│  │ │ - Delete       │   │      ├──────────────────────────────┤ │
│  │ │ - Reorder      │   │      │ Search by:                   │ │
│  │ │ - Set primary  │   │      │ - Listing title              │ │
│  │ └────────────────┘   │      │ - Image title                │ │
│  └──────────────────────┘      │ - Description                │ │
│                                │                              │ │
│                                │ Filter by:                   │ │
│                                │ - Primary status             │ │
│                                │ - Creation date              │ │
│                                │ - Listing name               │ │
│                                └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │
                    Django ORM   │   Admin Framework
                                 │
                ┌────────────────▼────────────────┐
                │     Django Database Layer      │
                ├───────────────────────────────┤
                │                               │
                │  listings_listing TABLE       │
                │  ─────────────────────        │
                │  - id (PK)                    │
                │  - title                      │
                │  - price                      │
                │  - size_sqm                   │
                │  - location (GIS Point)       │
                │  - image (nullable)           │
                │  - created_at                 │
                │  - updated_at                 │
                │                               │
                │  (1) ─────────────────┐       │
                │                       │       │
                │  listings_listingimage TABLE  │
                │  ──────────────────────────   │
                │  - id (PK)                    │
                │  - listing_id (FK)            │
                │  - image                      │ (N)
                │  - title                      │
                │  - description                │
                │  - order                      │
                │  - is_primary                 │
                │  - created_at                 │
                │  - updated_at                 │
                │  - uploaded_by                │
                │                               │
                │  INDEXES:                     │
                │  - (listing_id, order)        │
                │  - (is_primary)               │
                └───────────────────────────────┘
                         ▲
                         │
                    Media Storage
                         │
                ┌────────▼──────────────┐
                │ media/listings/       │
                │   images/             │
                │   ├── listing_1_1.jpg │
                │   ├── listing_1_2.jpg │
                │   ├── listing_2_1.jpg │
                │   └── ...             │
                └───────────────────────┘
```

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────┐
│         User Action in Admin Interface              │
│  (Upload image, set title, mark primary, save)      │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  Django Admin Form        │
         │  Validates & Processes    │
         └────────────┬──────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │  ListingImage Model         │
        │  .save() method runs        │
        │  - Check if primary         │
        │  - Unset other primaries    │
        │  - Set first as primary     │
        │  - Log to logger            │
        └────────────┬────────────────┘
                     │
                     ▼
       ┌──────────────────────────────┐
       │  Django ORM Saves to DB      │
       │                              │
       │  INSERT INTO                 │
       │    listings_listingimage     │
       │  VALUES (...)                │
       └────────────┬─────────────────┘
                    │
                    ▼
         ┌────────────────────────────┐
         │  File Storage (media/)     │
         │  Image file written        │
         └────────────────────────────┘
```

## 🔄 Query Flow

### Getting Images in Template

```
Django Template
      │
      ├─ {{ listing.images.all }}
      │         │
      │         ▼
      │  Django ORM Query
      │  SELECT * FROM listings_listingimage
      │  WHERE listing_id = X
      │  ORDER BY order, created_at
      │         │
      │         ▼
      │  Returns QuerySet
      │  of ListingImage objects
      │         │
      │         ▼
      │  Loop in template
      │  {{ image.image.url }}
      │  {{ image.title }}
      │  {{ image.description }}
      │
      └─ Render HTML with images
```

### Getting Primary Image

```
listing.get_primary_image()
        │
        ├─ Query: is_primary=True & listing_id=X
        │         │
        │         ├─ Found → Return image file
        │         │
        │         └─ Not found → Try first image
        │                        │
        │                        ├─ Has images → Return first
        │                        │
        │                        └─ No images → Return None
        │
        └─ Return ImageFieldFile or None
```

## 🎯 Admin Workflow

### Adding Image to Listing

```
User in ListingAdmin
      │
      ├─ Scroll to "Listing Images" section
      │
      ├─ Click "+ Add another Listing Image"
      │
      ├─ Form appears with:
      │  - Image upload
      │  - Title field
      │  - Description field
      │  - Order number
      │  - Primary checkbox
      │
      ├─ User fills in data
      │
      ├─ Click Save
      │
      ├─ ListingImage.save() runs
      │  ├─ Check if primary
      │  ├─ Unset other primaries if needed
      │  └─ Set first image as primary
      │
      └─ Image stored in media/listings/images/
         Record saved to database
```

### Managing Images

```
User visits ListingImageAdmin (/admin/listings/listingimage/)
      │
      ├─ List view shows all images
      │  ├─ Image preview (50x50px)
      │  ├─ Listing name
      │  ├─ Image title
      │  ├─ Order
      │  ├─ Primary status (checkbox)
      │  └─ Created date
      │
      ├─ Can Filter by:
      │  ├─ Primary status
      │  ├─ Creation date
      │  └─ Listing name
      │
      ├─ Can Search by:
      │  ├─ Listing title
      │  ├─ Image title
      │  └─ Description
      │
      ├─ Click image to edit:
      │  ├─ View large image (300x300px)
      │  ├─ Change title, description
      │  ├─ Change order
      │  ├─ Mark as primary
      │  └─ See upload metadata
      │
      └─ Can delete images
         (Others stay, new first becomes primary if needed)
```

## 💾 Storage Structure

```
FileSystem
│
└─ media/
   └─ listings/
      └─ images/
         ├─ listing_1_living_room_1.jpg
         ├─ listing_1_bedroom_2.jpg
         ├─ listing_1_kitchen_3.jpg
         │
         ├─ listing_2_exterior_1.jpg
         ├─ listing_2_pool_2.jpg
         │
         └─ ...

Database (PostgreSQL/SQLite)
│
└─ listings_listingimage
   ├─ id | listing_id | image | title | ... | is_primary
   ├─ 1  | 1          | listing_1_living_room_1.jpg | Living Room | ... | TRUE
   ├─ 2  | 1          | listing_1_bedroom_2.jpg | Master Bedroom | ... | FALSE
   ├─ 3  | 1          | listing_1_kitchen_3.jpg | Kitchen | ... | FALSE
   ├─ 4  | 2          | listing_2_exterior_1.jpg | Exterior | ... | TRUE
   ├─ 5  | 2          | listing_2_pool_2.jpg | Pool | ... | FALSE
   └─ ...
```

## 🔗 Relationships

```
┌──────────────┐              ┌────────────────────┐
│   Listing    │              │  ListingImage      │
├──────────────┤              ├────────────────────┤
│ id (PK)      │──────────┐   │ id (PK)            │
│ title        │          │   │ listing_id (FK)    │
│ price        │          ├──▶│ image              │
│ size_sqm     │          │   │ title              │
│ location     │          │   │ description        │
│ image (old)  │          │   │ order              │
│ created_at   │          │   │ is_primary         │
│ updated_at   │          │   │ created_at         │
└──────────────┘          │   │ updated_at         │
                          │   │ uploaded_by        │
                          └──▶└────────────────────┘
                              (1 to Many)
                              (CASCADE delete)
```

## 🎨 Admin Interface Layout

```
Listing Admin Page
┌─────────────────────────────────────────────────────┐
│  Listing Form                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ Title: [________________]                     │  │
│  │ Price: [________________]                     │  │
│  │ Size: [_____]                                 │  │
│  │ Location: [__________________________]        │  │
│  │ Image (legacy): [Choose File]                 │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Images ★ (2 images, 1 primary)                    │
│  ┌───────────────────────────────────────────────┐  │
│  │ Listing Images                                │  │
│  ├───────────────────────────────────────────────┤  │
│  │ Image | Title | Desc | Order | Primary | Date │  │
│  ├───────────────────────────────────────────────┤  │
│  │ [IMG] | Living | ... |   1   |   ☑    | Nov14│  │
│  │ [IMG] | Bedroom| ... |   2   |   ☐    | Nov14│  │
│  ├───────────────────────────────────────────────┤  │
│  │ + Add another Listing Image                  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [Save]  [Save and Continue Editing]  [Delete]     │
└─────────────────────────────────────────────────────┘
```

## 📈 Query Optimization

```python
# BAD - Multiple queries
for listing in listings:
    print(listing.images.count())  # N queries

# GOOD - Single query with prefetch
from django.db.models import Prefetch
listings = Listing.objects.prefetch_related('images')
for listing in listings:
    print(listing.images.count())  # Already cached

# GOOD - Get images ordered
images = listing.images.all()  # Uses index (listing_id, order)

# GOOD - Get primary quickly
primary = listing.images.filter(is_primary=True).first()
# Uses index (is_primary)
```

---

**Architecture is clean, well-indexed, and optimized!** ✨
