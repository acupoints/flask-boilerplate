from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mongoengine import MongoEngine
from flask import render_template

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
# db.create_all()

# app.config['MONGODB_SETTINGS'] = {'DB': 'my_catalog'}
# db = MongoEngine(app)
import os
ALLOWED_EXTENSIONS=set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER=os.path.realpath('.')+'/my_app/static/uploads'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

## 启用CSRF保护
# app.config['WTF_CSRF_SECRET_KEY']='random key for form'
# from flask_wtf.csrf import CSRFProtect
# CSRFProtect(app)

from redis import Redis
redis = Redis()

from flask_migrate import Migrate, MigrateCommand
migrate = Migrate(app, db)

# db = SQLAlchemy()
# def create_app():
#     app = Flask(__name__)
#     db.init_app(app)
#     return app
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='auth.login'

from flask_restful import Api
api = Api(app)

from my_app.catalog.views import catalog
app.register_blueprint(catalog)
from my_app.auth.views import auth
app.register_blueprint(auth)


app.secret_key="some_random_key"

###
# from flask import request
# def get_request():
#     bar = request.args.get('foo', 'bar')
#     return '-3- A simple Flask request where foo is %s' % bar

# app.add_url_rule('/a-get-request2', view_func=get_request)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

db.create_all()