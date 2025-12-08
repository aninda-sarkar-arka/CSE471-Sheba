
from flask import Blueprint, request, jsonify, current_app, session
from .models import User, Item
from . import db


api_bp = Blueprint('api', __name__)


def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)


def login_required(fn):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'msg': 'authentication required'}), 401
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


@api_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({'msg': 'pong'})


@api_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'msg': 'username and password required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'username taken'}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': 'user created', 'user': user.to_dict()}), 201


@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'msg': 'username and password required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'msg': 'invalid credentials'}), 401
    # set session
    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'msg': 'logged in', 'user': user.to_dict()})


@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'msg': 'logged out'})


@api_bp.route('/auth/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        return jsonify({'user': None})
    return jsonify({'user': user.to_dict()})


@api_bp.route('/protected', methods=['GET'])
@login_required
def protected():
    user = get_current_user()
    return jsonify({'logged_in_as': user.username if user else None})


@api_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user = get_current_user()
    return jsonify(user.to_dict())


@api_bp.route('/profile', methods=['PUT', 'PATCH'])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}
    # Basic user fields
    for field in ('location', 'skills', 'service_area', 'profile_photo', 'name'):
        if field in data:
            setattr(user, field, data.get(field))
    if isinstance(data.get('skills'), list):
        user.skills = ','.join(data.get('skills'))

    # Partner-specific updates (if provided)
    # nid, partner_category, partner_locations (list allowed), fee_min, fee_max
    if 'nid' in data:
        user.nid = data.get('nid')
    if 'partner_category' in data:
        user.partner_category = data.get('partner_category')

    # Validate partner_locations if provided
    if 'partner_locations' in data:
        locs = data.get('partner_locations')
        if isinstance(locs, list):
            # server-side enforce limit 3
            if len(locs) > 3:
                return jsonify({'msg': 'maximum 3 partner locations allowed'}), 400
            user.partner_locations = ','.join(locs)
        elif isinstance(locs, str):
            # accept comma-separated string but enforce count
            arr = [p.strip() for p in locs.split(',') if p.strip()]
            if len(arr) > 3:
                return jsonify({'msg': 'maximum 3 partner locations allowed'}), 400
            user.partner_locations = ','.join(arr)
        else:
            user.partner_locations = None

    # Fees validation
    if 'fee_min' in data:
        try:
            fee_min = int(data.get('fee_min')) if data.get('fee_min') not in (None, '') else None
        except (ValueError, TypeError):
            return jsonify({'msg': 'fee_min must be a number'}), 400
        if fee_min is not None and (fee_min < 200 or fee_min > 5000):
            return jsonify({'msg': 'fee_min must be between 200 and 5000'}), 400
        user.fee_min = fee_min
    if 'fee_max' in data:
        try:
            fee_max = int(data.get('fee_max')) if data.get('fee_max') not in (None, '') else None
        except (ValueError, TypeError):
            return jsonify({'msg': 'fee_max must be a number'}), 400
        if fee_max is not None and (fee_max < 200 or fee_max > 5000):
            return jsonify({'msg': 'fee_max must be between 200 and 5000'}), 400
        user.fee_max = fee_max

    # If both fees present, ensure min <= max
    if user.fee_min is not None and user.fee_max is not None:
        if user.fee_min > user.fee_max:
            return jsonify({'msg': 'fee_min cannot be greater than fee_max'}), 400

    # If partner fields filled, mark role as 'partner'
    if user.partner_category or user.nid or (user.partner_locations and user.partner_locations.strip()):
        user.role = 'partner'

    db.session.commit()
    return jsonify(user.to_dict())


@api_bp.route('/profile/<int:user_id>', methods=['GET'])
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())



@api_bp.route('/items', methods=['GET'])
def list_items():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])


@api_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict())


@api_bp.route('/items', methods=['POST'])
@login_required
def create_item():
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description')
    if not title:
        return jsonify({'msg': 'title is required'}), 400
    item = Item(title=title, description=description)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@api_bp.route('/items/<int:item_id>', methods=['PUT', 'PATCH'])
@login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description')
    if title is not None:
        item.title = title
    if description is not None:
        item.description = description
    db.session.commit()
    return jsonify(item.to_dict())


@api_bp.route('/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'msg': 'deleted'})
