import os
import runpy

from app import create_app
from app.models import User
from app.services.similarity_service import ensure_all_relationships

app = create_app()

if __name__ == '__main__':
    auto_seed = os.environ.get('AUTO_SEED', '1').lower() not in {'0', 'false', 'no'}
    with app.app_context():
        database_is_empty = User.query.first() is None
    if auto_seed and database_is_empty:
        runpy.run_path(os.path.join(os.path.dirname(__file__), 'seed.py'), run_name='__main__')
    with app.app_context():
        note_count, connection_count = ensure_all_relationships()
        print(
            f'Automatic connections ready: {connection_count} relationships '
            f'across {note_count} notes.'
        )
    debug_mode = os.environ.get('FLASK_DEBUG', '1').lower() not in {'0', 'false', 'no'}
    app.run(debug=debug_mode, port=int(os.environ.get('PORT', 5000)))
