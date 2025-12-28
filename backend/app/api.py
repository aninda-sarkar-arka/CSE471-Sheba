
from flask import Blueprint, request, jsonify, current_app, session
from flask_socketio import emit, join_room, leave_room
from .models import User, Item, ServiceRequest, Notification, Complaint, Warning, ChatMessage
from . import db, socketio, mail


api_bp = Blueprint('api', __name__)


# SocketIO event handlers for real-time notifications
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    user_id = session.get('user_id')
    if user_id:
        room = f'user_{user_id}'
        join_room(room)
        print(f'[SOCKETIO] User {user_id} connected and joined room {room}')
        emit('connected', {'status': 'connected', 'user_id': user_id})
    else:
        print('[SOCKETIO] Anonymous user connected (no session)')
        emit('error', {'msg': 'authentication required'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = session.get('user_id')
    if user_id:
        room = f'user_{user_id}'
        leave_room(room)
        print(f'[SOCKETIO] User {user_id} disconnected from room {room}')


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
    name = data.get('name')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default to user if not specified

    if not username or not password:
        return jsonify({'msg': 'username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'username taken'}), 400

    new_user = User(username=username, role=role, name=name, email=email)
    new_user.set_password(password)
    
    db.session.add(new_user)
    # Auto-assign Provider ID if role is provider
    if role == 'provider':
        db.session.flush() # flush to get an ID
        new_user.provider_unique_id = f"PV-{new_user.id:03d}"

    db.session.commit()

    return jsonify({'msg': 'registered successfully', 'role': role}), 201




@api_bp.route('/user/past-providers', methods=['GET'])
@login_required
def get_past_providers():
    user = get_current_user()
    if user.role != 'user':
        return jsonify([])

    # Find requests made by this user that have a provider assigned
    requests = ServiceRequest.query.filter_by(user_id=user.id).filter(ServiceRequest.provider_id.isnot(None)).all()
    
    # Extract unique providers
    seen = set()
    providers = []
    for req in requests:
        if req.provider_id not in seen:
            p = User.query.get(req.provider_id)
            if p:
                providers.append({
                    'id': p.id,
                    'name': p.name or p.username,
                    'provider_unique_id': p.provider_unique_id
                })
                seen.add(req.provider_id)
    
    return jsonify(providers)





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


@api_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """
    Simulate subscription purchase.
    In a real app, this would verify payment from a gateway.
    """
    user = get_current_user()
    from datetime import datetime, timedelta
    
    # Simulate payment success
    user.is_premium = True
    # 30 days subscription
    user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
    
    db.session.commit()
    
    # Notify user
    notif_msg = f'Congratulations! You are now a Premium Member. Enjoy exclusive benefits!'
    notification = Notification(recipient_id=user.id, message=notif_msg)
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'msg': 'Subscription successful',
        'user': user.to_dict()
    })


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

    # If partner fields filled, mark role as 'provider'
    if user.partner_category or user.nid or (user.partner_locations and user.partner_locations.strip()):
        user.role = 'provider'

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

# -------------------------------------------------------------------------
# Service Request Endpoints
# -------------------------------------------------------------------------

@api_bp.route('/service_requests', methods=['POST'])
@login_required
def create_service_request():
    """
    Create a new service request and notify all matching providers.
    Expected JSON: { "category": "<category>", "description": "<optional description>" }
    """
    user = get_current_user()
    data = request.get_json() or {}
    category = data.get('category')
    description = data.get('description', '')

    if not category:
        return jsonify({'msg': 'category is required'}), 400

    # Create service request without provider_id initially
    sr = ServiceRequest(
        user_id=user.id,
        provider_id=None,
        category=category,
        description=description,
        status='pending'
    )
    db.session.add(sr)
    db.session.commit()

    # Find all providers matching the category AND location
    # User location must match one of the provider's service locations
    # Provider locations are comma-separated string
    
    # Get all providers in category
    providers_in_category = User.query.filter_by(role='provider', partner_category=category).all()
    matching_providers = []
    
    user_location = user.location.strip().lower() if user.location else ''
    
    for prov in providers_in_category:
        if not user_location:
            # If user has no location, maybe show all? Or require location first? 
            # For now, let's include all to avoid empty list, or strict?
            # Strict: matching_providers = [] 
            # Loose: matching_providers.append(prov)
            # Going with Loose for now to allow testing without strict location
            matching_providers.append(prov)
            continue
            
        p_locs = [l.strip().lower() for l in (prov.partner_locations or '').split(',') if l.strip()]
        
        # Check partial match? or exact? 
        # Simple string inclusion for now
        if any(user_location in pl or pl in user_location for pl in p_locs):
            matching_providers.append(prov)
            
    # Fallback: if no location match, maybe notify all in category? 
    # User requirement: "by category and location"
    # If no match, maybe empty list is correct.
    if not matching_providers and not user_location:
         matching_providers = providers_in_category 

    # Notify all matching providers
    for provider in matching_providers:
        notif_msg = f'New service request #{sr.id} in category "{category}" from user {user.username}. Description: {description[:50]}...' if len(description) > 50 else f'New service request #{sr.id} in category "{category}" from user {user.username}. Description: {description}'
        
        # Create notification record
        notification = Notification(recipient_id=provider.id, message=notif_msg)
        db.session.add(notification)

        # Emit real-time notification via SocketIO
        socketio.emit('notification', {
            'id': notification.id,
            'message': notif_msg,
            'is_read': False,
            'created_at': notification.created_at.isoformat() if notification.created_at else None
        }, room=f'user_{provider.id}')

        # Send email if provider has a valid email
        if provider.email and provider.email.strip():
            try:
                from flask_mail import Message
                msg = Message(
                    subject=f'New Service Request - {category}',
                    recipients=[provider.email],
                    body=f'Hello {provider.username},\n\n{notif_msg}\n\nPlease check your dashboard to accept or reject this request.\n\nBest regards,\nServiceHub Team',
                    sender=current_app.config.get('MAIL_PROVIDER_SENDER')
                )
                mail.send(msg)
                print(f'[EMAIL] ✓ Email sent successfully to provider {provider.username} ({provider.email})')
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f'[EMAIL] ✗ Failed to send email to provider {provider.username} ({provider.email})')
                print(f'[EMAIL] Error: {str(e)}')
                print(f'[EMAIL] Details: {error_details}')
                print(f'[EMAIL] Config - Server: {current_app.config.get("MAIL_SERVER")}, Port: {current_app.config.get("MAIL_PORT")}, Username: {current_app.config.get("MAIL_USERNAME")}')
        else:
            print(f'[EMAIL] ⚠ Provider {provider.username} does not have an email address. Email notification will be sent when they add an email address.')

    db.session.commit()

    return jsonify(sr.to_dict()), 201

@api_bp.route('/service_requests/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_service_request(request_id):
    """
    Provider accepts a pending service request.
    Only providers matching the category can accept.
    """
    user = get_current_user()
    
    if user.role != 'provider':
        return jsonify({'msg': 'only providers can accept requests'}), 403

    sr = ServiceRequest.query.get_or_404(request_id)

    # Check if provider matches the category and request is still pending
    if sr.category != user.partner_category:
        return jsonify({'msg': 'category mismatch'}), 403
    
    if sr.status != 'pending':
        return jsonify({'msg': 'request already processed'}), 400

    # Assign provider and accept
    sr.provider_id = user.id
    sr.status = 'accepted'
    db.session.commit()

    # Notify the requesting user
    notif_msg = f'Your service request #{sr.id} ({sr.category}) has been accepted by provider {user.username}.'
    notification = Notification(recipient_id=sr.user_id, message=notif_msg)
    db.session.add(notification)
    db.session.commit()

    # Emit real-time notification
    socketio.emit('notification', {
        'id': notification.id,
        'message': notif_msg,
        'is_read': False,
        'created_at': notification.created_at.isoformat() if notification.created_at else None
    }, room=f'user_{sr.user_id}')

    # Email to user if email exists
    requester = User.query.get(sr.user_id)
    if requester and requester.email and requester.email.strip():
        try:
            from flask_mail import Message
            msg = Message(
                subject='Service Request Accepted',
                recipients=[requester.email],
                body=f'Hello {requester.username},\n\n{notif_msg}\n\nProvider: {user.username}\nCategory: {sr.category}\n\nBest regards,\nServiceHub Team',
                sender=current_app.config.get('MAIL_USER_SENDER')
            )
            mail.send(msg)
            print(f'[EMAIL] ✓ Email sent successfully to user {requester.username} ({requester.email})')
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f'[EMAIL] ✗ Failed to send email to user {requester.username} ({requester.email})')
            print(f'[EMAIL] Error: {str(e)}')
            print(f'[EMAIL] Details: {error_details}')
    else:
        print(f'[EMAIL] ⚠ User {requester.username if requester else "Unknown"} does not have an email address. Email notification will be sent when they add an email address.')

    return jsonify(sr.to_dict()), 200

@api_bp.route('/service_requests/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_service_request(request_id):
    """
    Provider rejects a pending service request.
    """
    user = get_current_user()
    
    if user.role != 'provider':
        return jsonify({'msg': 'only providers can reject requests'}), 403

    sr = ServiceRequest.query.get_or_404(request_id)

    # Check if provider matches the category
    if sr.category != user.partner_category:
        return jsonify({'msg': 'category mismatch'}), 403

    sr.status = 'rejected'
    db.session.commit()

    notif_msg = f'Your service request #{sr.id} ({sr.category}) has been rejected by provider {user.username}.'
    notification = Notification(recipient_id=sr.user_id, message=notif_msg)
    db.session.add(notification)
    db.session.commit()

    # Emit real-time notification
    socketio.emit('notification', {
        'id': notification.id,
        'message': notif_msg,
        'is_read': False,
        'created_at': notification.created_at.isoformat() if notification.created_at else None
    }, room=f'user_{sr.user_id}')

    requester = User.query.get(sr.user_id)
    if requester and requester.email and requester.email.strip():
        try:
            from flask_mail import Message
            msg = Message(
                subject='Service Request Rejected',
                recipients=[requester.email],
                body=f'Hello {requester.username},\n\n{notif_msg}\n\nYou can create a new request or wait for other providers to respond.\n\nBest regards,\nServiceHub Team',
                sender=current_app.config.get('MAIL_USER_SENDER')
            )
            mail.send(msg)
            print(f'[EMAIL] ✓ Email sent successfully to user {requester.username} ({requester.email})')
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f'[EMAIL] ✗ Failed to send email to user {requester.username} ({requester.email})')
            print(f'[EMAIL] Error: {str(e)}')
            print(f'[EMAIL] Details: {error_details}')
    else:
        print(f'[EMAIL] ⚠ User {requester.username if requester else "Unknown"} does not have an email address. Email notification will be sent when they add an email address.')

    return jsonify(sr.to_dict()), 200

@api_bp.route('/service_requests', methods=['GET'])
@login_required
def list_my_service_requests():
    """
    List service requests for the current user.
    - For regular users: requests they created.
    - For providers: requests matching their category (pending, accepted, or rejected by them).
    """
    user = get_current_user()
    if user.role == 'provider':
        # Show all requests matching provider's category
        requests = ServiceRequest.query.filter_by(category=user.partner_category).order_by(ServiceRequest.created_at.desc()).all()
    else:
        requests = ServiceRequest.query.filter_by(user_id=user.id).order_by(ServiceRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in requests]), 200

