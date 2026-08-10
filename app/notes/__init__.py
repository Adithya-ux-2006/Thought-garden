from flask import Blueprint

bp = Blueprint('notes', __name__, url_prefix='/notes')

from app.notes import routes