#!/bin/bash
# Reset database automatically (no confirmation)
# Usage: ./scripts/db/reset-db-auto.sh
# WARNING: This will destroy all data!

set -e

python backend/scripts/reset_db_auto.py
