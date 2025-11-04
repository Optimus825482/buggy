"""
Buggy Call - Test Routes
Test ve geliştirme amaçlı route'lar
"""
from flask import Blueprint, render_template

test_bp = Blueprint('test', __name__, url_prefix='/test')


@test_bp.route('/loading')
def test_loading():
    """Loading animasyon test sayfası"""
    return render_template('test_loading.html')
