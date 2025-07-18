import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .serializers import OrderSerializer

@api_view(['POST'])
def create_order(request):
    data = request.data
    item = data.get('item')
    quantity = int(data.get('quantity'))
    unit_price = {
        'pizza': 2500,
        'burger': 1500,
        'fries': 1000
    }.get(item.lower())

    if not unit_price:
        return Response({"error": "Invalid item"}, status=400)

    amount = unit_price * quantity
    order = Order.objects.create(
        phone_number=data.get('phone_number'),
        item=item,
        quantity=quantity,
        address=data.get('address'),
        amount=amount,
    )

    # Create Paystack Page
    paystack_secret = settings.PAYSTACK_SECRET_KEY
    headers = {
        "Authorization": f"Bearer {paystack_secret}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": f"{item.title()} x{quantity}",
        "description": f"Order for {order.phone_number} to {order.address}",
        "amount": amount * 100,  # kobo or pesewas
        "currency": "GHS"
    }

    r = requests.post("https://api.paystack.co/page", json=payload, headers=headers)
    res = r.json()

    if r.status_code != 200 or not res.get('status'):
        return Response({"error": "Failed to create Paystack page"}, status=500)

    paystack_slug = res['data']['slug']
    order.paystack_slug = paystack_slug
    order.save()

    return Response({
        "success": True,
        "order_slug": order.slug,
        "payment_page": f"https://paystack.com/pay/{paystack_slug}"
    })
