from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Profile fields
    role = db.Column(db.String(20), default='user')  # 'user' or 'provider'
    name = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    skills = db.Column(db.Text, nullable=True)  # comma-separated list
    service_area = db.Column(db.String(200), nullable=True)
    profile_photo = db.Column(db.String(500), nullable=True)  # URL to photo
    # Partner-specific fields
    nid = db.Column(db.String(50), nullable=True)
    partner_category = db.Column(db.String(100), nullable=True)
    partner_locations = db.Column(db.Text, nullable=True)  # comma-separated, up to 3
    fee_min = db.Column(db.Integer, nullable=True)
    fee_max = db.Column(db.Integer, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        skills = self.skills.split(',') if self.skills else []
        partner_locations = self.partner_locations.split(',') if self.partner_locations else []
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'role': self.role,
            'location': self.location,
            'skills': skills,
            'service_area': self.service_area,
            'profile_photo': self.profile_photo,
            'nid': self.nid,
            'partner_category': self.partner_category,
            'partner_locations': partner_locations,
            'fee_min': self.fee_min,
            'fee_max': self.fee_max,
        }

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    provider = db.relationship('User', backref=db.backref('services', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'provider_username': self.provider.username if self.provider else None,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'price': self.price,
            'created_at': self.created_at.isoformat()
        }
