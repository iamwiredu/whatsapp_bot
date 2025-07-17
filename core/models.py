from django.db import models

class Customer(models.Model):
    phone_number = models.CharField(max_length=20, unique=True,null=True)
    current_step = models.CharField(max_length=50, default='start')
    temp_order_data = models.JSONField(default=dict)

    def __str__(self):
        return self.phone_number

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True)
    item = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    address = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