@api_bp.route('/service_requests/<int:request_id>/complete', methods=['POST'])
@login_required
def complete_service_request(request_id):
    """
    Provider marks the request as completed.
    """
    user = get_current_user()
    if user.role != 'provider':
        return jsonify({'msg': 'only providers can complete requests'}), 403
        
    sr = ServiceRequest.query.get_or_404(request_id)
    
    if sr.provider_id != user.id:
        return jsonify({'msg': 'not authorized'}), 403
        
    if sr.status != 'accepted':
        return jsonify({'msg': 'request must be accepted first'}), 400
        
    sr.status = 'completed'
    from datetime import datetime
    sr.completed_at = datetime.utcnow()
    db.session.commit()
    
    # Notify user
    notif_msg = f'Service request #{sr.id} has been marked as completed by provider. Please rate the service.'
    notification = Notification(recipient_id=sr.user_id, message=notif_msg)
    db.session.add(notification)
    db.session.commit()
    
    socketio.emit('notification', {
        'id': notification.id,
        'message': notif_msg,
        'is_read': False,
        'created_at': notification.created_at.isoformat()
    }, room=f'user_{sr.user_id}')
    
    return jsonify(sr.to_dict()), 200

@api_bp.route('/service_requests/<int:request_id>/rate', methods=['POST'])
@login_required
def rate_service_request(request_id):
    """
    User rates the completed service.
    Expected JSON: { "rating": 5, "review": "Great service!" }
    """
    user = get_current_user()
    sr = ServiceRequest.query.get_or_404(request_id)
    
    if sr.user_id != user.id:
        return jsonify({'msg': 'not authorized'}), 403
        
    if sr.status != 'completed':
        return jsonify({'msg': 'service must be completed to rate'}), 400
        
    data = request.get_json() or {}
    rating = data.get('rating')
    review = data.get('review')
    
    if rating is None or not (1 <= int(rating) <= 5):
        return jsonify({'msg': 'valid rating (1-5) required'}), 400
        
    sr.rating = int(rating)
    sr.review = review
    db.session.commit()
    
    # Update provider's average rating
    provider = User.query.get(sr.provider_id)
    if provider:
        # Recalculate average (simple way: query all rated requests)
        # Verify relationships carefully. provider.assigned_requests
        rated_reqs = [r for r in provider.assigned_requests if r.rating is not None]
        total_rating = sum(r.rating for r in rated_reqs)
        count = len(rated_reqs)
        
        provider.rating_count = count
        provider.rating_average = round(total_rating / count, 1) if count > 0 else 0.0
        db.session.commit()
        
    return jsonify(sr.to_dict()), 200

