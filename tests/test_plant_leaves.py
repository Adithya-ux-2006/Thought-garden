"""Plant/leaf grouping: multi-part document imports become one plant whose
chunks are leaves, the garden collapses leaves onto the plant (no clutter),
and leaves get a jump pager on the note view."""

import io

import pytest

from app import create_app, db
from app.models import Note, User

LONG_TEXT = ('Paragraph about gardens and knowledge graphs. ' * 120).encode()


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    return client


def _user_id():
    return User.query.filter_by(email='test@example.com').one().id


def _import_doc(client, name='doc.txt'):
    return client.post('/notes/import', data={
        'file': (io.BytesIO(LONG_TEXT), name),
    }, content_type='multipart/form-data')


def _plant(filename='doc.txt'):
    return Note.query.filter_by(
        user_id=_user_id(), source_filename=filename, parent_id=None
    ).one()


def _leaves(plant):
    return sorted(plant.leaf_notes, key=lambda leaf: (leaf.part_index or 0, leaf.id))


# ---- import splits a long document into one plant + leaf notes ----

def test_multi_chunk_import_creates_one_plant_with_leaves(client):
    response = _import_doc(client)
    assert response.status_code == 302

    plant = _plant()
    leaves = _leaves(plant)
    assert len(leaves) >= 3

    assert all(leaf.parent_id == plant.id for leaf in leaves)
    assert all(leaf.source_type == 'txt' for leaf in leaves)
    assert plant.content.startswith(f'> Imported from **doc.txt**')
    assert 'leaf note' in plant.content

    indexes = [leaf.part_index for leaf in leaves]
    assert indexes == list(range(1, len(leaves) + 1))

    assert leaves[0].title.endswith('(Part 1)')
    assert plant.title not in {leaf.title for leaf in leaves}

    # The import redirects to the plant's own page (which lists its leaves).
    assert response.headers['Location'] == f'/notes/{plant.id}'


def test_single_chunk_import_stays_a_plain_note(client):
    response = client.post('/notes/import', data={
        'file': (io.BytesIO(b'Short note.'), 'short.txt'),
    }, content_type='multipart/form-data')

    notes = Note.query.filter_by(user_id=_user_id(), source_filename='short.txt').all()
    assert len(notes) == 1
    assert notes[0].parent_id is None
    assert notes[0].part_index is None
    assert notes[0].content == 'Short note.'
    assert response.headers['Location'] == f'/notes/{notes[0].id}'


def test_manual_notes_remain_standalone(client):
    client.post('/notes/create', data={'title': 'Solo', 'content': 'Just me.'})
    notes = Note.query.filter_by(user_id=_user_id()).all()
    assert len(notes) == 1
    assert notes[0].parent_id is None
    assert notes[0].leaf_notes == []


# ---- the garden collapses leaves onto plants ----

def test_garden_data_shows_only_plants_not_leaf_nodes(client):
    _import_doc(client, 'a.txt')
    _import_doc(client, 'b.txt')

    plant_ids = {n.id for n in Note.query.filter(Note.parent_id.is_(None)).all()}
    leaf_ids = {n.id for n in Note.query.filter(Note.parent_id.isnot(None)).all()}
    assert leaf_ids

    payload = client.get('/garden/data').get_json()
    node_ids = {node['id'] for node in payload['nodes']}

    assert set(node_ids) == plant_ids
    assert node_ids.isdisjoint(leaf_ids)

    for edge in payload['edges']:
        assert edge['from'] in node_ids, 'edge endpoint must be a plant/standalone node'
        assert edge['to'] in node_ids


def test_garden_list_groups_leaves_under_their_plant(client):
    _import_doc(client)
    plant = _plant()
    leaves = _leaves(plant)

    page = client.get('/garden/list').data.decode()
    assert 'leaf note' in page
    assert any(leaf.title in page for leaf in leaves)
    # Leaf titles appear next to their plant's row.
    assert plant.title in page


# ---- the note view: leaf pager and plant leaf list ----

def test_note_view_leaf_pager_jumps_between_leaves(client):
    _import_doc(client)
    plant = _plant()
    leaves = _leaves(plant)
    assert len(leaves) >= 3

    page = client.get(f'/notes/{leaves[1].id}').data.decode()
    # The pager has exactly two real links (prev + next) for a middle leaf.
    assert page.count('<a class="leaf-pager-link"') == 2
    assert f'/notes/{leaves[0].id}' in page
    assert f'/notes/{leaves[2].id}' in page

    first = client.get(f'/notes/{leaves[0].id}').data.decode()
    assert first.count('<a class="leaf-pager-link"') == 1  # Previous is disabled
    assert f'/notes/{leaves[1].id}' in first

    last = client.get(f'/notes/{leaves[-1].id}').data.decode()
    assert last.count('<a class="leaf-pager-link"') == 1  # Next is disabled
    assert f'/notes/{leaves[-2].id}' in last


def test_note_view_plant_lists_leaves(client):
    _import_doc(client)
    plant = _plant()
    leaves = _leaves(plant)

    page = client.get(f'/notes/{plant.id}').data.decode()
    assert 'leaf note' in page
    for leaf in leaves:
        assert f'/notes/{leaf.id}' in page

    # Opening a leaf links back to its plant.
    leaf_page = client.get(f'/notes/{leaves[0].id}').data.decode()
    assert f'/notes/{plant.id}' in leaf_page


# ---- lifecycle: deleting a plant removes its leaves ----

def test_deleting_plant_deletes_its_leaves(client):
    _import_doc(client)
    plant = _plant()
    leaves = _leaves(plant)
    assert leaves

    response = client.post(f'/notes/{plant.id}/delete')
    assert response.status_code == 302
    assert db.session.get(Note, plant.id) is None
    assert Note.query.filter(Note.parent_id == plant.id).count() == 0


def test_deleting_a_leaf_keeps_the_plant(client):
    _import_doc(client)
    plant = _plant()
    leaves = _leaves(plant)

    response = client.post(f'/notes/{leaves[0].id}/delete')
    assert response.status_code == 302
    assert db.session.get(Note, plant.id) is not None
    assert Note.query.filter(Note.parent_id == plant.id).count() == len(leaves) - 1


# ---- dashboard counts imported documents, not their leaves ----

def test_dashboard_documents_stat_counts_each_plant_once(client):
    import re
    _import_doc(client)

    page = client.get('/dashboard').data.decode()
    stats = [int(n) for n in re.findall(r'class="stat-number">(\d+)<', page)]
    total, documents = stats[0], stats[1]
    assert total >= 4  # one plant + at least three leaves
    assert documents == 1