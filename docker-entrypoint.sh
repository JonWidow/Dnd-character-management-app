#!/bin/bash
# Entrypoint for Flask app
# Note: Database backups are managed by the host system's cron job
# See BACKUP_STRATEGY.md for setup instructions

set -e

# Start Flask
flask run --host=0.0.0.0 --port=5000 --reload
