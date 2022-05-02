from flask import Blueprint, render_template

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/first_page')

def first_page():
    return render_template('index.html')

@bp.route('/')
def index():
    return 'index!'