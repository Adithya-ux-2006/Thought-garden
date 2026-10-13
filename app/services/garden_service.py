"""Collapse leaf notes into their plant for garden-level views.

A multi-part imported document is stored as one plant note with several
leaf notes (document chunks). The garden graph and list should show only
the plants - otherwise a big PDF clutters the stage with N sibling nodes.
Every note-with-relationships view (graph /data, the accessible /list,
focus, and the selection panel) maps each underlying relationship onto
the plant level: edges to an endpoint's parent are attributed to the
parent, intra-plant edges are dropped, and each plant's connection count
is the number of distinct plants/notes it connects to.
"""

from app.models import Note


def load_plants_by_id(notes):
    """note_id -> parent Note (or None) for every note in the list.

    One query for all parents, so callers never trigger a lazy load per
    leaf when walking a large garden.
    """
    parent_ids = {n.parent_id for n in notes if n.parent_id}
    parents = {}
    if parent_ids:
        parents = {p.id: p for p in Note.query.filter(Note.id.in_(parent_ids)).all()}
    return {n.id: parents.get(n.parent_id) for n in notes}


def collapse(notes, relationships, plant_of=None):
    """Map active notes + their relationships onto the plant level.

    Returns (visible, edges, counts, leaf_sets, owners, edge_map, plant_of):

    - visible:  deduped top-level notes (plants + standalone), query order
    - edges:    Relationship objects, strongest per distinct top-level pair
    - counts:   top-level note id -> distinct top-level neighbours
    - leaf_sets: top-level note id -> list of its leaf note ids
    - owners:   note id -> top-level note id
    - edge_map: (min_top_id, max_top_id) -> strongest Relationship
    - plant_of: the note_id -> parent-Note map supplied (or loaded)
    """
    if plant_of is None:
        plant_of = load_plants_by_id(notes)

    owners = {}
    visible_by_id = {}
    leaf_sets = {}
    for n in notes:
        parent = plant_of.get(n.id)
        top = parent if parent is not None else n
        owners[n.id] = top.id
        if top.id not in visible_by_id:
            visible_by_id[top.id] = top
        if top.id != n.id:
            leaf_sets.setdefault(top.id, []).append(n.id)

    edge_map = {}
    neighbour_sets = {}
    for rel in relationships:
        a = owners.get(rel.source_note_id)
        b = owners.get(rel.target_note_id)
        if a is None or b is None or a == b:
            continue
        key = (a, b) if a < b else (b, a)
        prev = edge_map.get(key)
        if prev is None or rel.similarity_score > prev.similarity_score:
            edge_map[key] = rel
        neighbour_sets.setdefault(a, set()).add(b)
        neighbour_sets.setdefault(b, set()).add(a)

    counts = {top_id: len(neighbours) for top_id, neighbours in neighbour_sets.items()}
    return (
        list(visible_by_id.values()),
        list(edge_map.values()),
        counts,
        leaf_sets,
        owners,
        edge_map,
        plant_of,
    )