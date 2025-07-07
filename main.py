from flask import Flask, render_template, url_for, request, redirect
import csv
import stripe
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = 'https://arnold-brothers-web.onrender.com'

@app.route("/")
def my_home():
    today = datetime.today().strftime('%B %d, %Y')
    return render_template('index.html', today=today)

@app.route("/<string:page_name>")
def html_page(page_name):
    return render_template(f"{page_name}.html")

@app.route('/generic')
def generic_page():
    success = request.args.get('success')
    return render_template('generic.html', success=success)

@app.route("/privacy")
def privacy_policy():
    return render_template("privacy.html")

@app.route("/gigs")
def gigs():
    return render_template("gigs.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/booking")
def booking():
    return render_template("booking.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        gig_date = request.form['gig_date']

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': f'Guitar Gig Booking ({gig_date})',
                    },
                    'unit_amount': 5000 * 100,  # £50.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
            metadata={
                'gig_date': gig_date
            }
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        data = request.form.to_dict()
        write_to_csv(data)
        return redirect('/generic?success=1')
    except Exception as e:
        return f'An error occurred: {e}'

def write_to_file(data):
    with open('database.txt', mode='a') as database:
        name = data.get("name", "")
        email = data.get("email", "")
        message = data.get("message", "")
        database.write(f'\n{name},{email},{message}')

def write_to_csv(data):
    with open('database.csv', mode='a', newline='') as database2:
        name = data.get("name", "")
        email = data.get("email", "")
        message = data.get("message", "")
        csv_writer = csv.writer(database2, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([name, email, message])

if __name__ == '__main__':
    app.run(debug=True)
