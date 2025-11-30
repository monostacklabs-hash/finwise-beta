#!/bin/bash
# Apply schema descriptions to database tables and columns
# Usage: ./scripts/db/apply-schema-descriptions.sh

set -e

cd backend/migrations
python apply_schema_descriptions.py
