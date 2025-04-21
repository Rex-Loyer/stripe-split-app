from flask import Flask, request, jsonify
import stripe
import uuid
import os

app = Flask(__name__)


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
        payment_intent_id = session['payment_intent']

        # Step 1: Retrieve the PaymentIntent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Step 2: Get the charge ID from the PaymentIntent
        charge_id = payment_intent['charges']['data'][0]['id']

        # Step 3: Retrieve the balance transaction for the charge
        charge = stripe.Charge.retrieve(charge_id)
        balance_txn_id = charge['balance_transaction']
        balance_txn = stripe.BalanceTransaction.retrieve(balance_txn_id)

        # Step 4: Extract the actual fee
        stripe_fee = balance_txn['fee']
        amount_received = balance_txn['amount']  # gross amount
        net_amount = balance_txn['net']

        # Step 5: Split the actual net
        half_amount = net_amount // 2

        # Step 6: Transfer half to your partner
        stripe.Transfer.create(
            amount=half_amount,
            currency='usd',
            destination=PARTNER_ACCOUNT_ID,
            transfer_group=order_id
        )

    return jsonify(success=True)
