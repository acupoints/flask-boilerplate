from flask import request, jsonify, Blueprint
from my_app import db
from my_app.catalog.models import Product, Category
# from my_app.catalog.models import Product
from decimal import Decimal
from my_app import redis
from flask import render_template
from flask import flash, redirect, url_for
from sqlalchemy.orm.util import join
from my_app.catalog.models import ProductForm, CategoryForm

import os
from werkzeug import secure_filename
from my_app import ALLOWED_EXTENSIONS, UPLOAD_FOLDER


catalog = Blueprint('catalog', __name__)

from functools import wraps

def template_or_json(template=None):
    def decorated(f):
        @wraps(f)
        def decorated_fn(*args, **kwargs):
            ctx = f(*args, **kwargs)
            if request.is_xhr or not template:
                return jsonify(ctx)
            else:
                return render_template(template, **ctx)
        
        return decorated_fn
    return decorated

@catalog.route('/2')
@catalog.route('/home2')
@template_or_json('home.html')
def home():
    # return "Welcome to the Catalog Home."
    products = Product.query.all()
    return dict(count=len(products))
    # if request.is_xhr:
    #     products = Product.query.all()
    #     return jsonify({
    #         'count': len(products)
    #     })
    # return render_template('home.html')

@catalog.route('/product/<id>')
def product(id):
    # product = Product.objects.get_or_404(key=key)
    product = Product.query.get_or_404(id)
    # return 'Product - %s, $%s' % (product.name, product.price)
    return render_template('product.html', product=product)

@catalog.route('/products')
@catalog.route('/products/<int:page>')
def products(page=1):
    products = Product.query.paginate(page, 10)
    return render_template('products.html', products=products)


# @catalog.route('/products')
# def products():
#     products = Product.objects.all()
#     res = {}
#     for product in products:
#         res[product.key] = {
#             'name': product.name,
#             'price': str(product.price),
#         }
#     return jsonify(res)

# @catalog.route('/products')
# def products():
#     products = Product.query.all()
#     res = {}
#     for product in products:
#         res[product.id] = {
#             'name': product.name,
#             'price': str(product.price),
#             'category': product.category.name,
#         }
#     return jsonify(res)

# @catalog.route('/product-create', methods=['POST',])
# def create_product():
#     name = request.form.get('name')
#     key = request.form.get('key')
#     price = request.form.get('price')
#     product = Product(
#                        name = name,
#         key = key,
#         price = Decimal(price)
#     )
#     product.save()
#     return 'Product created.'

def allowed_file(filename):
    return '.' in filename and filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

from werkzeug.datastructures import CombinedMultiDict

@catalog.route('/product-create', methods=['POST','GET'])
def create_product():
    # form = ProductForm(CombinedMultiDict([request.form, request.files]), csrf_enabled=False)
    form = ProductForm(CombinedMultiDict([request.form, request.files]))
    # categories = [(c.id, c.name) for c in Category.query.all()]
    # form.category.choices = categories

    # if request.method == 'POST' and form.validate():
    # flash("%s" % form.name.data, "success")
    # flash("%s" % form.price.data, "success")
    # flash("%s" % form.category.data, "success")
    # flash("%s" % form.image.data, "success")
    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        category = Category.query.get_or_404(
            form.category.data
        )
        # name = request.form.get('name')
        # price = request.form.get('price')
        # categ_name = request.form.get('category')
        # category = Category.query.filter_by(name=categ_name).first()
        # if not category:
        #     category = Category(categ_name)
        ###
        image = form.image.data
        if allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        product = Product(name, price, category, filename)

        db.session.add(product)
        db.session.commit()
        flash('The product %s has been created' % name, 'success')
        return redirect(url_for('catalog.product', id=product.id))
    
    if form.errors:
        flash(form.errors, 'danger')

    return render_template('product-create.html', form=form)

@catalog.route('/product-search')
@catalog.route('/product-search/<int:page>')
def product_search(page=1):
    name = request.args.get('name')
    price = request.args.get('price')
    company = request.args.get('company')
    category = request.args.get('category')
    products = Product.query
    if name:
        products = products.filter(Product.name.like('%'+name+'%'))
    if price:
        products = products.filter(Product.price == price)
    if company:
        products = products.filter(Product.company.like('%'+company+'%'))
    if category:
        products = products.select_from(join(Product, Category)).filter(Category.name.like('%'+category+'%'))
    return render_template('products.html', products=products.paginate(page, 10))



@catalog.route('/category/<id>')
def category(id):
    category = Category.query.get_or_404(id)
    return render_template('category.html', category=category)

@catalog.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)


@catalog.route('/category-create', methods=['POST', 'GET'])
def create_category():
    form = CategoryForm(csrf_enabled=False)
    if form.validate_on_submit():
        name = form.name.data
        # name = request.form.get('name')

        category = Category(name)
        db.session.add(category)
        db.session.commit()
        flash('The category %s has been created' % name, 'success')
        return redirect(url_for('catalog.category', id=category.id))

    if form.errors:
        flash(form.errors, "danger")
    # return 'Category created.'
    return render_template('category-create.html', form=form)


from flask_restful import Resource
from my_app import api
from flask import abort
import json
from flask_restful import reqparse
parser = reqparse.RequestParser()
parser.add_argument('name', type=str)
parser.add_argument('price', type=float)
parser.add_argument('category', type=dict)

class ProductApi(Resource):
    def get(self, id=None, page=1):
        # Return product data
        # return 'This is a GET response'
        if not id:
            products = Product.query.paginate(page, 10).items
        else:
            products = [Product.query.get(id)]
        
        if not products:
            abort(404)
        res = {}
        for product in products:
            res[product.id] = {
                'name': product.name,
                'price': product.price,
                'category': product.category.name
            }
        return json.dumps(res)

    def post(self):
        # Create a new product
        # return 'This is a POST response'
        args = parser.parse_args()
        name = args['name']
        price = args['price']
        categ_name = args['category']['name']
        category = Category.query.filter_by(name=categ_name).first()
        if not category:
            category = Category(categ_name)
        product = Product(name, price, category, "iphone6.PNG")
        db.session.add(product)
        db.session.commit()
        res = {}
        res[product.id] = {
            'name': product.name,
            'price': product.price,
            'category': product.category.name,
        }
        return json.dumps(res)

    def put(self, id):
        # Update the product with given id
        # return 'This is a PUT response'
        args = parser.parse_args()
        name = args['name']
        price = args['price']
        categ_name = args['category']['name']
        category = Category.query.filter_by(name=categ_name).first()
        Product.query.filter_by(id=id).update({
            'name': name,
            'price': price,
            'category_id': category.id,
        })
        db.session.commit()
        product = Product.query.get_or_404(id)
        res = {}
        res[product.id] = {
            'name': product.name,
            'price': product.price,
            'category': product.category.name,
        }
        return json.dumps(res)

    def delete(self, id):
        # Delete the product with given id
        # return 'This is a DELETE response'
        product = Product.query.filter_by(id=id)
        product.delete()
        db.session.commit()
        return json.dumps({'response': 'Success'})

api.add_resource(ProductApi
    ,'/api/product'
    , '/api/product/<int:id>'
    , '/api/product/<int:id>/<int:page>'
    )
