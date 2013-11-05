from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
import importlib
import os

app = Flask('periscope')
app.config.from_pyfile('config.py')

DIRNAME = os.path.abspath(os.path.dirname(__file__))

### Initialize the sources
sources = {}


def get_klass(klass):
    module_name, class_name = klass.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

for source_name, source_details in app.config['PERISCOPE_SOURCES'].items():
    sources[source_name] = get_klass(source_details['type'])(source_details['config'])
    sources[source_name].description = source_details.get('description')


### Models
if 'SQLALCHEMY_DATABASE_URI' not in app.config:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(DIRNAME, 'periscope.db')

db = SQLAlchemy(app)


class Monitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    task = db.Column(db.Text())


@app.route('/')
def index():
    monitors = Monitor.query.all()
    return render_template('index.html', monitors=monitors)


if __name__ == '__main__':
    app.run()
