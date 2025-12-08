from app import create_app, db
from flask.cli import FlaskGroup
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)
cli = FlaskGroup(create_app=lambda: app)

if __name__ == '__main__':
    cli()
