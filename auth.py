from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, request, jsonify, render_template, redirect, url_for

auth_bp = Blueprint('auth', __name__)

def init_auth(app, db):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(150), unique=True, nullable=False)
        password = db.Column(db.String(256), nullable=False)
        name = db.Column(db.String(100))
        facility = db.Column(db.String(100))
        role = db.Column(db.String(20), default='staff')
        credentials = db.Column(db.String(100), default='')
        title = db.Column(db.String(100), default='')
        license_number = db.Column(db.String(50), default='')
        created_at = db.Column(db.DateTime, default=db.func.now())
        is_active = db.Column(db.Boolean, default=True)

        def get_id(self):
            return str(self.id)

        @property
        def is_authenticated(self):
            return True

        @property
        def is_anonymous(self):
            return False

        @property
        def is_admin(self):
            return self.role == 'admin'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @auth_bp.route('/login')
    def login_page():
        if current_user.is_authenticated:
            return redirect('/app')
        return render_template('login.html')

    @auth_bp.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.json
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'All fields required'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),
            name=data['name'],
            facility=data.get('facility', ''),
            role='staff'
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify({'success': True, 'name': user.name})

    @auth_bp.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.json
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        login_user(user, remember=True)
        return jsonify({'success': True, 'name': user.name})

    @auth_bp.route('/api/auth/logout', methods=['POST'])
    @login_required
    def logout():
        logout_user()
        return jsonify({'success': True})

    @auth_bp.route('/api/auth/me', methods=['GET'])
    def me():
        if current_user.is_authenticated:
            return jsonify({
                'authenticated': True,
                'name': current_user.name,
                'email': current_user.email,
                'facility': current_user.facility,
                'role': current_user.role
            })
        return jsonify({'authenticated': False})

    return User