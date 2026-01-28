from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app.models import db, Character, Skill, Spell, CharacterClassModel, RaceModel, ClassSpellSlots, User, Feat
from app.models.character_struct import CharacterClassFeature, RaceFeature, SubclassFeature, SubclassModel
from app.models.spell_slots import CharacterSpellSlot
from app.grid import grid_bp
from app.routes.assets import assets_bp
from app.routes.characters import characters_bp
from app.extensions import socketio
from sqlalchemy import func
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "../instance")
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, "characters.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

socketio.init_app(app)
app.register_blueprint(grid_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(characters_bp)

# Jinja Filters
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

# Helpers
def ability_mod(score: int) -> int:
    try:
        return (int(score) - 10) // 2
    except Exception:
        return 0

def _require_admin():
    """Helper to check admin access."""
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)

# Routes
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

@app.route('/search')
def search_page():
    return render_template('search.html')

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


