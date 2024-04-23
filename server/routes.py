"""
Defines the endpoints available (i.e. the valid paths that users can make requests to),
and their responses.
"""

from . import app
from flask import render_template

@app.route('/')
def home():
    return render_template('home/index.html', title='Home')

@app.route('/about')
def about():
    return render_template('about/index.html', title='About')
