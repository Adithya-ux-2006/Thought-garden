import sys

from app import create_app
from app.cli import schema_is_current
from config import Config

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        if not schema_is_current():
            sys.exit('Database schema is not up to date. Run: flask db upgrade')
    app.run(debug=Config.FLASK_DEBUG, port=Config.PORT)
