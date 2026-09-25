import sys

import numpy as np

from app import create_app, db
from app.models import User, Note, NoteEmbedding
from app.services import embedding_service, indexer


def test_embedding_model_is_stubbed_for_tests():
    model = embedding_service.get_model()
    assert getattr(model, 'is_test_stub', False)
    assert 'sentence_transformers' not in sys.modules

    a = model.encode('neural networks learn', convert_to_numpy=True, normalize_embeddings=True)
    b = model.encode('neural networks learn', convert_to_numpy=True, normalize_embeddings=True)
    c = model.encode('cpu scheduling deadlocks', convert_to_numpy=True, normalize_embeddings=True)
    assert np.allclose(a, b)
    assert abs(float(np.linalg.norm(a)) - 1.0) < 1e-5
    assert float(np.dot(a, b)) > float(np.dot(a, c))


def test_indexer_process_pending_runs_synchronously_in_tests():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                      'SECRET_KEY': 'test-secret-key'})
    with app.app_context():
        db.create_all()
        user = User(name='U', email='u@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        note = Note(user_id=user.id, title='Inline', content='Indexed immediately.')
        db.session.add(note)
        db.session.commit()

        indexer.enqueue(note)
        indexer.process_pending(app)

        assert db.session.get(NoteEmbedding, note.id) is not None
        db.session.remove()
        db.drop_all()
