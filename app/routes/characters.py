"""Blueprint for character management routes."""
from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import db, Character, Spell, CharacterClassModel, RaceModel, SubclassModel, Feat, CharacterClassFeature, RaceFeature, SubclassFeature
from app.models.character_struct import ClassLevel
from app.models.spell_slots import CharacterSpellSlot

characters_bp = Blueprint('characters', __name__, url_prefix='')


def ability_mod(score: int) -> int:
    try:
        return (int(score) - 10) // 2
    except Exception:
        return 0


@characters_bp.route('/add_character', methods=['GET','POST'])
@login_required
def add_character():
    if request.method == 'POST':
        level = request.form.get('level', type=int)
        if level is None or level < 1:
            level = 1

        ability_scores = [
            int(request.form['str_sc']),
            int(request.form['dex_sc']),
            int(request.form['con_sc']),
            int(request.form['int_sc']),
            int(request.form['wis_sc']),
            int(request.form['cha_sc'])
        ]

        class_name = request.form['char_class'].strip()
        char_class_model = CharacterClassModel.query.filter(
            db.func.lower(CharacterClassModel.name) == db.func.lower(class_name)
        ).first()

        new_char = Character(
            name=request.form['name'].strip(),
            char_class=class_name,
            race=request.form['race'].strip(),
            ability_scores=ability_scores,
            level=level
        )
        
        if char_class_model:
            new_char.char_class_id = char_class_model.id
        
        subclass_id = request.form.get('subclass_id', type=int)
        if subclass_id:
            new_char.subclass_id = subclass_id
        
        if current_user.is_authenticated:
            new_char.user_id = current_user.id
        
        if char_class_model:
            con_mod = new_char.sc_to_mod(new_char.con_sc)
            hit_die_val = int(char_class_model.hit_die.replace('d', '')) if 'd' in str(char_class_model.hit_die) else char_class_model.hit_die
            avg_hit_die = (hit_die_val // 2) + 1
            new_char.max_hp = hit_die_val + (level - 1) * avg_hit_die + con_mod * level
            new_char.current_hp = new_char.max_hp
        
        db.session.add(new_char)
        db.session.commit()
        
        if char_class_model:
            new_char.sync_spell_slots()
            db.session.commit()
        return redirect(url_for('characters.character_details', char_id=new_char.id))
    
    classes = CharacterClassModel.query.order_by(CharacterClassModel.name).all()
    races = RaceModel.query.order_by(RaceModel.name).all()
    return render_template('add_character.html', classes=classes, races=races)


@characters_bp.route('/characters')
@login_required
def characters():
    name = request.args.get('name')
    if not name or name == '*':
        if current_user.is_admin:
            chars = Character.query.all()
        else:
            chars = Character.query.filter_by(user_id=current_user.id).all()
        return render_template('list_characters.html', characters=chars)
    else:
        char = Character.query.filter_by(name=name).first()
        if char:
            if char.user_id == current_user.id or current_user.is_admin:
                return render_template('character_details.html', character=char)
            else:
                abort(403)
        else:
            return render_template('character_details.html', character=None)


@characters_bp.route('/characters/<int:char_id>', methods=['GET', 'POST'])
@login_required
def character_details(char_id):
    char = Character.query.get_or_404(char_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'reset_spells':
            for slot in char.spell_slots:
                slot.remaining_slots = slot.total_slots
            db.session.commit()
            flash('Spell slots reset on long rest!', 'success')
            return redirect(url_for('characters.character_details', char_id=char_id))

    cls = char.character_class_model
    
    # Calculate max spell level based on spell slots (do this early)
    max_spell_level = 0
    for slot in char.spell_slots:
        if slot.total_slots > 0:
            max_spell_level = max(max_spell_level, slot.level)
    
    # Determine which spells to display as "known"
    # For classes that know all spells, show all class spells up to their level
    # For classes that choose spells, show only what the character has learned
    spells_to_display = char.spells
    if cls and not cls.chooses_spells_to_know:
        # This class knows all spells - show all class spells up to their spell level
        spells_to_display = [s for s in cls.spells if s.level <= max_spell_level]
    else:
        # This class chooses spells - only filter if they're displaying all-known
        spells_to_display = [s for s in (char.spells or []) if s.level <= max_spell_level]
    
    known_spells_count = len(spells_to_display or [])
    max_prepared = 0
    prepared_spells = char.prepared_spells
    
    if cls and cls.spellcasting_ability:
        if cls.prepares_spells:
            ability = (cls.spellcasting_ability or "").lower()
            sc_map = {"int": char.int_sc, "wis": char.wis_sc, "cha": char.cha_sc}
            max_prepared = max(1, char.level + ability_mod(sc_map.get(ability, 10)))
        else:
            # Class doesn't prepare spells - all known spells are "prepared"
            prepared_spells = spells_to_display

    if cls:
        try:
            feats = (cls.features
                     .filter(CharacterClassFeature.level <= char.level)
                     .order_by(CharacterClassFeature.level.asc(),
                               CharacterClassFeature.name.asc())
                     .all())
        except AttributeError:
            feats = sorted(
                [f for f in (cls.features or []) if f.level <= char.level],
                key=lambda f: (f.level, f.name.lower())
            )
    else:
        feats = []

    return render_template('character_details.html',
                           character=char,
                           spells_to_display=spells_to_display,
                           known_spells_count=known_spells_count,
                           max_prepared=max_prepared,
                           prepared_spells=prepared_spells,
                           feats=feats,
                           max_spell_level=max_spell_level)


@characters_bp.route('/characters/<int:char_id>/delete', methods=['POST'])
@login_required
def delete_character(char_id: int):
    char = Character.query.get_or_404(char_id)
    db.session.delete(char)
    db.session.commit()
    flash('Character deleted.', 'success')
    return redirect(url_for('characters.characters'))


@characters_bp.route('/characters/<int:char_id>/reset_spell_slots', methods=['POST'])
@login_required
def reset_spell_slots(char_id):
    char = Character.query.get_or_404(char_id)
    
    for slot in char.spell_slots:
        slot.reset_slots()
    
    db.session.commit()
    flash(f"{char.name}'s spell slots have been reset (long rest).", 'success')
    return redirect(url_for('characters.character_details', char_id=char.id))


@characters_bp.route('/api/characters')
@login_required
def api_characters():
    name = request.args.get('q', '')
    query = Character.query
    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    
    if name:
        chars = query.filter(Character.name.ilike(f"%{name}%")).all()
    else:
        chars = query.all()

    result = []
    for char in chars:
        result.append({
            "id": char.id,
            "name": char.name,
            "level": char.level,
            "race": char.race,
            "char_class": char.char_class.name if char.char_class else None,
            "max_hp": char.max_hp,
            "current_hp": char.current_hp,
        })

    return jsonify(result)


@characters_bp.route('/api/characters/<int:char_id>/spell-slots/<int:slot_id>/toggle', methods=['POST'])
@login_required
def toggle_spell_slot(char_id, slot_id):
    """Toggle a spell slot as used/available."""
    char = Character.query.get_or_404(char_id)
    
    if not current_user.is_admin and char.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    slot = CharacterSpellSlot.query.filter_by(id=slot_id, character_id=char_id).first_or_404()
    
    try:
        data = request.get_json() or {}
        use_slot = data.get('use_slot', True)
        
        if use_slot:
            if slot.remaining_slots > 0:
                slot.remaining_slots -= 1
        else:
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


@characters_bp.route('/characters/<int:char_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_character(char_id: int):
    char = Character.query.get_or_404(char_id)
    cls = char.character_class_model

    if request.method == 'POST':
        nm = request.form.get('name')
        if nm: char.name = nm.strip()

        rc = request.form.get('race')
        if rc: char.race = rc.strip()

        old_con_sc = char.con_sc

        lvl = request.form.get('level', type=int)
        if lvl and lvl >= 1:
            old_level = char.level
            char.level = lvl
            if old_level != lvl:
                char.sync_spell_slots()

        if 'notes' in request.form:
            char.notes = request.form.get('notes', '')

        for key in ['str_sc','dex_sc','con_sc','int_sc','wis_sc','cha_sc']:
            val = request.form.get(key, type=int)
            if val is not None:
                setattr(char, key, val)

        ac = request.form.get('armor_class', type=int)
        if ac is not None and ac >= 1:
            char.armor_class = ac

        con_changed = char.con_sc != old_con_sc
        if (lvl and lvl >= 1 and old_level != lvl) or con_changed:
            if char.char_class:
                con_mod = char.sc_to_mod(char.con_sc)
                hit_die_val = int(char.char_class.hit_die.replace('d', '')) if 'd' in str(char.char_class.hit_die) else char.char_class.hit_die
                avg_hit_die = (hit_die_val // 2) + 1
                char.max_hp = hit_die_val + (char.level - 1) * avg_hit_die + con_mod * char.level
                char.current_hp = char.max_hp

        spell_ids = request.form.getlist('known_spells')
        if spell_ids is not None:
            chosen = Spell.query.filter(Spell.id.in_(list(map(int, spell_ids)))).all()
            char.spells.clear()
            char.spells.extend(chosen)

        cls = char.character_class_model
        max_prepared = 0
        if cls and cls.prepares_spells:
            ability = (cls.spellcasting_ability or "").lower()
            sc_map = {"int": char.int_sc, "wis": char.wis_sc, "cha": char.cha_sc}
            ability_score = sc_map.get(ability, 10)
            max_prepared = max(1, char.level + ability_mod(ability_score))

        known_ids = {s.id for s in (char.spells or [])}
        if getattr(char, 'prepared_spells', None) is not None:
            pruned = [s for s in char.prepared_spells if s.id in known_ids]
            if max_prepared and len(pruned) > max_prepared:
                kept = pruned[:max_prepared]
                char.prepared_spells = kept
                flash(f'Prepared spells trimmed to {max_prepared} due to level/ability changes.', 'warning')
            else:
                char.prepared_spells = pruned

        db.session.commit()
        flash('Character updated.', 'success')
        return redirect(url_for('characters.character_details', char_id=char.id))

    max_spell_level = 0
    for slot in char.spell_slots:
        if slot.total_slots > 0:
            max_spell_level = max(max_spell_level, slot.level)
    
    if cls:
        available_spells = [s for s in cls.spells if s.level <= max_spell_level]
    else:
        available_spells = Spell.query.filter(Spell.level <= max_spell_level).order_by(Spell.level.asc(), Spell.name.asc()).all()

    return render_template('edit_character.html',
                           character=char,
                           available_spells=available_spells)


@characters_bp.route('/characters/<int:char_id>/level_up', methods=['GET', 'POST'])
@login_required
def level_up_character(char_id):
    character = Character.query.get_or_404(char_id)

    if request.method == 'GET':
        character.max_hp_before = character.max_hp
        character.max_hp_after = character.calculate_max_hp()

        character.spell_slots_before = character.spell_slots.copy() if character.spell_slots else {i: 0 for i in range(1, 6)}
        character.spell_slots_after = character.get_new_spell_slots() if hasattr(character, 'get_new_spell_slots') else character.spell_slots_before

        new_features = character.get_new_features_for_level() if hasattr(character, 'get_new_features_for_level') else []
        asi_options = character.get_asi_options() if hasattr(character, 'get_asi_options') else []
        
        available_feats = []
        new_level = character.level + 1
        ASI_LEVELS = {
            "Fighter": [4, 6, 8, 12, 14, 16, 19],
            "Paladin": [4, 8, 12, 16, 19],
            "Rogue": [4, 8, 10, 12, 16, 19],
            "Bard": [4, 8, 12, 16, 19],
        }
        
        if character.char_class and character.char_class.name in ASI_LEVELS:
            if new_level in ASI_LEVELS[character.char_class.name]:
                available_feats = Feat.query.all()

        return render_template(
            'level_up.html',
            character=character,
            new_features=new_features,
            asi_options=asi_options,
            available_feats=available_feats
        )

    if request.method == 'POST':
        asi_choice = request.form.get('asi_choice')
        if asi_choice:
            character.apply_asi_choice(int(asi_choice))

        new_features = character.get_new_features_for_level() if hasattr(character, 'get_new_features_for_level') else []
        for feature in new_features:
            choice = request.form.get(f'feature_{feature.id}')
            if choice:
                character.apply_feature_choice(feature, int(choice))

        feat_choice = request.form.get('feat_choice')
        if feat_choice:
            feat = Feat.query.get(int(feat_choice))
            if feat and feat not in character.feats:
                character.feats.append(feat)

        new_spell_ids = request.form.getlist('new_spells')
        if new_spell_ids:
            character.learn_new_spells([int(sid) for sid in new_spell_ids])

        character.level_up()

        db.session.commit()
        flash(f"{character.name} is now level {character.level}!", "success")
        return redirect(url_for('characters.character_details', char_id=character.id))


@characters_bp.route("/api/characters/<int:char_id>/known-spells", methods=["GET"])
@login_required
def get_known_spells(char_id: int):
    """Get current known spells for a character as JSON."""
    char = Character.query.get_or_404(char_id)
    
    if char.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    cls = char.character_class_model
    
    # Determine which spells to return based on class
    spells = char.spells
    if cls and not cls.chooses_spells_to_know:
        # Class knows all spells
        spells = cls.spells
    
    # Filter by max spell level
    max_spell_level = 0
    for slot in char.spell_slots:
        if slot.total_slots > 0:
            max_spell_level = max(max_spell_level, slot.level)
    
    spells = [s for s in (spells or []) if s.level <= max_spell_level]
    
    return jsonify({
        'spells': [
            {'id': s.id, 'name': s.name, 'level': s.level}
            for s in spells
        ],
        'known_ids': [s.id for s in char.spells],
        'prepared_ids': [s.id for s in char.prepared_spells],
        'max_spell_level': max_spell_level
    })


@characters_bp.route("/characters/<int:char_id>/manage_known_spells", methods=["POST"])
@login_required
def manage_known_spells(char_id: int):
    """Update which spells a character knows (for classes that choose spells)."""
    char = Character.query.get_or_404(char_id)
    
    if char.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    cls = char.character_class_model
    if not cls or not cls.chooses_spells_to_know:
        flash("This class does not choose spells to know.", "warning")
        return redirect(url_for('characters.character_details', char_id=char.id))
    
    ids = request.form.getlist("known_spells")
    ids_int = []
    for x in ids:
        try:
            ids_int.append(int(x))
        except Exception:
            pass

    # Get available spells for this class
    available_ids = {s.id for s in (cls.spells or [])}
    ids_int = [i for i in ids_int if i in available_ids]
    
    # Calculate max spells known for this level
    max_known = 0
    if cls:
        # This should ideally come from ClassLevel.spells_known
        # For now, use a simple calculation or get from ClassLevel
        class_level = db.session.query(ClassLevel).filter_by(
            class_id=cls.id,
            level=char.level
        ).first()
        if class_level and class_level.spells_known:
            max_known = class_level.spells_known
    
    if max_known and len(ids_int) > max_known:
        ids_int = ids_int[:max_known]
        flash(f"Known spell limit reached ({max_known}). Extra selections were ignored.", "warning")
    
    chosen = Spell.query.filter(Spell.id.in_(ids_int)).all()
    char.spells.clear()
    char.spells.extend(chosen)
    
    # If any prepared spells are no longer known, remove them
    char.prepared_spells[:] = [s for s in char.prepared_spells if s in chosen]
    
    db.session.commit()
    flash("Known spells updated.", "success")
    return redirect(url_for("characters.character_details", char_id=char.id))


@characters_bp.route("/characters/<int:char_id>/prepare_spells", methods=["POST"])
@login_required
def prepare_spells(char_id: int):
    char = Character.query.get_or_404(char_id)

    cls = char.character_class_model
    max_prepared = 0
    if cls and cls.prepares_spells:
        ability = (cls.spellcasting_ability or "").lower()
        sc_map = {"int": char.int_sc, "wis": char.wis_sc, "cha": char.cha_sc}
        ability_score = sc_map.get(ability, 10)
        max_prepared = max(1, char.level + ability_mod(ability_score))

    ids = request.form.getlist("prepared_spells")
    ids_int = []
    for x in ids:
        try:
            ids_int.append(int(x))
        except Exception:
            pass

    known_ids = {s.id for s in (char.spells or [])}
    ids_int = [i for i in ids_int if i in known_ids]

    if max_prepared and len(ids_int) > max_prepared:
        ids_int = ids_int[:max_prepared]
        flash(f"Prepared spell limit reached ({max_prepared}). Extra selections were ignored.", "warning")

    chosen = Spell.query.filter(Spell.id.in_(ids_int)).all()
    char.prepared_spells = chosen

    db.session.commit()
    flash("Prepared spells saved.", "success")
    return redirect(url_for("characters.character_details", char_id=char.id))


@characters_bp.route("/characters/<int:char_id>/toggle_favorite", methods=["POST"])
@login_required
def toggle_favorite(char_id: int):
    char = Character.query.get_or_404(char_id)
    
    if char.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    char.is_favorite = not char.is_favorite
    db.session.commit()
    
    return jsonify({'favorite': char.is_favorite})
