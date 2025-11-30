#!/bin/bash
# Reset database with confirmation prompt
# Usage: ./scripts/db/reset-db.sh

set -e

python backend/scripts/reset_db.py
