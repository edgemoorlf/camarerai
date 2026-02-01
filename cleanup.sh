#!/bin/bash
# Project Cleanup Script
# Consolidates implementations and organizes documentation

echo "=========================================="
echo "CamareraI - Project Cleanup"
echo "=========================================="
echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p archive
mkdir -p docs/toolkit
mkdir -p docs/planning
mkdir -p docs/implementation
mkdir -p docs/reference

# Consolidate implementations
echo ""
echo "Consolidating implementations..."

# Copy streaming implementations to main names
if [ -f "streaming_voice_agent.py" ]; then
    cp streaming_voice_agent.py voice_agent.py
    echo "✓ Created voice_agent.py"
fi

if [ -f "static/app_streaming.js" ]; then
    cp static/app_streaming.js static/app.js
    echo "✓ Created static/app.js"
fi

if [ -f "templates/index_streaming.html" ]; then
    cp templates/index_streaming.html templates/index.html
    echo "✓ Created templates/index.html"
fi

# Archive old implementations
echo ""
echo "Archiving old implementations..."

if [ -f "poc_voice_agent.py" ]; then
    mv poc_voice_agent.py archive/
    echo "✓ Archived poc_voice_agent.py"
fi

# Move planning docs
echo ""
echo "Organizing planning documents..."

for file in PLAN.md PRODUCT_VISION.md INTERACTION_PATTERNS.md IMPLEMENTATION_PLAN.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/planning/
        echo "✓ Moved $file to docs/planning/"
    fi
done

# Move implementation docs
echo ""
echo "Organizing implementation documents..."

for file in STREAMING_*.md IMPLEMENTATION_STATUS.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/implementation/
        echo "✓ Moved $file to docs/implementation/"
    fi
done

# Move reference docs
echo ""
echo "Organizing reference documents..."

for file in AUDIO_FIX.md TROUBLESHOOTING.md QUICK_START.md CURRENT_STATUS.md CLEANUP.md WORKFLOW_SUMMARY.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/reference/
        echo "✓ Moved $file to docs/reference/"
    fi
done

# Summary
echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Active files:"
echo "  - voice_agent.py (main server)"
echo "  - static/app.js (main client)"
echo "  - templates/index.html (main UI)"
echo ""
echo "Documentation:"
echo "  - README.md (single source of truth)"
echo "  - docs/planning/ (original planning)"
echo "  - docs/implementation/ (technical details)"
echo "  - docs/reference/ (guides and troubleshooting)"
echo ""
echo "Next steps:"
echo "  1. Test: python3 test_all.py"
echo "  2. Start: python3 voice_agent.py"
echo "  3. Open: http://localhost:5002"
echo ""
echo "=========================================="
