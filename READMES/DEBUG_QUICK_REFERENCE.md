# Quick Debug Logging Reference

## 🚀 Start Here

### View Debug Output While Server Runs
```bash
# Terminal 1: Start server
python manage.py runserver 0.0.0.0:8902

# Terminal 2: Watch logs live
tail -f logs/django.log
```

### Make a Test Request
```bash
# Trigger the API in another terminal
curl http://localhost:8902/api/listings.geojson
```

## 📋 Common Commands

### View Logs
```bash
# Last 50 lines
tail -50 logs/django.log

# Real-time follow
tail -f logs/django.log

# Full log file
cat logs/django.log
```

### Search Logs
```bash
# Show all API completions
grep "[API_COMPLETE]" logs/django.log

# Show only errors
grep "ERROR\|FAILED" logs/django.log

# Show config changes
grep "[CONFIG_SAVED]\|[CONFIG_LOADED]" logs/django.log

# Find slow requests (>1 second)
grep "[API_COMPLETE]" logs/django.log | grep -E "Total time: [1-9]\.[0-9]+"
```

### Analyze Performance
```bash
# Count total API calls
grep "[API_START]" logs/django.log | wc -l

# Average API response time
grep "[API_COMPLETE]" logs/django.log | grep -oP "Total time: \K[0-9.]+" | awk '{sum+=$1; count++} END {print "Average: " sum/count "s"}'

# Max response time
grep "[API_COMPLETE]" logs/django.log | grep -oP "Total time: \K[0-9.]+" | sort -rn | head -1
```

## 🎯 What To Watch For

### ✅ Healthy Indicators
```
✓ [API_COMPLETE] Total time: < 3 seconds
✓ [FEATURE_COMPLETE] Avg per feature: < 0.05 seconds  
✓ [DB_STATS] Total queries: < 400
✓ No [ERROR] entries
```

### ⚠️ Red Flags
```
⚠ [API_COMPLETE] Total time: > 5 seconds
⚠ [ERROR] or [FAILED] tags appearing
⚠ [DB_STATS] queries: > 1000
⚠ Single [FEATURE_COMPLETE] > 1 second
```

## 📊 Log Format

Each entry looks like:
```
[LEVEL] YYYY-MM-DD HH:MM:SS MODULE_NAME FUNCTION:LINE - [TAG] Details
```

Example:
```
[INFO] 2025-11-14 01:30:45 listings.views listings_geojson:72 - [API_START] listings_geojson endpoint called
```

## 🔧 Levels Explained

| Level | Use |
|-------|-----|
| **DEBUG** | Detailed per-item info |
| **INFO** | Important events, progress |
| **WARNING** | Unusual but handled |
| **ERROR** | Something failed |

## 📁 Log Location

```
/home/lofa/DEV-msi/realestate/innovate/IstanbulPropTech/logs/django.log
```

## 💡 Pro Tips

1. **Live monitoring**: Use `tail -f logs/django.log` in a separate terminal
2. **Grep multiple terms**: `grep "ERROR\|FAILED\|SLOW" logs/django.log`
3. **Count occurrences**: Append `| wc -l` to any grep
4. **Extract just times**: `grep -oP 'Total time: \K[0-9.]+'`
5. **Sort by time**: `sort -t: -k3 -rn` (reverse numeric on field 3)

## 🎓 Common Queries

**"Are requests slow today?"**
```bash
tail -100 logs/django.log | grep "[API_COMPLETE]" | tail -5
```

**"Any errors in last hour?"**
```bash
grep "ERROR" logs/django.log | tail -20
```

**"How many features processed?"**
```bash
grep "[FEATURES_PROCESSED]" logs/django.log | tail -1
```

**"Database performance?"**
```bash
grep "[DB_STATS]" logs/django.log | tail -10
```

---

**Debug Logging Status**: ✅ Active  
**Log File**: `logs/django.log`  
**Update Frequency**: Real-time
