# app.py
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app.models import db, Character, Skill, Spell, CharacterClassModel, RaceModel, ClassSpellSlots, User, Feat
from app.models.character_struct import CharacterClassFeature, RaceFeature, SubclassFeature, SubclassModel
from app.models.spell_slots import CharacterSpellSlot
from app.grid import grid_bp
from app.routes.assets import assets_bp
from app.extensions import socketio
from sqlalchemy import func
import os

app = Flask(__name__)

# --- Instance folder & absolute SQLite path ---
basedir = os.path.abspath(os.path.dirname(__file__))         # /opt/dnd
instance_path = os.path.join(basedir, "../instance")            # /opt/dnd/instance
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, "characters.db")       # /opt/dnd/instance/characters.db
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
with app.app_context():
    db.create_all()

socketio.init_app(app)
app.register_blueprint(grid_bp)
app.register_blueprint(assets_bp)

# ---------- Jinja Filters ----------
@app.template_filter('parse_proficiencies')
def parse_proficiencies(items):
    """
    Parse proficiencies list, handling both choice-based and regular items.
    Items starting with "Choose X from:" are separated from regular items.
    """
    if not items:
        return {'regular': [], 'choices': []}
    
    regular = []
    choices = []
    
    for item in items:
        item = item.strip()
        if item.lower().startswith('choose'):
            choices.append(item)
        else:
            regular.append(item)
    
    return {'regular': regular, 'choices': choices}

