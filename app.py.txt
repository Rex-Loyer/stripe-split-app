from flask import Flask, request, jsonify
import stripe
import uuid
import os

app = Flask(__name__)
stripe.api_key = os.environ['STRIPE_SECRET_KEY']
PARTNER_ACCOUNT_ID = os.environ['PARTNER_ACCOUNT_ID']
WEBHOOK_SECRET = os.environ['STRIPE_WEBHOOK_SECRET']

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    data = request.get_json()
    base_amount = data.get("base_amount", 10000)
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
        success_url='https://example.com/success',
        cancel_url='https://example.com/cancel',
        metadata={"order_id": order_id},
    )

    return jsonify({"checkout_url": session.url, "order_id": order_id})

@app.route('/webhook', methods=['POST'])
def webhook_received():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception:
        return jsonify(success=False), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata']['order_id']
        amount_received = session['amount_total']
        half_amount = amount_received // 2

        stripe.Transfer.create(
            amount=half_amount,
            currency='usd',
            destination=PARTNER_ACCOUNT_ID,
            transfer_group=order_id
        )

    return jsonify(success=True)
