from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.mime.text import MIMEText
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'made in haven'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
manager = LoginManager(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


# база данных
class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    text = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return self.title


class User (db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_buyer = db.Column(db.String(128), nullable=False)
    number_b = db.Column(db.String(50), nullable=False)
    mail_buyer = db.Column(db.String(128), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    item = db.relationship('Items', backref='orders')

    def __repr__(self):
        return self


seller_login = "admin"
seller_password = "qwerty"
logged_seller = False


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# главная страница
@app.route('/')
def index():
    categories = Category.query.all()
    return render_template("index.html", categories=categories)


# описание магаза
@app.route('/about')
def about():
    return render_template('about.html')


# адреса
@app.route('/adress')
def adress():
    return render_template('adress.html')


@app.route('/login_page', methods=['GET','POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            return redirect('/')
    return render_template('login_page.html')

@app.route('/create', methods=['POST', 'GET'])
def create():
    if logged_seller == True:
        if request.method == "POST":
            title = request.form['title']
            price = request.form['price']
            text = request.form['text']
            image = request.form['image']
            category_id = int(request.form['category'])

            new_items = Items(title=title, price=price, text=text, image=image, category_id=category_id)

            try:
                db.session.add(new_items)
                db.session.commit()
                return redirect('/')
            except:
                return "ошибка"
        else:
            categories = Category.query.all()
            return render_template('create.html', categories=categories)
    else:
        return redirect('/seller')


@app.route('/seller', methods=['GET', 'POST'])
def seller():
    global logged_seller
    if request.method == 'POST':
        username = request.form['login']
        password = request.form['password']
        if username == seller_login and password == seller_password:
            logged_seller = True
            return redirect('/create')
    return render_template('seller.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/logoutsell', methods=['GET', 'POST'])
def logoutsell():
    global logged_seller
    logged_seller = False
    return redirect('/')


@app.route("/category", methods=["POST"])
def show_category():
    category_id = request.form.get("category_id")
    category = Category.query.get(category_id)
    products = Items.query.filter_by(category_id=category_id).all()
    categories = Category.query.all()
    return render_template("laptops.html", category=category, products=products, categories=categories)


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')

    if request.method == "POST":
        hash_pwd = generate_password_hash(password)
        new_user = User(login=login, password=hash_pwd)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/')
    return render_template('register.html')


@app.route('/help', methods=['POST', 'GET'])
def help():
    if request.method == "POST":
        phone_number = request.form['phone_number']

        sender_email = "timyrbylat0309@gmail.com"
        password = "odmz gzie fvyn qotp"

        message = MIMEText(f"Номер телефона: {phone_number}")
        message['Subject'] = 'номер телефона клиента'
        message['From'] = sender_email
        message['To'] = sender_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, sender_email, message.as_string())
        return redirect('/')
    else:
        return render_template('help.html')


@app.route("/search", methods=["POST"])
def search():
    query = request.form["query"]
    results = Items.query.filter(Items.title.ilike(f"%{query}%")).all()
    categories = Category.query.all()
    return render_template("search.html", results=results,categories=categories)


#@app.route('/buy/)
#def buy(product_id):
 #   product_name = Items.get(product_id, "Товар не найден")
 #   return redirect('/submit_order.html', product=product_name)


@app.route('/submit_order/<int:product_id>', methods=['POST', 'GET'])
@login_required
def submit_order(product_id):
    if request.method == "POST":
        name_buyer = request.form['name_buyer']
        number_b = request.form['number_b']
        mail_buyer = request.form['mail_buyer']

        order = Orders(name_buyer=name_buyer, number_b=number_b, mail_buyer=mail_buyer, item_id=product_id)

        try:
            db.session.add(order)
            db.session.commit()
            return redirect('/')
        except:
            return "ошибка"
    else:
        product_name = Items.query.get(product_id)
        return render_template('submit_order.html', product_name=product_name)


if __name__ == '__main__':
    app.run(debug=True)