#!/bin/bash
# Apply database indexes for optimization
# Usage: ./scripts/db/apply-indexes.sh

set -e

python backend/apply_indexes.py
