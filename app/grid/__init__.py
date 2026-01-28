# /opt/dnd/grid/__init__.py
from flask import Blueprint, render_template, jsonify
from app.extensions import socketio
from flask_socketio import join_room, leave_room, emit
from flask_login import current_user
from app.models.character import Character
from app.models.encounter import Encounter, CombatParticipant
from app.models import db

# All grid routes will live under /grid/...
grid_bp = Blueprint("grid", __name__, url_prefix="/grid")

# ---------- In-memory cache for active sessions ----------
grids = {}

def _room(code: str) -> str:
    return f"grid:{code}"

def _get_or_create_encounter(code: str) -> Encounter:
    """Get encounter from cache or load/create from DB"""
    if code in grids:
        return grids[code]["encounter"]
    
    # Try to load from database
    encounter = Encounter.query.filter_by(session_code=code).first()
    
    if not encounter:
        # Create new encounter
        encounter = Encounter(session_code=code, name=f"Encounter {code}")
        db.session.add(encounter)
        db.session.commit()
    
    # Cache it with grid metadata
    grids[code] = {
        "encounter": encounter,
        "w": 100,
        "h": 100,
        "cell_px": 48,
        "tokens": {}
    }
    
    # Load tokens from DB into cache
    for participant in encounter.participants:
        grids[code]["tokens"][participant.id] = {
            "id": participant.id,
            "name": participant.name,
            "x": participant.x,
            "y": participant.y,
            "color": participant.color,
            "character_id": participant.character_id
        }
    
    return encounter

# ---------- HTTP routes ----------
@grid_bp.route("/<code>")
def grid_view(code):
    return render_template("grid.html", code=code)

@grid_bp.route("/api/characters/<int:char_id>")
def get_character_stats(char_id):
    """Fetch character stats for grid display"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    
    character = Character.query.get(char_id)
    if not character or character.user_id != current_user.id:
        return jsonify({"error": "Not found"}), 404
    
    # Get spell slots from character's spell_slots relationship
    spell_slots = []
    try:
        if character.spell_slots:
            for slot in sorted(character.spell_slots, key=lambda s: s.level):
                spell_slots.append({
                    "id": slot.id,
                    "level": slot.level,
                    "total_slots": slot.total_slots,
                    "remaining_slots": slot.remaining_slots,
                    "used": slot.total_slots - slot.remaining_slots
                })
    except Exception as e:
        # Continue without spell slots rather than failing
        pass
    
    return jsonify({
        "id": character.id,
        "name": character.name,
        "hit_points": character.max_hp,
        "current_hp": character.current_hp,
        "spell_slots": spell_slots
    })

@grid_bp.route("/api/characters")
def get_characters():
    """Fetch current user's characters for token spawning"""
    if not current_user.is_authenticated:
        return jsonify([])
    
    characters = Character.query.filter_by(user_id=current_user.id).all()
    return jsonify([
        {"id": c.id, "name": c.name}
        for c in characters
    ])

# ---------- Socket.IO handlers ----------
@socketio.on("join_grid")
def on_join_grid(data):
    code = (data or {}).get("code")
    user = (data or {}).get("user") or "anon"
    if not code:
        emit("error", {"msg": "missing code"})
        return
    
    # Load/create encounter
    encounter = _get_or_create_encounter(code)
    join_room(_room(code))
    emit("presence", {"user": user, "action": "join"}, to=_room(code))

@socketio.on("leave_grid")
def on_leave_grid(data):
    code = (data or {}).get("code")
    user = (data or {}).get("user") or "anon"
    leave_room(_room(code))
    emit("presence", {"user": user, "action": "leave"}, to=_room(code))

@socketio.on("request_state")
def on_request_state(data):
    code = (data or {}).get("code")
    encounter = _get_or_create_encounter(code)
    grid_data = grids[code]
    tokens = list(grid_data["tokens"].values())
    emit("state", {
        "exists": True,
        "grid": {"w": grid_data["w"], "h": grid_data["h"], "cell_px": grid_data["cell_px"], "name": code},
        "tokens": tokens
    })

