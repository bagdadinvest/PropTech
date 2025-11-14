# Debug Statements & Performance Monitoring Guide

## Overview

Comprehensive debug logging has been added throughout the application to monitor database transfers, performance metrics, and identify bottlenecks. All debug output goes to both console and log files.

## What's Being Logged

### 1. **API Endpoint Logging** (`listings_geojson`)

Every API request logs:
- ✓ Request start/completion
- ✓ Configuration loading time
- ✓ Total listings vs retrieved listings
- ✓ Feature processing progress
- ✓ Total execution time
- ✓ Query count and execution time (DEBUG mode)
- ✓ Response size in KB
- ✓ Any errors encountered

**Example Output:**
```
[INFO] ================================================================================
[INFO] [API_START] listings_geojson endpoint called
[INFO] [CONFIG] DEBUG mode: True
[INFO] [CONFIG_LOADED] Time: 0.0012s | Max Listings: 100
[INFO] [DB_QUERY] Retrieved 100/500 listings | Query time: 0.0234s
[DEBUG] [DB_STATS] Queries so far: 3
[INFO] [PROGRESS] Processed 10/100 listings
[INFO] [PROGRESS] Processed 20/100 listings
...
[INFO] [FEATURES_PROCESSED] Processed 100 features | Time: 2.3456s | Avg per feature: 0.0235s
[DEBUG] [DB_STATS] Total queries executed: 347
[DEBUG] [DB_STATS] Total query time: 2.1234s
[INFO] [API_COMPLETE] ✓ Success | Total time: 2.3890s | Features returned: 100/100 | Response size: 234.56KB
[INFO] ================================================================================
```

### 2. **Per-Listing Feature Processing** (`_listing_feature`)

For each listing processed:
- ✓ Metro station lookup time
- ✓ Grocery store count and time
- ✓ Clothing store count and time
- ✓ Individual query count
- ✓ Total feature creation time

**Example Output:**
```
[DEBUG] [METRO] Listing 1 (Beautiful apartment in Kadıköy): Found nearest station 'Kadıköy' at 245.32m | Time: 0.0456s
[DEBUG] [GROCERY] Listing 1: Found 8 stores | Time: 0.0234s
[DEBUG] [CLOTHING] Listing 1: Found 5 stores | Time: 0.0189s
[DEBUG] [FEATURE_COMPLETE] Listing 1: Total time: 0.0879s | Queries: 3 | Breakdown - Metro: 0.0456s, Grocery: 0.0234s, Clothing: 0.0189s
```

### 3. **Configuration Logging** (`DisplayConfig`)

When configuration is loaded or changed:
- ✓ Configuration retrieval (cached or newly created)
- ✓ All current limits
- ✓ Configuration saves
- ✓ Deletion attempts (prevented with warning)

**Example Output:**
```
[DEBUG] [CONFIG_RETRIEVED] Current limits - Listings: 100, Grocery: 200, Clothing: 200, Metro: 100
[INFO] [CONFIG_SAVED] Updated display limits - Listings: 75, Grocery: 150, Clothing: 150, Metro: 75
[WARNING] [CONFIG_DELETE_ATTEMPTED] Deletion of DisplayConfig prevented (singleton protection)
```

## Log Files

### Console Output
Real-time display during development (when running `python manage.py runserver`)

### File Logging
- **Location**: `/home/lofa/DEV-msi/realestate/innovate/IstanbulPropTech/logs/django.log`
- **Format**: Timestamp | Level | Module | Function | Line | Message
- **Auto-rotated**: When file grows (configure in settings if needed)
- **Retention**: All debug info persists for analysis

## Access Logs

### View Real-Time Logs While Server Runs
```bash
# Terminal 1: Start server
python manage.py runserver 0.0.0.0:8902

# Terminal 2: Watch logs live
tail -f logs/django.log
```