# -------------------------------------------------------------------------
# Service Request Chat Endpoints
# -------------------------------------------------------------------------

@api_bp.route('/service_requests/<int:request_id>/messages', methods=['GET'])
@login_required
def get_service_request_messages(request_id):
    """
    Get chat messages for a specific service request.
    Only accessible by the requester (user) and the assigned provider.
    """
    user = get_current_user()
    sr = ServiceRequest.query.get_or_404(request_id)
    
    # helper to check access
    if sr.user_id != user.id and sr.provider_id != user.id:
        return jsonify({'msg': 'access denied'}), 403
        
    messages = ChatMessage.query.filter_by(service_request_id=request_id).order_by(ChatMessage.created_at.asc()).all()
    return jsonify([m.to_dict() for m in messages]), 200

@api_bp.route('/service_requests/<int:request_id>/messages', methods=['POST'])
@login_required
def send_service_request_message(request_id):
    """
    Send a chat message for a service request.
    Only accessible if request is accepted (or maybe pending? usually accepted).
    """
    user = get_current_user()
    sr = ServiceRequest.query.get_or_404(request_id)
    
    if sr.user_id != user.id and sr.provider_id != user.id:
        return jsonify({'msg': 'access denied'}), 403
        
    # Optional: Only allow chat if status is accepted/in_progress
    if sr.status not in ['accepted', 'completed']: 
        # allowing 'completed' for post-service chat? or restrict? 
        # Usually chat is for active jobs. But let's allow it for now.
        if sr.status == 'pending':
            return jsonify({'msg': 'request must be accepted to start chat'}), 400
            
    data = request.get_json() or {}
    msg_text = data.get('message')
    if not msg_text:
        return jsonify({'msg': 'message required'}), 400
        
    chat_msg = ChatMessage(
        service_request_id=request_id,
        sender_id=user.id,
        message=msg_text
    )
    db.session.add(chat_msg)
    db.session.commit()
    
    # SocketIO Emit
    payload = chat_msg.to_dict()
    socketio.emit('new_message', payload, room=f'service_request_{request_id}')
    
    # Notify offline recipient? (Optional enhancement)
    
    return jsonify(payload), 201

