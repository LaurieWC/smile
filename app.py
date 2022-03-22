from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "login successful"
DATABASE = "C:/Users/18047/OneDrive - Wellington College/13DTS/Smile/smile.db"


def create_connection(db_file):
    """
    Create a connection with database
    parameter: name of the database file
    returns: a connection to the file
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        return None


def is_logged_in():
    """
    A function to return whether the user is logged in or not
    """
    if session.get('email') is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/menu')
def render_menu_page():
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, price, image, id FROM product"
    cur = con.cursor()
    cur.execute(query)
    product_list = cur.fetchall()
    con.close()

    if is_logged_in():
        first_name = session['fname']

    return render_template('menu.html', products=product_list, logged_in=is_logged_in(), fname=first_name)


@app.route('/addtocart/<product_id>')
def render_addtocart_page(product_id):
    print("Add {} to cart".format(product_id))
    userid = session['customer_id']
    timestamp = datetime.now()
    try:
        product_id = int(product_id)
    except ValueError:
        print("{} is not am integer".format(product_id))
        return redirect(request.referrer + "?error=Invalid+product+id")
    query = "INSERT INTO cart(id,customerid,productid,timestamp) VALUES (NULL,?,?,?)"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (userid, product_id, timestamp))
    con.commit()
    con.close()
    return redirect(request.referrer)


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, fname, password FROM customer WHERE email=?"
        cur = con.cursor()
        cur.execute(query, (email, ))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]

        else:
            return redirect('/login?error=email+or+password+is+invalid')
            # Set up a session for this login

        if not bcrypt.check_password_hash(db_password, password):
            return redirect('/login?error=email+or+password+is+invalid')

        session['email'] = email
        session['customer_id'] = userid
        session['fname'] = firstname
        session['cart'] = []
        return redirect('/menu')
    return render_template('login.html', logged_in=is_logged_in())


@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time')


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Check to see whether the passwords match
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')
        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)

        query = "INSERT INTO customer(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"

        cur = con.cursor()  # Create cursor to run the query
        cur.execute(query, (fname, lname, email, hashed_password))
        con.commit()
        con.close()
        return redirect('/login')

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in())


@app.route('/cart')
def render_cart():
    if not is_logged_in():
        return redirect('/menu')
    else:
        customer_id = session['customer_id']
        query = "SELECT productid FROM cart WHERE customerid=?;"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (customer_id, ))
        product_ids = cur.fetchall()
        for i in range(len(product_ids)):
            product_ids[i] = product_ids[i][0]
        unique_product_ids = list(set(product_ids))
        unique_product_ids.sort()
        for i in range(len(unique_product_ids)):
            product_count = product_ids.count(unique_product_ids[i])
            unique_product_ids[i] = [unique_product_ids[i], product_count]
        total = 0
        query = "SELECT name, price FROM product WHERE id = ?"
        for item in unique_product_ids:
            cur.execute(query, (item[0], ))
            item_details = cur.fetchall()
            item.append(item_details[0][0])
            item.append(item_details[0][1])
            item.append(item[1] * item[3])
            total += item[4]
        con.close()
        return render_template('cart.html', cart_data=unique_product_ids,
                               logged_in=is_logged_in(), total=total,
                               fname=session['fname'])


app.run(host='0.0.0.0', debug=True)