### View All Historical Logs
```bash
# View entire log file
cat logs/django.log

# View last 50 lines
tail -50 logs/django.log

# Search for specific issues
grep "ERROR\|FAILED" logs/django.log

# Filter by app
grep "listings" logs/django.log
```

### Analytics Queries
```bash
# Count total API calls
grep "[API_START]" logs/django.log | wc -l

# Average response time
grep "[API_COMPLETE]" logs/django.log | grep -oP "Total time: \K[0-9.]+" | awk '{sum+=$1; count++} END {print "Average: " sum/count "s"}'

# Find slow requests (>1 second)
grep "[API_COMPLETE]" logs/django.log | grep -E "Total time: [1-9]\."

# Track configuration changes
grep "[CONFIG_SAVED]" logs/django.log
```

## Log Levels Explained

| Level | When Used | Example |
|-------|-----------|---------|
| **DEBUG** | Detailed per-feature info, query counts | Per-listing processing times |
| **INFO** | API calls, config loads, progress | Request start/complete, batch milestones |
| **WARNING** | Unusual but handled situations | Config deletion attempts |
| **ERROR** | Processing failures | Feature creation failed, DB connection errors |

## Performance Benchmarks

### Healthy Performance Indicators

```
✓ API_COMPLETE total time < 3 seconds (for 100 listings)
✓ Average per feature < 0.05 seconds
✓ Database query count < 400 total
✓ Response size < 500KB
```

### Red Flags to Watch

```
⚠ API_COMPLETE total time > 5 seconds
⚠ Average per feature > 0.1 seconds
⚠ Database query count > 1000
⚠ Single feature taking > 1 second
⚠ Multiple [ERROR] entries for specific listings
```

## Interpreting Output

### Scenario 1: Slow Requests
```
[INFO] [API_COMPLETE] ✓ Success | Total time: 4.5678s | Features returned: 100/100
```
**Issue**: Total time is high. Check:
- Feature processing time in detailed logs
- Metro station lookups taking too long
- Too many store counts

**Solution**: Reduce `max_listings` or optimize queries

### Scenario 2: Query Explosion
```
[DEBUG] [DB_STATS] Total queries executed: 1250
```
**Issue**: Way too many queries (should be <400 for 100 listings)

**Solution**: This indicates N+1 queries. Each listing shouldn't run independent metro/store queries.

### Scenario 3: Individual Feature Failure
```
[ERROR] [FEATURE_FAILED] Listing 42 failed: Division by zero
[DEBUG] [FEATURE_COMPLETE] Listing 41: Total time: 0.0234s
[DEBUG] [FEATURE_COMPLETE] Listing 43: Total time: 0.0245s
```
**Issue**: Feature creation failed for one listing but others work

**Solution**: The error is logged but other listings continue. Check the specific listing in database.

## Configuration in settings.py

Debug logging is configured with:
- **Console handler**: Always active during development
- **File handler**: Persists all debug info
- **Log levels**: DEBUG when `DJANGO_DEBUG=1`, INFO otherwise
- **Formatters**: Verbose format with timestamp and location info

To adjust, edit `IstanbulPropTech/settings.py` - LOGGING section.

## Disable/Reduce Logging

If logs become too verbose:

### Option 1: Reduce DEBUG Level
```python
# In settings.py, change to:
"handlers": ["console", "file"],
"level": "INFO",  # Changed from "DEBUG"
```

### Option 2: Disable File Logging
```python
# In settings.py, remove "file" from handlers:
"handlers": ["console"],  # Removed "file"
```

### Option 3: Disable Specific Modules
```python
"loggers": {
    "listings": {
        "level": "WARNING",  # Changed from "DEBUG"
    },
}
```

## Integration with Monitoring Tools

Use log files to feed into:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Datadog**
- **New Relic**
- **CloudWatch**
- **Sentry** (for error tracking)

Parse the structured log format:
```
[LEVEL] [TAG] Details
```

---

**Debug logging active** ✓  
**Next step**: Monitor the logs during production usage to identify bottlenecks!