@socketio.on('join_service_request')
def on_join_service_request(data):
    """
    Join a chat room for a specific service request.
    Expects data: { 'request_id': 123 }
    """
    uid = session.get('user_id')
    if not uid:
        return
    request_id = data.get('request_id')
    if request_id:
        # verify access? (optional but recommended)
        # For perf, skipping db check here, assuming frontend handles access logic
        room = f'service_request_{request_id}'
        join_room(room)
        print(f'[SOCKETIO] User {uid} joined room {room}')

@socketio.on('leave_service_request')
def on_leave_service_request(data):
    uid = session.get('user_id')
    if not uid:
        return
    request_id = data.get('request_id')
    if request_id:
        room = f'service_request_{request_id}'
        leave_room(room)
        print(f'[SOCKETIO] User {uid} left room {room}')

# -------------------------------------------------------------------------
# Notification Endpoints
# -------------------------------------------------------------------------

@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """
    Retrieve all notifications for the current user.
    """
    user = get_current_user()
    notifs = Notification.query.filter_by(recipient_id=user.id).order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifs]), 200

@api_bp.route('/notifications/<int:notif_id>/mark_read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """
    Mark a notification as read.
    """
    user = get_current_user()
    notif = Notification.query.filter_by(id=notif_id, recipient_id=user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'msg': 'notification marked as read'}), 200

# -------------------------------------------------------------------------
# Email Test Endpoint
# -------------------------------------------------------------------------

@api_bp.route('/test-email', methods=['POST'])
@login_required
def test_email():
    """
    Test email sending functionality.
    Sends a test email to the current user's email address.
    """
    user = get_current_user()
    
    if not user.email or not user.email.strip():
        return jsonify({'msg': 'User does not have an email address configured'}), 400
    
    try:
        from flask_mail import Message
        msg = Message(
            subject='Test Email from ServiceHub',
            recipients=[user.email],
            body=f'Hello {user.username},\n\nThis is a test email from ServiceHub.\n\nIf you received this, your email configuration is working correctly!\n\nBest regards,\nServiceHub Team',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        
        # Return email config info (without password)
        config_info = {
            'mail_server': current_app.config.get('MAIL_SERVER'),
            'mail_port': current_app.config.get('MAIL_PORT'),
            'mail_use_tls': current_app.config.get('MAIL_USE_TLS'),
            'mail_username': current_app.config.get('MAIL_USERNAME'),
            'mail_default_sender': current_app.config.get('MAIL_DEFAULT_SENDER'),
            'recipient': user.email
        }
        
        return jsonify({
            'msg': 'Test email sent successfully',
            'config': config_info
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        
        config_info = {
            'mail_server': current_app.config.get('MAIL_SERVER'),
            'mail_port': current_app.config.get('MAIL_PORT'),
            'mail_use_tls': current_app.config.get('MAIL_USE_TLS'),
            'mail_username': current_app.config.get('MAIL_USERNAME'),
            'mail_default_sender': current_app.config.get('MAIL_DEFAULT_SENDER'),
            'recipient': user.email,
            'error': str(e),
            'error_type': type(e).__name__
        }
        
        print(f'[EMAIL TEST] ✗ Failed to send test email')
        print(f'[EMAIL TEST] Error: {str(e)}')
        print(f'[EMAIL TEST] Details: {error_details}')
        
        return jsonify({
            'msg': 'Failed to send test email',
            'error': str(e),
            'error_type': type(e).__name__,
            'config': config_info,
            'hint': 'Check your MAIL_USERNAME and MAIL_PASSWORD in config.py or environment variables. For Gmail, you need an App Password, not your regular password.'
        }), 500

# -------------------------------------------------------------------------
# Complaint Endpoints
# -------------------------------------------------------------------------

@api_bp.route('/complaints', methods=['POST'])
@login_required
def create_complaint():
    """
    Create a new complaint.
    Expected JSON: {
        "title": "<title>",
        "description": "<description>",
        "provider_id": <optional provider_id>,
        "service_request_id": <optional service_request_id>
    }
    """
    user = get_current_user()
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description')
    provider_id = data.get('provider_id')
    provider_unique_id = data.get('provider_unique_id')
    service_request_id = data.get('service_request_id')

    if not title or not description:
        return jsonify({'msg': 'title and description are required'}), 400

    # Validate provider_id / provider_unique_id if provided
    if provider_id:
        provider = User.query.get(provider_id)
        if not provider or provider.role != 'provider':
            return jsonify({'msg': 'invalid provider_id'}), 400
    elif provider_unique_id:
        provider = User.query.filter_by(provider_unique_id=provider_unique_id).first()
        if not provider or provider.role != 'provider':
            return jsonify({'msg': 'invalid provider_unique_id'}), 400
        provider_id = provider.id

    # Validate service_request_id if provided
    if service_request_id:
        sr = ServiceRequest.query.get(service_request_id)
        if not sr:
            return jsonify({'msg': 'invalid service_request_id'}), 400

    complaint = Complaint(
        user_id=user.id,
        provider_id=provider_id,
        service_request_id=service_request_id,
        title=title,
        description=description,
        status='pending'
    )
    db.session.add(complaint)
    db.session.commit()

    return jsonify(complaint.to_dict()), 201

@api_bp.route('/complaints', methods=['GET'])
@login_required
def list_complaints():
    """
    List complaints based on user role:
    - Admin: all complaints (can filter by status)
    - User: their own complaints
    - Provider: complaints against them
    """
    user = get_current_user()
    status_filter = request.args.get('status')  # optional filter: pending, reviewed, resolved

    if user.role == 'admin':
        query = Complaint.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        complaints = query.order_by(Complaint.created_at.desc()).all()
    elif user.role == 'provider':
        complaints = Complaint.query.filter_by(provider_id=user.id).order_by(Complaint.created_at.desc()).all()
    else:
        complaints = Complaint.query.filter_by(user_id=user.id).order_by(Complaint.created_at.desc()).all()

    return jsonify([c.to_dict() for c in complaints]), 200
  
@api_bp.route('/complaints/<int:complaint_id>/messages', methods=['GET'])
@login_required
def get_complaint_messages(complaint_id):
    """Get chat history for a complaint"""
    user = get_current_user()
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Access control
    if user.role != 'admin' and complaint.user_id != user.id:
        return jsonify({'msg': 'access denied'}), 403
        
    messages = ChatMessage.query.filter_by(complaint_id=complaint_id).order_by(ChatMessage.created_at.asc()).all()
    return jsonify([m.to_dict() for m in messages]), 200

@api_bp.route('/complaints/<int:complaint_id>/messages', methods=['POST'])
@login_required
def send_complaint_message(complaint_id):
    """Send a chat message"""
    user = get_current_user()
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if user.role != 'admin' and complaint.user_id != user.id:
        return jsonify({'msg': 'access denied'}), 403
        
    if complaint.status == 'reviewed':
        return jsonify({'msg': 'chat is closed'}), 400

    data = request.get_json() or {}
    text = data.get('message', '')
    if not text.strip():
        return jsonify({'msg': 'message required'}), 400
        
    msg = ChatMessage(complaint_id=complaint_id, sender_id=user.id, message=text)
    db.session.add(msg)
    
    # If first message by admin, likely changing status to progress if pending
    if user.role == 'admin' and complaint.status == 'pending':
        complaint.status = 'progress'
        
    db.session.commit()
    
    # Emit real-time message
    msg_data = msg.to_dict()
    socketio.emit('new_message', msg_data, room=f'complaint_{complaint_id}')
    
    # Notify offline participant
    recipient_id = complaint.user_id if user.role == 'admin' else None 
    # Logic for notifying admin is subtler (any admin), skipping for now as admin monitors dashboard
    
    if recipient_id:
        notif_msg = f'New message from {user.username} on complaint "#{complaint.title}"'
        notification = Notification(recipient_id=recipient_id, message=notif_msg)
        db.session.add(notification)
        db.session.commit()
        socketio.emit('notification', {
            'id': notification.id, 
            'message': notif_msg, 
            'is_read': False,
            'created_at': notification.created_at.isoformat()
        }, room=f'user_{recipient_id}')

    return jsonify(msg_data), 201

@api_bp.route('/complaints/<int:complaint_id>/status', methods=['PATCH'])
@login_required
def update_complaint_status(complaint_id):
    """Admin toggles status: progress <-> reviewed"""
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'msg': 'admin only'}), 403
        
    complaint = Complaint.query.get_or_404(complaint_id)
    data = request.get_json() or {}
    new_status = data.get('status')
    
    if new_status not in ['progress', 'reviewed', 'resolved']:
        return jsonify({'msg': 'invalid status'}), 400
        
    complaint.status = new_status
    db.session.commit()
    
    # Notify via socket room
    socketio.emit('status_change', {
        'complaint_id': complaint_id,
        'status': new_status
    }, room=f'complaint_{complaint_id}')
    
    # Also refresh dashboard lists
    socketio.emit('complaint_update', {'complaint_id': complaint_id}, room=f'complaint_{complaint_id}')
    
    return jsonify(complaint.to_dict()), 200

@api_bp.route('/complaints/<int:complaint_id>/reply', methods=['POST'])
@login_required
def reply_to_complaint(complaint_id):
    """
    Admin replies to a complaint and marks it as reviewed.
    Expected JSON: { "response": "<admin response text>" }
    """
    user = get_current_user()
    
    if user.role != 'admin':
        return jsonify({'msg': 'only admin can reply to complaints'}), 403

    complaint = Complaint.query.get_or_404(complaint_id)
    data = request.get_json() or {}
    response = data.get('response', '')

    if not response:
        return jsonify({'msg': 'response is required'}), 400

    complaint.admin_response = response
    complaint.status = 'reviewed'
    db.session.commit()

    # Notify the user who filed the complaint
    notif_msg = f'Admin has replied to your complaint: "{complaint.title}". Response: {response[:100]}...' if len(response) > 100 else f'Admin has replied to your complaint: "{complaint.title}". Response: {response}'
    notification = Notification(recipient_id=complaint.user_id, message=notif_msg)
    db.session.add(notification)
    db.session.commit()

    # Emit real-time notification
    socketio.emit('notification', {
        'id': notification.id,
        'message': notif_msg,
        'is_read': False,
        'created_at': notification.created_at.isoformat() if notification.created_at else None
    }, room=f'user_{complaint.user_id}')

    # Emit complaint update via socketio for real-time chat
    socketio.emit('complaint_update', {
        'complaint_id': complaint.id,
        'admin_response': response,
        'status': complaint.status
    }, room=f'complaint_{complaint.id}')

    return jsonify(complaint.to_dict()), 200

@api_bp.route('/complaints/<int:complaint_id>/warn_provider', methods=['POST'])
@login_required
def warn_provider(complaint_id):
    """
    Admin issues a warning to a provider mentioned in a complaint.
    Expected JSON: { "message": "<warning message>" }
    """
    user = get_current_user()
    
    if user.role != 'admin':
        return jsonify({'msg': 'only admin can warn providers'}), 403

    complaint = Complaint.query.get_or_404(complaint_id)
    
    if not complaint.provider_id:
        return jsonify({'msg': 'complaint does not mention a provider'}), 400

    data = request.get_json() or {}
    warning_message = data.get('message', '')

    if not warning_message:
        return jsonify({'msg': 'warning message is required'}), 400

    # Create warning record
    warning = Warning(
        complaint_id=complaint.id,
        provider_id=complaint.provider_id,
        admin_id=user.id,
        message=warning_message
    )
    db.session.add(warning)
    db.session.commit()

    # Notify the provider
    notif_msg = f'⚠️ WARNING: You have received a warning from admin regarding complaint: "{complaint.title}". {warning_message}'
    notification = Notification(recipient_id=complaint.provider_id, message=notif_msg)
    db.session.add(notification)
    db.session.commit()

    # Emit real-time notification (in red/highlighted)
    socketio.emit('notification', {
        'id': notification.id,
        'message': notif_msg,
        'is_read': False,
        'is_warning': True,  # Flag for frontend to style differently
        'created_at': notification.created_at.isoformat() if notification.created_at else None
    }, room=f'user_{complaint.provider_id}')

    return jsonify(warning.to_dict()), 201

# -------------------------------------------------------------------------
# Warning Endpoints (for providers)
# -------------------------------------------------------------------------

@api_bp.route('/warnings', methods=['GET'])
@login_required
def list_warnings():
    """
    List warnings for the current provider.
    """
    user = get_current_user()
    
    if user.role != 'provider':
        return jsonify({'msg': 'only providers can view warnings'}), 403

    warnings = Warning.query.filter_by(provider_id=user.id).order_by(Warning.created_at.desc()).all()
    return jsonify([w.to_dict() for w in warnings]), 200

# -------------------------------------------------------------------------
# SocketIO Events for Complaints (Real-time chat)
# -------------------------------------------------------------------------

@socketio.on('join_complaint')
def handle_join_complaint(data):
    """Join a complaint room for real-time chat"""
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'msg': 'authentication required'})
        return
    
    complaint_id = data.get('complaint_id')
    if not complaint_id:
        emit('error', {'msg': 'complaint_id required'})
        return
    
    # Verify user has access to this complaint
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        emit('error', {'msg': 'complaint not found'})
        return
    
    user = User.query.get(user_id)
    if user.role != 'admin' and complaint.user_id != user_id and complaint.provider_id != user_id:
        emit('error', {'msg': 'access denied'})
        return
    
    room = f'complaint_{complaint_id}'
    join_room(room)
    emit('joined_complaint', {'complaint_id': complaint_id, 'room': room})

@socketio.on('leave_complaint')
def handle_leave_complaint(data):
    """Leave a complaint room"""
    complaint_id = data.get('complaint_id')
    if complaint_id:
        room = f'complaint_{complaint_id}'
        leave_room(room)
        emit('left_complaint', {'complaint_id': complaint_id})
