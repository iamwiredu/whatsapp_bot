import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Order
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings


@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            phone = data.get('phone_number')
            item = data.get('item')
            quantity = data.get('quantity')
            address = data.get('address')
            amount = data.get('amount')  # in pesewas
            paystack_slug = str(uuid.uuid4())

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

        except Exception as err:
            error_message = str(err)
            print(f"❌ Error creating order: {error_message}")
            return JsonResponse({
                'success': False,
                'error': error_message,
            }, status=500)

def view_order(request, slug):
    order = get_object_or_404(Order, slug=slug)

    whatsapp_number = '233XXXXXXXXX'  # Your business line
    message = f"Hello, I’ve completed payment for my order ({order.slug})"
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text={message.replace(' ', '%20')}"
    print(order.phone_number)
    return render(request, 'makePayment.html', {
        'order': order,
        'paystack_public_key': 'https://07229c36e080.ngrok-free.app/create-order/',
        'callback_url': f"https://yourdomain.com/payment-success/{order.slug}/",
        'whatsapp_link': whatsapp_link,
    })


def payment_success(request, slug):
    order = get_object_or_404(Order, slug=slug)
    order.paid = True
    order.save()

    whatsapp_number = '233XXXXXXXXX'
    message = f"Hello, I’ve completed payment for my order ({order.slug})"
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text={message.replace(' ', '%20')}"

    return redirect(whatsapp_link)
