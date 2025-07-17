import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Customer, Order

WHAPI_API_TOKEN = "e73B1hnZ59F2jB7QFXjBtzPGJTGtsMKg"
WHAPI_BASE_URL = "https://gate.whapi.cloud"

MENU = {
    "pizza": 25,
    "burger": 15,
    "fries": 10
}


def send_whatsapp_message(to, message):
    url = f"{WHAPI_BASE_URL}/messages/text"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHAPI_API_TOKEN}"
    }
    body = {
        "to": to,
        "body": message
    }

    print(f"📨 Sending to: {to}")
    print(f"📩 Message: {message}")
    print(f"📡 Request Body: {body}")

    response = requests.post(url, headers=headers, json=body)
    print(f"✅ Whapi Response: {response.status_code}")
    print(f"🔎 Response Content: {response.text}")


@csrf_exempt
def webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        messages = data.get('messages', [])
        if not messages:
            print("No messages in webhook")
            return JsonResponse({'error': 'No messages'}, status=400)

        message_data = messages[0]
        if message_data.get("type") != "text":
            return JsonResponse({'status': 'ignored'}, status=200)

        phone = message_data['from']
        message = message_data.get('text', {}).get('body', '').strip().lower()

        customer, _ = Customer.objects.get_or_create(phone_number=phone)

        # RESET FLOW if user types "hi"
        if message == "hi":
            menu_text = "🍔 *Menu*\n" + "\n".join([f"- {item.title()} (GH₵{price})" for item, price in MENU.items()])
            send_whatsapp_message(phone, f"Hi! 👋 Welcome to our Burger Hub.\n\n{menu_text}\n\nPlease type the *name* of the item you'd like to order.")
            customer.current_step = 'awaiting_item'
            customer.temp_order_data = {}
            customer.save()
            return JsonResponse({'status': 'menu_sent'})

        # FLOW: Item → Quantity → Address
        step = customer.current_step

        if step == 'awaiting_item':
            if message in MENU:
                customer.temp_order_data = {'item': message}
                customer.current_step = 'awaiting_quantity'
                send_whatsapp_message(phone, f"Great choice! 🍽 How many *{message}s* would you like?")
            else:
                send_whatsapp_message(phone, "❌ Sorry, we don't have that item. Please choose from the menu: pizza, burger, or fries.")
        
        elif step == 'awaiting_quantity':
            if message.isdigit():
                customer.temp_order_data['quantity'] = message
                customer.current_step = 'awaiting_address'
                send_whatsapp_message(phone, "📍 Please enter your *delivery address*.")
            else:
                send_whatsapp_message(phone, "❌ Please enter a valid number for quantity.")

        elif step == 'awaiting_address':
            try:
                item = customer.temp_order_data['item']
                quantity = int(customer.temp_order_data['quantity'])
                address = message

                Order.objects.create(
                    customer=customer,
                    item=item,
                    quantity=quantity,
                    address=address
                )

                send_whatsapp_message(
                    phone,
                    f"✅ Order confirmed!\n\n🛒 {quantity} x {item.title()}\n📍 {address}\n\nWe'll process your order shortly!"
                )
                customer.temp_order_data = {}
                customer.current_step = 'start'
            except Exception as e:
                print("Order saving error:", e)
                send_whatsapp_message(phone, "⚠️ Something went wrong saving your order. Please start again by typing *hi*.")
                customer.temp_order_data = {}
                customer.current_step = 'start'

        else:
            send_whatsapp_message(phone, "👋 Hi! To place an order, just type *hi*.")

        customer.save()
        return JsonResponse({'status': 'ok'})

    except Exception as e:
        print("Webhook error:", e)
        return JsonResponse({'error': 'Invalid payload'}, status=400)
