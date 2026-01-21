# Database Backup & Recovery Strategy

This project includes automated database backups to prevent data loss.

## Automatic Backups

### Setup (Host System)

Add this to your server's crontab to run backups daily at 2 AM:

```bash
crontab -e
```

Then add:

```cron
# Backup D&D database daily at 2 AM
0 2 * * * cd /opt/dnd && docker exec dnd-web python /app/scripts/backup_db.py --keep-days 30 >> /var/log/dnd-backup.log 2>&1
```

**For multiple backup schedules:**

```cron
# Daily backup at 2 AM
0 2 * * * cd /opt/dnd && docker exec dnd-web python /app/scripts/backup_db.py --keep-days 30 >> /var/log/dnd-backup.log 2>&1

# Weekly backup (Sunday 3 AM) - kept for 90 days
0 3 * * 0 cd /opt/dnd && docker exec dnd-web python /app/scripts/backup_db.py --keep-days 90 >> /var/log/dnd-backup.log 2>&1
```

### Verify Cron Setup

```bash
# List your cron jobs
crontab -l

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON
```

- Backups are stored in `/opt/backups/dnd/`
- Older backups are automatically deleted based on `--keep-days`
- Backup logs are saved to `/var/log/dnd-backup.log`

**Important:** This location is OUTSIDE the project directory, so backups survive if `/opt/dnd` is accidentally deleted.

## Manual Backup

Create an immediate backup:

```bash
python scripts/backup_db.py
```

List all available backups:

```bash
python scripts/backup_db.py --list
```

Keep backups for a custom duration:

```bash
python scripts/backup_db.py --keep-days 90
```

## Database Recovery

### Restore from specific backup:

```bash
python scripts/restore_db.py characters_20260102_150000.db
```

### Restore from most recent backup:

```bash
python scripts/restore_db.py --latest
```

### List available backups:

```bash
python scripts/restore_db.py --list
```

## Within Docker

### Manual backup (from host):

```bash
docker exec dnd-web python /app/scripts/backup_db.py
```

### Restore (from host):

```bash
docker exec -it dnd-web python /app/scripts/restore_db.py --latest
```

## Automated Backups via Host Cron

The recommended approach is to use your server's cron for reliability:

```bash
# Edit crontab
crontab -e

# Add this line (daily at 2 AM):
0 2 * * * cd /opt/dnd && docker exec dnd-web python /app/scripts/backup_db.py --keep-days 30 >> /var/log/dnd-backup.log 2>&1
```

**Why host cron?**
- ✅ Runs independently of container state
- ✅ Backup happens even if container restarts
- ✅ More reliable for production
- ✅ Works across Docker restarts

## Important Notes

⚠️ **DO NOT run these commands:**

```bash
# This will delete your database volume!
docker-compose down -v

# Instead, use:
docker-compose down
# This preserves the ./instance volume
```

✅ **SAFE way to clean up:**

```bash
# Stop containers but keep volumes
docker-compose down

# Only clean up if you've backed up first
docker volume prune
```

## Backup Storage Locations

### Current Database
- **Location:** `/opt/dnd/instance/characters.db`
- **Mounted in Docker:** `/app/instance/characters.db`

### Backups (Outside Project)
- **Location:** `/opt/backups/dnd/`
- **Survives:** Complete `/opt/dnd` deletion
- **Timestamp format:** `characters_YYYYMMDD_HHMMSS.db`

Backups are stored locally in `instance/backups/`:

```
instance/
├── backups/
│   ├── characters_20260102_140000.db
│   ├── characters_20260101_140000.db
│   └── pre_restore_20260102_150000.db    # Safety backup before restore
├── characters.db                          # Current database
```

## Recovery Workflow

If data is lost:

1. **List available backups:**
   ```bash
   python scripts/restore_db.py --list
   ```

2. **Restore from backup:**
   ```bash
   python scripts/restore_db.py --latest
   ```
   A safety backup of the corrupted DB is automatically created before restoring.

3. **Verify the restore:**
   - Check the Flask app to confirm data is back
   - Review safety backup if needed

## Additional Safeguards

- **Health checks:** Docker monitors if the database file is accessible
- **Volume persistence:** `instance/` is mounted as a volume to survive container restarts
- **.gitignore protection:** Database files are not committed to git
- **Safety backups:** A backup is created before each restore operation

## Maintenance

To manually clean old backups:

```bash
python scripts/backup_db.py --keep-days 60
```

To disable automatic cleanup (useful for testing):

```bash
python scripts/backup_db.py --no-cleanup
```
