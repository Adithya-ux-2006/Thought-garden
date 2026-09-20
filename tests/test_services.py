import numpy as np
import pytest
from app import create_app, db
from app.models import User, Note, Tag, Relationship, NoteEmbedding
from app.services.math_utils import cosine_similarity, extract_keywords, Pagination
from app.services.similarity_service import (
    lightweight_similarity,
    get_relationship_explanation,
)
from app.services.search_service import keyword_search


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'SEMANTIC_PIPELINE_BACKGROUND': False,
    })
    with app.app_context():
        db.create_all()
        user = User(name='Test', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestCosineSimilarity:
    def test_identical_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 1.0])
        assert cosine_similarity(a, b) == 0.0

    def test_symmetry(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a))


class TestExtractKeywords:
    def test_basic_extraction(self):
        keywords = extract_keywords('machine learning and deep learning networks')
        assert 'machine' in keywords
        assert 'learning' in keywords
        assert 'deep' in keywords

    def test_stop_words_filtered(self):
        keywords = extract_keywords('the and or but is was are')
        assert len(keywords) == 0

    def test_max_keywords(self):
        text = 'alpha bravo charlie delta echo foxtrot golf hotel india'
        keywords = extract_keywords(text, max_keywords=3)
        assert len(keywords) <= 3

    def test_case_insensitive(self):
        k1 = extract_keywords('Machine Learning')
        k2 = extract_keywords('machine learning')
        assert k1 == k2

    def test_short_words_filtered(self):
        keywords = extract_keywords('AI is fun but ML is better')
        assert 'ai' not in [k.lower() for k in keywords]


class TestPagination:
    def test_basic_pagination(self):
        items = list(range(10))
        p = Pagination(items, page=1, per_page=10, total=25)
        assert p.pages == 3
        assert p.has_prev is False
        assert p.has_next is True

    def test_last_page(self):
        items = list(range(5))
        p = Pagination(items, page=3, per_page=10, total=25)
        assert p.has_prev is True
        assert p.has_next is False

    def test_iter_pages(self):
        p = Pagination([], page=3, per_page=10, total=50)
        pages = list(p.iter_pages())
        assert 3 in pages


class TestLightweightSimilarity:
    def test_identical_notes(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='Machine Learning', content='neural network deep learning classification')
            n2 = Note(user_id=user.id, title='Machine Learning', content='neural network deep learning classification')
            db.session.add_all([n1, n2])
            db.session.commit()
            score = lightweight_similarity(n1, n2)
            assert score >= 0.45

    def test_different_notes(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='Cats and Kittens', content='feline animal pet household')
            n2 = Note(user_id=user.id, title='Quantum Physics', content='particle wave function collapse')
            db.session.add_all([n1, n2])
            db.session.commit()
            score = lightweight_similarity(n1, n2)
            assert score < 0.3

    def test_same_category_boost(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='Alpha Test', content='unique words alpha testing', category='AI')
            n2 = Note(user_id=user.id, title='Beta Test', content='unique words beta testing', category='AI')
            n3 = Note(user_id=user.id, title='Gamma Test', content='unique words gamma testing', category='Math')
            db.session.add_all([n1, n2, n3])
            db.session.commit()
            same_cat = lightweight_similarity(n1, n2)
            diff_cat = lightweight_similarity(n1, n3)
            assert same_cat >= diff_cat

    def test_symmetry(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='Alpha', content='alpha content words')
            n2 = Note(user_id=user.id, title='Beta', content='beta content words')
            db.session.add_all([n1, n2])
            db.session.commit()
            assert lightweight_similarity(n1, n2) == pytest.approx(lightweight_similarity(n2, n1))

    def test_score_range(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='A', content='a a a')
            n2 = Note(user_id=user.id, title='B', content='b b b')
            db.session.add_all([n1, n2])
            db.session.commit()
            score = lightweight_similarity(n1, n2)
            assert 0.0 <= score <= 1.0


class TestGetRelationshipExplanation:
    def test_common_keywords(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='Python coding', content='python programming language code')
            n2 = Note(user_id=user.id, title='Python testing', content='python testing framework code')
            db.session.add_all([n1, n2])
            db.session.commit()
            explanation = get_relationship_explanation(n1, n2)
            assert 'python' in explanation.lower()

    def test_no_common_content(self, app):
        with app.app_context():
            user = User.query.first()
            n1 = Note(user_id=user.id, title='Alpha', content='unique words alpha here')
            n2 = Note(user_id=user.id, title='Zeta', content='distinct terms zeta here')
            db.session.add_all([n1, n2])
            db.session.commit()
            explanation = get_relationship_explanation(n1, n2)
            assert isinstance(explanation, str)
            assert len(explanation) > 0


class TestKeywordSearch:
    def test_keyword_search(self, app):
        with app.app_context():
            user = User.query.first()
            note = Note(user_id=user.id, title='Machine Learning', content='deep learning AI', category='AI')
            db.session.add(note)
            db.session.commit()
            results = keyword_search(user.id, 'machine')
            assert len(results.items) >= 1
            assert results.items[0].title == 'Machine Learning'

    def test_keyword_search_no_results(self, app):
        with app.app_context():
            user = User.query.first()
            results = keyword_search(user.id, 'zzzznonexistent')
            assert len(results.items) == 0

    def test_keyword_search_category_filter(self, app):
        with app.app_context():
            user = User.query.first()
            db.session.add(Note(user_id=user.id, title='ML Notes', content='machine learning', category='AI'))
            db.session.add(Note(user_id=user.id, title='ML Sec', content='machine learning', category='Cybersecurity'))
            db.session.commit()
            results = keyword_search(user.id, 'machine', category='AI')
            assert all(n.category == 'AI' for n in results.items)

    def test_keyword_search_empty_query(self, app):
        with app.app_context():
            user = User.query.first()
            db.session.add(Note(user_id=user.id, title='Test Note', content='test content'))
            db.session.commit()
            results = keyword_search(user.id, '')
            assert len(results.items) >= 1

    def test_keyword_search_pagination(self, app):
        with app.app_context():
            user = User.query.first()
            for i in range(25):
                db.session.add(Note(user_id=user.id, title=f'Note {i}', content=f'content {i}'))
            db.session.commit()
            page1 = keyword_search(user.id, 'note', page=1, per_page=10)
            page2 = keyword_search(user.id, 'note', page=2, per_page=10)
            assert len(page1.items) == 10
            assert page1.has_next is True
            assert page2.has_prev is True


class TestNoteEmbedding:
    def test_model_table_exists(self, app):
        with app.app_context():
            assert NoteEmbedding.__tablename__ == 'note_embeddings'

    def test_create_and_read(self, app):
        with app.app_context():
            user = User.query.first()
            note = Note(user_id=user.id, title='Embed Test', content='test content')
            db.session.add(note)
            db.session.commit()
            record = NoteEmbedding(note_id=note.id, embedding=b'test-blob')
            db.session.add(record)
            db.session.commit()
            fetched = NoteEmbedding.query.filter_by(note_id=note.id).first()
            assert fetched is not None
            assert fetched.embedding == b'test-blob'
