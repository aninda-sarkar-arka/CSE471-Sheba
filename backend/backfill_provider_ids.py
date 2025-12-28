from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    providers = User.query.filter_by(role='provider').all()
    count = 0
    for p in providers:
        if not p.provider_unique_id:
            # Format PV-001, PV-005, etc. using their database ID
            p.provider_unique_id = f"PV-{p.id:03d}"
            count += 1
            print(f"Assigned {p.provider_unique_id} to {p.username}")
    
    if count > 0:
        db.session.commit()
        print(f"Successfully backfilled {count} providers.")
    else:
        print("No providers needed backfilling.")
