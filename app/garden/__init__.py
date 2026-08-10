from flask import Blueprint

bp = Blueprint('garden', __name__, url_prefix='/garden')

from app.garden import routes