@socketio.on("spawn_token")
def on_spawn_token(data):
    code = (data or {}).get("code")
    if not code:
        return
    
    encounter = _get_or_create_encounter(code)
    grid_data = grids[code]
    
    # Create database record
    participant = CombatParticipant(
        encounter_id=encounter.id,
        character_id=(data or {}).get("character_id"),
        name=(data or {}).get("name") or "Token",
        x=int((data or {}).get("x", 0)),
        y=int((data or {}).get("y", 0)),
        color=(data or {}).get("color") or "#444444"
    )
    
    # Clamp coordinates
    participant.x = max(0, min(grid_data["w"] - 1, participant.x))
    participant.y = max(0, min(grid_data["h"] - 1, participant.y))
    
    db.session.add(participant)
    db.session.commit()
    
    # Add to cache
    tok_dict = {
        "id": participant.id,
        "name": participant.name,
        "x": participant.x,
        "y": participant.y,
        "color": participant.color,
        "character_id": participant.character_id
    }
    grid_data["tokens"][participant.id] = tok_dict

    emit("token_spawned", tok_dict, to=_room(code))
    emit("state", {
        "exists": True,
        "grid": {"w": grid_data["w"], "h": grid_data["h"], "cell_px": grid_data["cell_px"], "name": code},
        "tokens": list(grid_data["tokens"].values())
    }, to=_room(code))

@socketio.on("move_token")
def on_move_token(data):
    code = (data or {}).get("code")
    tid  = int((data or {}).get("token_id", 0))
    x    = int((data or {}).get("x", 0))
    y    = int((data or {}).get("y", 0))
    
    encounter = _get_or_create_encounter(code)
    grid_data = grids[code]
    
    # Update cache
    tok = grid_data["tokens"].get(tid)
    if not tok:
        return
    
    x = max(0, min(grid_data["w"] - 1, x))
    y = max(0, min(grid_data["h"] - 1, y))
    tok["x"] = x
    tok["y"] = y
    
    # Update database
    participant = CombatParticipant.query.get(tid)
    if participant:
        participant.x = x
        participant.y = y
        db.session.commit()
    
    emit("token_moved", tok, to=_room(code))

@socketio.on("remove_token")
def on_remove_token(data):
    code = (data or {}).get("code")
    tid  = int((data or {}).get("token_id", 0))
    
    encounter = _get_or_create_encounter(code)
    grid_data = grids[code]
    
    # Remove from cache
    if tid in grid_data["tokens"]:
        del grid_data["tokens"][tid]
    
    # Remove from database
    CombatParticipant.query.filter_by(id=tid).delete()
    db.session.commit()
    
    emit("token_removed", {"token_id": tid}, to=_room(code))

@grid_bp.route("/spell-slots/<int:slot_id>/toggle", methods=["POST"])
def toggle_spell_slot_grid(slot_id):
    """Toggle a spell slot for the grid (no auth required for testing)."""
    from app.models.spell_slots import CharacterSpellSlot
    from flask import request
    
    try:
        slot = CharacterSpellSlot.query.get_or_404(slot_id)
        data = request.get_json() or {}
        use_slot = data.get('use_slot', True)
        
        if use_slot:
            # User wants to use a slot (decrement remaining)
            if slot.remaining_slots > 0:
                slot.remaining_slots -= 1
        else:
            # User wants to restore a slot (increment remaining)
            if slot.remaining_slots < slot.total_slots:
                slot.remaining_slots += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'remaining_slots': slot.remaining_slots,
            'total_slots': slot.total_slots
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grid_bp.route("/characters/<int:char_id>/hp", methods=["POST"])
def update_character_hp(char_id):
    """Update character's current HP."""
    from flask import request
    
    try:
        character = Character.query.get_or_404(char_id)
        data = request.get_json() or {}
        new_hp = data.get('current_hp', character.current_hp)
        
        # Ensure HP doesn't go below 0 or above max
        new_hp = max(0, min(new_hp, character.max_hp))
        character.current_hp = new_hp
        
        db.session.commit()
        return jsonify({
            'success': True,
            'current_hp': character.current_hp,
            'max_hp': character.max_hp
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
