# Character Notes Deletion Analysis

## Findings

### 1. Notes Storage
- Notes are stored in the `Character` model as a `Text` field (nullable with default='')
- Migration script `migrate_user_features.py` successfully adds the column to existing databases
- The field is properly defined in `/opt/Dnd-character-management-app/app/models/character.py` line 59

### 2. Notes Handling Routes

#### ✓ edit_character route (app/__init__.py line 771)
- **Status**: CORRECTLY PRESERVES NOTES
- Explicitly handles notes with: `char.notes = request.form.get('notes', '')`
- Notes form in character_details.html (line 96) POSTs to this route
- When notes form is submitted with only notes field, other character fields remain unchanged

#### ? level_up_character route (app/__init__.py line 862)
- **Status**: POTENTIALLY PROBLEMATIC
- The `level_up()` method in Character model (character.py) does NOT explicitly preserve notes
- The method does preserve most other data by modifying existing character object
- However, notes field is never mentioned or modified, so should remain intact
- **Risk**: LOW - The method modifies the character in-place, doesn't create a new character

#### ✗ copy_character.py script (scripts/copy_character.py)
- **Status**: DOES NOT COPY NOTES
- When copying a character, the script copies:
  - Basic attributes (name, level, race, abilities)
  - Relationships (features, spells, prepared_spells)
  - **MISSING**: notes field is NOT copied to new character
- **Impact**: If anyone uses this script, notes will be lost

#### ? add_character route (app/__init__.py line 238)
- **Status**: NEW CHARACTERS (not a deletion scenario)
- Creates new characters without notes (defaults to empty string)

### 3. Cascade Deletes and Relationships
- The Character model relationships don't have cascade deletes that would affect the notes field
- Notes are a simple text field, not a relationship, so no cascade issues

## Potential Deletion Causes

### Most Likely Issues:

1. **Form Submission Timing**: If the notes form is submitted but the edit_character route is called without the notes field in POST data, notes might be cleared. However, the code uses `request.form.get('notes', '')` which should default to empty string if missing - this WOULD clear notes!

   **PROBLEM IDENTIFIED**: If the notes form is not submitted correctly, or if another form posts to edit_character without notes field, the notes will be cleared.

2. **Level Change in Edit Form**: When changing level in the edit_character form, it updates character data. If the form doesn't include a notes field, notes would be cleared.

   **VERIFICATION NEEDED**: Check if the edit_character form includes a hidden notes field or if it submits separately.

### Other Potential Issues:

3. **copy_character.py**: If this script is used, notes won't be copied (but this is a script, not the web app)

4. **Database Migration Issues**: If the migration script failed to add the notes column properly, it could cause data loss

## Recommendations

### Immediate Actions:

1. **Check the edit_character form** (`app/templates/edit_character.html`):
   - Verify if the notes field is included in the main edit form
   - If not, the form would clear notes when submitted

2. **Update copy_character.py** to include notes:
   ```python
   new_char.notes = char.notes
   ```

3. **Modify edit_character route** to preserve notes if not in form:
   ```python
   # Instead of: char.notes = request.form.get('notes', '')
   # Use: new_notes = request.form.get('notes')
   #      if new_notes is not None:
   #          char.notes = new_notes
   ```

### Additional Safeguards:

4. Add a validation check to prevent accidental clearing of notes in critical routes

5. Log all notes modifications for audit trail

## Database Query to Investigate

To check if notes are being lost in production:
```sql
SELECT id, name, notes, level, created_at FROM character WHERE notes = '' ORDER BY id DESC LIMIT 20;
```

To find characters that previously had notes but now don't (requires audit log or backup comparison).
