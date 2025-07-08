from flask import Flask, render_template, url_for, request, redirect
import csv
import stripe
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = 'https://arnold-brothers-web.onrender.com'
BOOKINGS_FILE = 'bookings.json'


# --- Booking logic ---

def get_booked_dates():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as file:
            return json.load(file)['booked_dates']
    return []

def add_booked_date(date):
    data = get_booked_dates()
    if date not in data:
        data.append(date)
        with open(BOOKINGS_FILE, 'w') as file:
            json.dump({'booked_dates': data}, file)


# --- Routes ---

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
    # Generate next 30 days (excluding already booked)
    today = datetime.today()
    all_dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    booked = get_booked_dates()
    available = [d for d in all_dates if d not in booked]
    return render_template("booking.html", available_dates=available)

@app.route("/success")
def success():
    gig_date = request.args.get('gig_date')
    if gig_date:
        add_booked_date(gig_date)
    return render_template("success.html")

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        gig_date = request.form.get('gig_date')
        if not gig_date:
            return "Gig date is required.", 400

        booked = get_booked_dates()
        if gig_date in booked:
            return f"Sorry, {gig_date} is already booked.", 400

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': f'Guitar Gig Booking ({gig_date})',
                    },
                    'unit_amount': 5000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{YOUR_DOMAIN}/success?gig_date={gig_date}",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
            metadata={'gig_date': gig_date}
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return f"An error occurred: {e}", 500


# --- Contact Form ---

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
