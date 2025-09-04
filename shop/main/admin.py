from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)    
admin.site.register(ProductImage)
admin.site.register(Customer)
admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(Delivery)
admin.site.register(Discount)
admin.site.register(DiscountCode)