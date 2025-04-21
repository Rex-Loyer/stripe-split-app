from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import uuid
import os

app = Flask(__name__)
CORS(app)

stripe.api_key = os.environ['STRIPE_SECRET_KEY']
PARTNER_ACCOUNT_ID = os.environ['PARTNER_ACCOUNT_ID']
WEBHOOK_SECRET = os.environ['STRIPE_WEBHOOK_SECRET']

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    data = request.get_json()
    base_amount = data.get("base_amount", 10000)  # default to $100 if missing
    order_id = str(uuid.uuid4())

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Shared Product'},
                'unit_amount': base_amount,
            },
            'quantity': 1,
        }],
        mode='payment',