@app.template_filter('ensure_list')
def ensure_list(value):
    """Ensure value is a list, handling strings and lists."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Try to split by comma or multiple spaces
        if ',' in value:
            return [item.strip() for item in value.split(',') if item.strip()]
        else:
            return [item.strip() for item in value.split() if item.strip()]
    return []

# ---------- Helpers ----------
def ability_mod(score: int) -> int:
    try:
        return (int(score) - 10) // 2
    except Exception:
        return 0

def _class_row_for(character):
    name = (character.char_class.name if character.char_class else "").strip()
    if not name:
        return None
    return (CharacterClassModel.query
            .filter(db.func.lower(CharacterClassModel.name) == db.func.lower(name))
            .first())

def _require_admin():
    """Helper to check admin access."""
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('home.html')


# ========== AUTHENTICATION ROUTES ==========

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip() or None
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username:
            flash('Username is required.', 'error')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        theme = request.form.get('theme', 'light')
        
        # Validate email uniqueness
        if email and email != current_user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash('Email already in use.', 'error')
                return redirect(url_for('user_profile'))
        
        current_user.email = email if email else None
        current_user.theme_preference = theme
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('user_profile'))
    
    return render_template('user_profile.html', user=current_user)


@app.route('/user/settings/password', methods=['POST'])
@login_required
def change_password():
    current_pass = request.form.get('current_password', '')
    new_pass = request.form.get('new_password', '')
    confirm_pass = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_pass):
        flash('Current password is incorrect.', 'error')
    elif len(new_pass) < 6:
        flash('New password must be at least 6 characters.', 'error')
    elif new_pass != confirm_pass:
        flash('Passwords do not match.', 'error')
    else:
        current_user.set_password(new_pass)
        db.session.commit()
        flash('Password changed successfully.', 'success')
    
    return redirect(url_for('user_profile'))


def get_skills():
    skills = Skill.query.all()
    return jsonify([skill.to_dict() for skill in skills])


@app.route('/add_character', methods=['GET','POST'])
def add_character():
    if request.method == 'POST':
        # level (>=1)
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

        # Look up the class by name
        class_name = request.form['char_class'].strip()
        char_class_model = CharacterClassModel.query.filter(
            db.func.lower(CharacterClassModel.name) == db.func.lower(class_name)
        ).first()

        # Create character
        new_char = Character(
            name=request.form['name'].strip(),
            char_class=class_name,
            race=request.form['race'].strip(),
            ability_scores=ability_scores,
            level=level
        )
        
        # Link to the class model if found
        if char_class_model:
            new_char.char_class_id = char_class_model.id
        
        # Handle subclass if provided
        subclass_id = request.form.get('subclass_id', type=int)
        if subclass_id:
            new_char.subclass_id = subclass_id
        
        # Assign to current user
        if current_user.is_authenticated:
            new_char.user_id = current_user.id
        
        # Calculate initial HP using the class model directly
        if char_class_model:
            con_mod = new_char.sc_to_mod(new_char.con_sc)
            hit_die_val = int(char_class_model.hit_die.replace('d', '')) if 'd' in str(char_class_model.hit_die) else char_class_model.hit_die
            # HP = hit_die (level 1) + (level - 1) * average_hit_die + con_mod * level
            avg_hit_die = (hit_die_val // 2) + 1  # Average roll (e.g., d8 = 5, d6 = 4)
            new_char.max_hp = hit_die_val + (level - 1) * avg_hit_die + con_mod * level
            new_char.current_hp = new_char.max_hp
        
        db.session.add(new_char)
        db.session.commit()
        
        # Sync spell slots AFTER committing so character exists in DB
        if char_class_model:
            new_char.sync_spell_slots()
            db.session.commit()
        return redirect(url_for('character_details', char_id=new_char.id))
    
    # Fetch available character classes and races from database
    classes = CharacterClassModel.query.order_by(CharacterClassModel.name).all()
    races = RaceModel.query.order_by(RaceModel.name).all()
    return render_template('add_character.html', classes=classes, races=races)

@app.route('/admin')
@login_required
def admin_index():
    """Admin dashboard."""
    _require_admin()
    stats = {
        'total_characters': Character.query.count(),
        'total_classes': CharacterClassModel.query.count(),
        'total_subclasses': SubclassModel.query.count(),
        'total_races': RaceModel.query.count(),
        'total_users': User.query.count(),
    }
    return render_template('admin_index.html', stats=stats)


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    """Manage users and their roles."""
    _require_admin()
    
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id', type=int)
        
        user = User.query.get_or_404(user_id)
        
        if action == 'toggle_admin':
            user.is_admin = not user.is_admin
            db.session.commit()
            status = "admin" if user.is_admin else "regular user"
            flash(f"{user.username} is now a {status}.", "success")
        elif action == 'reset_password':
            temp_password = 'TempPass123!'
            user.set_password(temp_password)
            db.session.commit()
            flash(f"Password for {user.username} reset to: {temp_password}", "success")
        
        return redirect(url_for('admin_users'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/classes', methods=['GET', 'POST'])
@login_required
def admin_classes():
    """Manage character classes and their proficiencies."""
    _require_admin()
    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        
        if not class_id:
            flash('Class ID is required.', 'error')
            return redirect(url_for('admin_classes'))
        
        cls = CharacterClassModel.query.get_or_404(class_id)
        
        # Update proficiencies (parse comma-separated values)
        def parse_list(form_key):
            raw = request.form.get(form_key, '').strip()
            return [item.strip() for item in raw.split(',') if item.strip()] if raw else []
        
        cls.skill_proficiencies = parse_list('skill_proficiencies')
        cls.armor_proficiencies = parse_list('armor_proficiencies')
        cls.weapon_proficiencies = parse_list('weapon_proficiencies')
        cls.tool_proficiencies = parse_list('tool_proficiencies')
        cls.saving_throw_proficiencies = parse_list('saving_throw_proficiencies')
        
        # Update skill choice count
        skill_choice = request.form.get('skill_choice_count', type=int)
        if skill_choice and skill_choice > 0:
            cls.skill_choice_count = skill_choice
        else:
            cls.skill_choice_count = 0
        
        # Update other fields
        hit_die = request.form.get('hit_die', type=int)
        if hit_die and hit_die > 0:
            cls.hit_die = hit_die
        
        subclass_unlock = request.form.get('subclass_unlock_level', type=int)
        if subclass_unlock and subclass_unlock > 0:
            cls.subclass_unlock_level = subclass_unlock
        
        spellcasting = request.form.get('spellcasting_ability', '').strip().upper() or None
        if spellcasting and spellcasting in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            cls.spellcasting_ability = spellcasting
        elif not request.form.get('spellcasting_ability'):
            cls.spellcasting_ability = None
        
        prepares = request.form.get('prepares_spells') == 'on'
        cls.prepares_spells = prepares
        
        description = request.form.get('description', '').strip()
        if description:
            cls.description = description
        
        db.session.commit()
        flash(f'Class "{cls.name}" updated successfully.', 'success')
        return redirect(url_for('admin_classes'))
    
    # GET: Show the form
    classes = CharacterClassModel.query.order_by(CharacterClassModel.name).all()
    return render_template('admin_classes.html', classes=classes)

@app.route('/admin/subclasses', methods=['GET', 'POST'])
@login_required
def admin_subclasses():
    _require_admin()
    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not class_id or not name:
            flash('Class and name are required.', 'error')
            return redirect(url_for('admin_subclasses'))
        
        cls = CharacterClassModel.query.get_or_404(class_id)
        
        # Check if subclass already exists
        existing = (SubclassModel.query
                   .filter(SubclassModel.class_id == class_id)
                   .filter(func.lower(SubclassModel.name) == name.lower())
                   .first())
        
        if existing:
            flash(f'Subclass "{name}" already exists for {cls.name}.', 'warning')
        else:
            new_sub = SubclassModel(
                name=name,
                description=description if description else None,
                character_class=cls
            )
            db.session.add(new_sub)
            db.session.commit()
            flash(f'Subclass "{name}" added to {cls.name}.', 'success')
        
        return redirect(url_for('admin_subclasses'))
    
    # GET: Show the form
    classes = CharacterClassModel.query.order_by(CharacterClassModel.name).all()
    subclasses = (SubclassModel.query
                  .join(CharacterClassModel)
                  .order_by(CharacterClassModel.name, SubclassModel.name)
                  .all())
    
    return render_template('admin_subclasses.html', classes=classes, subclasses=subclasses)

@app.route('/subclass/<int:subclass_id>')
def subclass_details(subclass_id: int):
    """Display subclass details with rendered description."""
    subclass = SubclassModel.query.get_or_404(subclass_id)
    return render_template('subclass_details.html', subclass=subclass)

@app.route('/admin/subclasses/<int:subclass_id>/delete', methods=['POST'])
@login_required
def delete_subclass(subclass_id: int):
    _require_admin()
    subclass = SubclassModel.query.get_or_404(subclass_id)
    class_name = subclass.character_class.name
    db.session.delete(subclass)
    db.session.commit()
    flash(f'Subclass deleted from {class_name}.', 'success')
    return redirect(url_for('admin_subclasses'))

@app.route('/characters/<int:char_id>/delete', methods=['POST'])
def delete_character(char_id: int):
    char = Character.query.get_or_404(char_id)
    db.session.delete(char)
    db.session.commit()
    flash('Character deleted.', 'success')
    return redirect(url_for('characters'))



@app.route('/characters')
@login_required
def characters():
    name = request.args.get('name')
    if not name or name == '*':
        # Show only characters owned by the current user (or all if admin)
        if current_user.is_admin:
            chars = Character.query.all()
        else:
            chars = Character.query.filter_by(user_id=current_user.id).all()
        return render_template('list_characters.html', characters=chars)
    else:
        # If a name is provided, try to find the character
        char = Character.query.filter_by(name=name).first()
        if char:
            # Check if user owns this character or is admin
            if char.user_id == current_user.id or current_user.is_admin:
                return render_template('character_details.html', character=char)
            else:
                abort(403)
        else:
            return render_template('character_details.html', character=None)

@app.route('/characters/<int:char_id>', methods=['GET', 'POST'])
@login_required
def character_details(char_id):
    char = Character.query.get_or_404(char_id)

    # Handle POST actions
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'reset_spells':
            # Reset all spell slots to their maximum (long rest)
            for slot in char.spell_slots:
                slot.remaining_slots = slot.total_slots
            db.session.commit()
            flash('Spell slots reset on long rest!', 'success')
            return redirect(url_for('character_details', char_id=char_id))

    cls = char.get_character_class_model()
    known_spells_count = len(getattr(char, "spells", []) or [])
    max_prepared = 0
    prepared_spells = char.prepared_spells
    
    if cls and cls.spellcasting_ability:
        if cls.prepares_spells:
            # Classes that prepare spells (Cleric, Druid, Paladin, Wizard)
            ability = (cls.spellcasting_ability or "").lower()
            sc_map = {"int": char.int_sc, "wis": char.wis_sc, "cha": char.cha_sc}
            max_prepared = max(1, char.level + ability_mod(sc_map.get(ability, 10)))
        else:
            # Classes that don't prepare spells (Bard, Sorcerer, Ranger, Warlock, Rogue, etc.)
            # All known spells are considered "prepared"
            prepared_spells = char.spells

    # Features up to level (works if relationship is lazy='dynamic')
    if cls:
        try:
            feats = (cls.features
                     .filter(CharacterClassFeature.level <= char.level)
                     .order_by(CharacterClassFeature.level.asc(),
                               CharacterClassFeature.name.asc())
                     .all())
        except AttributeError:
            # fallback if features is an eager list
            feats = sorted(
                [f for f in (cls.features or []) if f.level <= char.level],
                key=lambda f: (f.level, f.name.lower())
            )
    else:
        feats = []

    return render_template('character_details.html',
                           character=char,
                           known_spells_count=known_spells_count,
                           max_prepared=max_prepared,
                           prepared_spells=prepared_spells,
                           feats=feats)


@app.route('/characters/<int:char_id>/reset_spell_slots', methods=['POST'])
def reset_spell_slots(char_id):
    char = Character.query.get_or_404(char_id)
    
    # Reset all spell slots for this character
    for slot in char.spell_slots:
        slot.reset_slots()
    
    db.session.commit()
    flash(f"{char.name}'s spell slots have been reset (long rest).", 'success')
    return redirect(url_for('character_details', char_id=char.id))


@app.route('/api/classes/<int:class_id>/subclasses')
def api_class_subclasses(class_id: int):
    """Get all subclasses for a given class."""
    cls = CharacterClassModel.query.get_or_404(class_id)
    subclasses = SubclassModel.query.filter_by(class_id=class_id).order_by(SubclassModel.name).all()
    return jsonify({
        'class_id': class_id,
        'class_name': cls.name,
        'unlock_level': cls.subclass_unlock_level,
        'subclasses': [{'id': s.id, 'name': s.name} for s in subclasses]
    })

@app.route('/api/characters')
@login_required
def api_characters():
    name = request.args.get('q', '')
    # Filter by ownership unless user is admin
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
            "char_class": char.char_class.name if char.char_class else None,  # serialize related class
            "max_hp": char.max_hp,
            "current_hp": char.current_hp,
        })

    return jsonify(result)


@app.route('/api/characters/<int:char_id>/spell-slots/<int:slot_id>/toggle', methods=['POST'])
@login_required
def toggle_spell_slot(char_id, slot_id):
    """Toggle a spell slot as used/available."""
    char = Character.query.get_or_404(char_id)
    
    # Verify ownership (unless admin)
    if not current_user.is_admin and char.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    slot = CharacterSpellSlot.query.filter_by(id=slot_id, character_id=char_id).first_or_404()
    
    try:
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


@app.route('/features/<int:feature_id>')
def feature_details(feature_id: int):
    feat = CharacterClassFeature.query.get_or_404(feature_id)
    ctx = {
        "id": feat.id,
        "name": feat.name,
        "level": feat.level,
        "description": feat.description or "",
        "uses": feat.uses or "",
        "scaling": feat.scaling or {},
        "class_name": feat.character_class.name if feat.character_class else "",
    }
    return render_template('feature_details.html', feature=ctx)

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/api/spells')
def get_spells():
    query = request.args.get('q', '').strip()
    if not query:
        spells = Spell.query.limit(20).all()
    else:
        spells = Spell.query.filter(Spell.name.ilike(f'%{query}%')).limit(20).all()
    return jsonify([
        {"id": s.id, "name": s.name, "level": s.level, "school": s.school, "casting_time": s.casting_time}
        for s in spells
    ])

@app.route('/api/search')
def global_search():
    """Global search across spells, classes, subclasses, races, feats, and features."""
    query = request.args.get('q', '').strip()
    filters = request.args.getlist('filter')  # e.g., ['spells', 'classes', 'feats']
    
    if not query:
        return jsonify({"spells": [], "classes": [], "subclasses": [], "races": [], "feats": [], "features": []})
    
    results = {}
    
    # Search Spells
    if not filters or 'spells' in filters:
        spells = Spell.query.filter(Spell.name.ilike(f'%{query}%')).limit(10).all()
        results['spells'] = [
            {"id": s.id, "name": s.name, "type": "spell", "detail": f"Level {s.level} {s.school}"}
            for s in spells
        ]
    
    # Search Classes
    if not filters or 'classes' in filters:
        classes = CharacterClassModel.query.filter(CharacterClassModel.name.ilike(f'%{query}%')).limit(10).all()
        results['classes'] = [
            {"id": c.id, "name": c.name, "type": "class", "detail": f"Hit Die: d{c.hit_die}"}
            for c in classes
        ]
    
    # Search Subclasses
    if not filters or 'subclasses' in filters:
        subclasses = SubclassModel.query.filter(SubclassModel.name.ilike(f'%{query}%')).limit(10).all()
        results['subclasses'] = [
            {"id": s.id, "name": s.name, "type": "subclass", "detail": s.character_class.name if s.character_class else ""}
            for s in subclasses
        ]
    
    # Search Races
    if not filters or 'races' in filters:
        races = RaceModel.query.filter(RaceModel.name.ilike(f'%{query}%')).limit(10).all()
        results['races'] = [
            {"id": r.id, "name": r.name, "type": "race", "detail": f"Speed: {r.speed} ft."}
            for r in races
        ]
    
    # Search Feats
    if not filters or 'feats' in filters:
        feats = Feat.query.filter(Feat.name.ilike(f'%{query}%')).limit(10).all()
        results['feats'] = [
            {"id": f.id, "name": f.name, "type": "feat", "detail": "Prerequisites: " + ", ".join([p.get("ability_score", {}).get("name", "Unknown") for p in f.prerequisites]) if f.prerequisites else "No prerequisites"}
            for f in feats
        ]
    
    # Search Features (Class & Subclass)
    if not filters or 'features' in filters:
        class_features = CharacterClassFeature.query.filter(CharacterClassFeature.name.ilike(f'%{query}%')).limit(5).all()
        subclass_features = SubclassFeature.query.filter(SubclassFeature.name.ilike(f'%{query}%')).limit(5).all()
        
        features = []
        for cf in class_features:
            features.append({
                "id": cf.id, 
                "name": cf.name, 
                "type": "class_feature", 
                "detail": f"{cf.character_class.name} - Level {cf.level}" if cf.character_class else f"Level {cf.level}"
            })
        for sf in subclass_features:
            features.append({
                "id": sf.id, 
                "name": sf.name, 
                "type": "subclass_feature", 
                "detail": f"{sf.subclass.name} - Level {sf.level}" if sf.subclass else f"Level {sf.level}"
            })
        
        results['features'] = features
    
    return jsonify(results)

@app.route('/spells/<int:spell_id>')
def spell_details(spell_id):
    spell = Spell.query.get_or_404(spell_id)
    return render_template('spell_details.html', spell=spell)

@app.route('/feats/<int:feat_id>')
def feat_details(feat_id):
    feat = Feat.query.get_or_404(feat_id)
    return render_template('feat_details.html', feat=feat)

# Edit character (GET shows form, POST saves and handles known spells)
@app.route('/characters/<int:char_id>/edit', methods=['GET', 'POST'])
def edit_character(char_id: int):
    char = Character.query.get_or_404(char_id)

    cls = char.get_character_class_model()

    if request.method == 'POST':
        nm = request.form.get('name')
        if nm: char.name = nm.strip()

        rc = request.form.get('race')
        if rc: char.race = rc.strip()

        # Track original CON to detect if it changed
        old_con_sc = char.con_sc

        lvl = request.form.get('level', type=int)
        if lvl and lvl >= 1:
            old_level = char.level
            char.level = lvl
            # If level changed, sync spell slots FIRST before calculating available spells
            if old_level != lvl:
                char.sync_spell_slots()

        # Handle notes - only update if explicitly provided in form
        if 'notes' in request.form:
            char.notes = request.form.get('notes', '')

        for key in ['str_sc','dex_sc','con_sc','int_sc','wis_sc','cha_sc']:
            val = request.form.get(key, type=int)
            if val is not None:
                setattr(char, key, val)

        # Handle armor class
        ac = request.form.get('armor_class', type=int)
        if ac is not None and ac >= 1:
            char.armor_class = ac

        # Recalculate HP if level or CON changed
        con_changed = char.con_sc != old_con_sc
        if (lvl and lvl >= 1 and old_level != lvl) or con_changed:
            if char.char_class:
                con_mod = char.sc_to_mod(char.con_sc)
                hit_die_val = int(char.char_class.hit_die.replace('d', '')) if 'd' in str(char.char_class.hit_die) else char.char_class.hit_die
                # HP = hit_die + (level - 1) * (hit_die / 2 + 1) + con_mod * level
                avg_hit_die = (hit_die_val // 2) + 1  # Average roll (e.g., d8 = 5, d6 = 4)
                char.max_hp = hit_die_val + (char.level - 1) * avg_hit_die + con_mod * char.level
                char.current_hp = char.max_hp

        # known spells selection
        spell_ids = request.form.getlist('known_spells')
        if spell_ids is not None:
            chosen = Spell.query.filter(Spell.id.in_(list(map(int, spell_ids)))).all()
            char.spells = chosen

        # Recalc max prepared & enforce prepared ⊆ known and cap
        cls = char.get_character_class_model()
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
        return redirect(url_for('character_details', char_id=char.id))

    # After handling POST (if any), calculate available spells based on current character state
    # Get max spell level character has slots for
    max_spell_level = 0
    for slot in char.spell_slots:
        if slot.total_slots > 0:
            max_spell_level = max(max_spell_level, slot.level)
    
    # Get class spells, filtered by max spell level character can use
    if cls:
        available_spells = [s for s in cls.spells if s.level <= max_spell_level]
    else:
        available_spells = Spell.query.filter(Spell.level <= max_spell_level).order_by(Spell.level.asc(), Spell.name.asc()).all()

    return render_template('edit_character.html',
                           character=char,
                           available_spells=available_spells)

@app.route('/characters/<int:char_id>/level_up', methods=['GET', 'POST'])
def level_up_character(char_id):
    character = Character.query.get_or_404(char_id)

    # --- GET: show level up page ---
    if request.method == 'GET':
        # Pre-calculate info to display
        character.max_hp_before = character.max_hp
        character.max_hp_after = character.calculate_max_hp()

        character.spell_slots_before = character.spell_slots.copy() if character.spell_slots else {i: 0 for i in range(1, 6)}
        character.spell_slots_after = character.get_new_spell_slots() if hasattr(character, 'get_new_spell_slots') else character.spell_slots_before

        new_features = character.get_new_features_for_level() if hasattr(character, 'get_new_features_for_level') else []
        asi_options = character.get_asi_options() if hasattr(character, 'get_asi_options') else []
        
        # Get available feats if character gets ASI at this level
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
                # Character gets ASI/Feat at this level
                available_feats = Feat.query.all()

        return render_template(
            'level_up.html',
            character=character,
            new_features=new_features,
            asi_options=asi_options,
            available_feats=available_feats
        )

    # --- POST: apply level up ---
    if request.method == 'POST':
        # Apply ASI choice if any
        asi_choice = request.form.get('asi_choice')
        if asi_choice:
            character.apply_asi_choice(int(asi_choice))  # implement this in your Character model

        # Apply feature choices if any
        new_features = character.get_new_features_for_level() if hasattr(character, 'get_new_features_for_level') else []
        for feature in new_features:
            choice = request.form.get(f'feature_{feature.id}')
            if choice:
                character.apply_feature_choice(feature, int(choice))  # implement this in your Character model

        # Apply feat choice if any
        feat_choice = request.form.get('feat_choice')
        if feat_choice:
            feat = Feat.query.get(int(feat_choice))
            if feat and feat not in character.feats:
                character.feats.append(feat)

        # Apply new spells if any
        new_spell_ids = request.form.getlist('new_spells')
        if new_spell_ids:
            character.learn_new_spells([int(sid) for sid in new_spell_ids])  # implement in Character model

        # Finalize level up (updates level, HP, spell slots, etc.)
        character.level_up()

        db.session.commit()
        flash(f"{character.name} is now level {character.level}!", "success")
        return redirect(url_for('character_details', char_id=character.id))


@app.route("/characters/<int:char_id>/prepare_spells", methods=["POST"])
def prepare_spells(char_id: int):
    char = Character.query.get_or_404(char_id)

    cls = char.get_character_class_model()
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
    return redirect(url_for("character_details", char_id=char.id))


@app.route("/characters/<int:char_id>/toggle_favorite", methods=["POST"])
@login_required
def toggle_favorite(char_id: int):
    char = Character.query.get_or_404(char_id)
    
    # Check ownership
    if char.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    char.is_favorite = not char.is_favorite
    db.session.commit()
    
    return jsonify({'favorite': char.is_favorite})


@app.route("/race/<race_name>")
def show_race(race_name):
    race = RaceModel.query.filter_by(name=race_name).first_or_404()
    features = RaceFeature.query.filter_by(race_id=race.id).all()
    return render_template("race_details.html", race=race, features=features)

@app.route("/class/<class_name>")
def show_character_class(class_name):
    char_class = CharacterClassModel.query.filter_by(name=class_name).first_or_404()
    features = char_class.features_up_to(20)  # show all up to level 20
    return render_template("characterclass_details.html", character_class=char_class, features=features)


if __name__ == '__main__':
    # You can also run with `flask run` if you prefer
     socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=True)


