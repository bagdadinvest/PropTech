#!/bin/bash
# Test script to trigger debug logging

echo "🔍 Testing Debug Logging..."
echo "Requesting listings API..."
echo ""

# Make the API request
curl -s "http://localhost:8902/api/listings.geojson" > /dev/null

echo ""
echo "✅ Request sent!"
echo ""
echo "📋 Viewing recent log entries..."
echo ""

if [ -f logs/django.log ]; then
    tail -50 logs/django.log
else
    echo "⚠️  Log file not found at logs/django.log"
fi
