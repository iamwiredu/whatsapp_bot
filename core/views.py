import uuid
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Order
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from urllib.parse import quote

def home(request):
    return render(request,'home.html')

@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        # Extract order details
        phone = data.get('phone_number')
        item = data.get('item')
        quantity = data.get('quantity')
        address = data.get('address')
        amount = data.get('amount')  # in pesewas
        paystack_slug = str(uuid.uuid4())  # unique slug for payment & order

        order = Order.objects.create(
            slug=paystack_slug,
            phone_number=phone,
            item=item,
            quantity=quantity,
            address=address,
            amount=amount,
            paystack_slug=paystack_slug,
        )

        order_url = request.build_absolute_uri(f"/order/{order.slug}/")
        return JsonResponse({
            'success': True,
            'order_id': order.slug,
            'order_url': order_url,
        })

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def view_order(request, slug):
    order = get_object_or_404(Order, slug=slug)

    if order.paid:
        return redirect('payment_success',slug=order.slug)

    whatsapp_number = '233XXXXXXXXX'  # Your business line
    message = f"Hello, I’ve completed payment for my order ({order.slug})"
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text={message.replace(' ', '%20')}"
    print(order.phone_number)
    return render(request, 'makePayment.html', {
        'order': order,
        'paystack_public_key': 'https://07229c36e080.ngrok-free.app/create-order/',
        'callback_url': f"https://grabtexts.shop/payment-success/{order.slug}/",
        'whatsapp_link': whatsapp_link,
    })




def payment_success(request, slug):
    order = get_object_or_404(Order, slug=slug)
    whatsapp_response = None  # default

    if not order.paid:
        order.paid = True
        order.save()

        # Call Node.js to send WhatsApp message
        try:
            node_url = 'https://whatsapp-bot-node-ej2c.onrender.com/send-payment-confirmation'
            payload = {
                'phone': order.phone_number,
                'slug': order.slug,
                'order_id':order.order_id
            }

            response = requests.post(node_url, json=payload, timeout=10)
            if response.ok:
                whatsapp_response = response.json()
            else:
                whatsapp_response = {
                    'success': False,
                    'error': f'Status {response.status_code}'
                }

        except Exception as e:
            print("⚠️ Failed to notify WhatsApp bot:", e)
            whatsapp_response = {
                'success': False,
                'error': str(e)
            }

    return render(request, 'orderSuccess.html', {
        'order': order,
        'whatsapp_response': whatsapp_response
    })