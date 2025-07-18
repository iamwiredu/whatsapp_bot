from django.db import models
import uuid

class Order(models.Model):
    slug = models.SlugField(default=uuid.uuid4, unique=True)
    phone_number = models.CharField(max_length=20)
    item = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    address = models.TextField()
    amount = models.IntegerField()  # store amount in kobo (e.g. GHS 25.00 => 2500)
    paystack_slug = models.CharField(max_length=255, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
