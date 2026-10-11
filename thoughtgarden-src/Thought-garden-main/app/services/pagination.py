"""A minimal stand-in for Flask-SQLAlchemy's Pagination object.

Used wherever a result list has already been fully computed and sorted in
Python (e.g. semantic/hybrid search, which ranks notes by similarity
score rather than a plain SQL ORDER BY) and just needs slicing into pages.
Previously this class was copy-pasted separately inside semantic_search()
and hybrid_search() in search_service.py; the two copies had drifted -
only one of them defined iter_pages(), so a template calling it on the
other copy's result would raise AttributeError. This is the one copy.
"""


class SimplePagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge
                    or (num > self.page - left_current - 1 and num < self.page + right_current)
                    or num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num
