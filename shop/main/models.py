from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

# -----------------------
# Customer
# Profile
# -----------------------


class Customer(models.Model):
    """
    Represents a customer profile linked to a Django user.
    Attributes:
        user (OneToOneField): Reference to the associated user account.
        phone (CharField): Optional phone number of the customer.
        address (TextField): Optional address of the customer.
        created_at (DateTimeField): Timestamp when the customer profile was created.
    Methods:
        str(): Returns the username of the associated user.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# -----------------------
# Category
# Model
# -----------------------
# --- Category & Subcategory - --


class Category(models.Model):
    """
    Represents a product category, supporting hierarchical relationships via a parent category.
    Attributes:
        name (CharField): The name of the category (max length 100).
        parent (ForeignKey): Optional reference to another Category as the parent, allowing nested categories.
        description (TextField): Optional description of the category.
        created_at (DateTimeField): Timestamp when the category was created.
    Methods:
        str(): Returns the category name, including parent hierarchy if applicable.
    """
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='subcategories'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if not self.parent else f"{self.parent} > {self.name}"


# --- Tag System(e.g., 'new', 'bestseller', etc.) - --



class Tag(models.Model):
    """
    Represents a tag that can be associated with other models for categorization or filtering.
    Attributes:
        name (CharField): The unique name of the tag, limited to 64 characters.
    Methods:
        str(): Returns the string representation of the tag, which is its name.
    """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

# --- Discount & Time - limited Promotions - --


class Discount(models.Model):
    """
    Represents a discount that can be applied to products or categories.
    Fields:
        name (CharField): The name of the discount.
        percentage (DecimalField): The percentage discount (e.g., 10.00 for 10%).
        value (DecimalField): The fixed amount discount (e.g., $5 off). Optional.
        start_time (DateTimeField): The datetime when the discount becomes active.
        end_time (DateTimeField): The datetime when the discount expires.
        products (ManyToManyField): Products to which the discount applies.
        categories (ManyToManyField): Categories to which the discount applies.
    Methods:
        is_active(): Returns True if the discount is currently active.
        str(): Returns the name of the discount.
    """
    name = models.CharField(max_length=64)
    percentage = models.DecimalField(max_digits=4, decimal_places=2)  # e.g., 10.00 = 10%
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # e.g., fixed $5 off
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    products = models.ManyToManyField('Product', blank=True, related_name='discounts')
    categories = models.ManyToManyField(Category, blank=True, related_name='discounts')


    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def __str__(self):
        return self.name
    

class DiscountCode(models.Model):
    """
    Represents a discount code that can be applied to orders for a discount.
    Fields:
        code (CharField): The unique code that users can enter to receive the discount.
        discount (ForeignKey): The discount associated with this code.
        usage_limit (PositiveIntegerField): The maximum number of times this code can be used. Optional.
        used_count (PositiveIntegerField): The number of times this code has been used.
        valid_from (DateTimeField): The datetime when the code becomes valid.
        valid_to (DateTimeField): The datetime when the code expires.
    Methods:
        is_valid(): Returns True if the code is currently valid and has not exceeded its usage limit.
        str(): Returns the discount code.
    """
    code = models.CharField(max_length=32, unique=True)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='codes')
    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # None means unlimited
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()


    def is_valid(self):
        now = timezone.now()
        if self.valid_from <= now <= self.valid_to:
            if self.usage_limit is None or self.used_count < self.usage_limit:
                return True
        return False

    def __str__(self):
        return self.code


# -----------------------
# Product
# Model
# -----------------------
# --- Product / Package - --


class Product(models.Model):
    """
    Represents a product or package available in the ecommerce platform.
    Attributes:
        CATEGORY_CHOICES (list): Choices for the kind of product ('product' or 'package').
        name (CharField): The name of the product.
        slug (SlugField): Unique slug for the product, used in URLs.
        description (TextField): Optional description of the product.
        category (ForeignKey): Reference to the Category this product belongs to.
        tags (ManyToManyField): Optional tags associated with the product.
        kind (CharField): Specifies if the instance is a 'product' or a 'package'.
        price (DecimalField): Price of the product.
        stock (PositiveIntegerField): Number of items available in stock.
        image (ImageField): Optional image representing the product.
        is_limited (BooleanField): Indicates if the product is a limited edition.
        created_at (DateTimeField): Timestamp when the product was created.
        updated_at (DateTimeField): Timestamp when the product was last updated.
        times_purchased (PositiveIntegerField): Number of times the product has been purchased.
        package_content (ManyToManyField): For packages, references to products included in the package.
    Methods:
        str(): Returns the string representation of the product (its name).
        available_discount(): Returns the best currently active discount for the product, considering both product-specific and category-wide discounts.
        get_absolute_url(): Returns the URL to the product's detail page.
    Notes:
        - If 'kind' is set to 'package', 'package_content' should list the products included in the package.
        - Discounts are assumed to be related via a 'discounts' relationship on both Product and Category models.
    """
    CATEGORY_CHOICES = [
        ('product', 'Product'),
        ('package', 'Package'),
    ]
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    kind = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='product')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_limited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    times_purchased = models.PositiveIntegerField(default=0)
    # For package: which products are inside the package
    package_content = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='packages')

    def __str__(self):
        return self.name


    def available_discount(self):
        # Returns the best (max) active discount for display
        now = timezone.now()
        product_ds = self.discounts.filter(start_time__lte=now, end_time__gte=now)
        category_ds = self.category.discounts.filter(start_time__lte=now, end_time__gte=now)
        return sorted(list(product_ds) + list(category_ds), key=lambda d: d.percentage, reverse=True)[:1]

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})


class ProductImage(models.Model):
    """
    Represents an image associated with a product in the ecommerce platform.
    Attributes:
        product (Product): The product to which this image belongs.
        image (ImageField): The image file for the product, uploaded to 'product_gallery/'.
        caption (str, optional): An optional caption describing the image.
    Methods:
        str(): Returns a string representation indicating the product name associated with the image.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_gallery/')
    caption = models.CharField(max_length=255, blank=True, null=True)  # optional


    def __str__(self):
        return f"Image for {self.product.name}"


# -----------------------

# --- Product
# Evaluation & Reviews - --


class Review(models.Model):
    """
    Represents a product review submitted by a user.
    Fields:
        product (ForeignKey): Reference to the reviewed Product. Deletes reviews if the product is deleted.
        user (ForeignKey): Reference to the User who submitted the review. Deletes reviews if the user is deleted.
        rating (PositiveSmallIntegerField): Rating value from 1 to 5.
        text (TextField): Optional review text provided by the user.
        created_at (DateTimeField): Timestamp when the review was created.
    Methods:
        str: Returns a string representation of the review, showing the rating and product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


def __str__(self):
    return f"{self.rating} stars for {self.product}"


# --- Like
# System - --


class ProductLike(models.Model):
    """
    Represents a 'like' relationship between a user and a product.
    Attributes:
        user (ForeignKey): Reference to the User who liked the product.
        product (ForeignKey): Reference to the Product that was liked.
        created_at (DateTimeField): Timestamp when the like was created.
    Meta:
        unique_together: Ensures that each user can like a specific product only once.
    """
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='likes')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('user', 'product')


# -----------------------
# Order & OrderItem
# -----------------------


class Order(models.Model):
    """
    Represents a customer's order in the ecommerce system.
    Fields:
        customer (Customer): The customer who placed the order.
        created_at (DateTime): Timestamp when the order was created.
        updated_at (DateTime): Timestamp when the order was last updated.
        status (str): Current status of the order. Choices are 'pending', 'processing', 'shipped', 'delivered', 'cancelled'.
        total_price (Decimal): Total price of the order.
    Methods:
        str: Returns a string representation of the order, including its ID and the username of the customer.
    """
    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)
    delivery = models.OneToOneField('Delivery', on_delete=models.SET_NULL, null=True, blank=True, related_name='order')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)


    def __str__(self):
        return f"Order #{self.id} by {self.customer.user.username}"


class OrderItem(models.Model):
    """
    Represents an item within an order, linking a product to an order with a specified quantity and price.
    Attributes:
        order (Order): The order to which this item belongs.
        product (Product): The product being ordered.
        quantity (int): The number of units of the product ordered. Defaults to 1.
        price (Decimal): The price per unit of the product at the time of ordering.
    Methods:
        str(): Returns a human-readable representation of the order item in the format '<quantity> × <product name>'.
    """
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


# -----------------------
# Cart & CartItem
# -----------------------


class Cart(models.Model):
    """
    Represents a shopping cart associated with a customer.
    Attributes:
        customer (Customer): The customer who owns the cart. One-to-one relationship.
        items (ManyToMany[Product]): Products added to the cart, managed through the CartItem intermediary model.
        ordered (bool): Indicates whether the cart has been ordered.
        ordered_date (datetime): The date and time when the cart was ordered. Can be null if not ordered.
        created_at (datetime): Timestamp when the cart was created.
    Methods:
        str(): Returns a string representation of the cart, showing the associated customer's username.
    """
    customer = models.OneToOneField(Customer, related_name="cart", on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through="CartItem")
    ordered = models.BooleanField(default=False)
    ordered_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Cart of {self.customer.user.username}"


class CartItem(models.Model):
    """
    Represents an item in a shopping cart.
    Attributes:
        cart (Cart): The cart to which this item belongs.
        product (Product): The product added to the cart.
        quantity (int): The quantity of the product in the cart. Defaults to 1.
        added_at (datetime): The timestamp when the item was added to the cart.
    Meta:
        unique_together: Ensures that each product appears only once per cart.
    Methods:
        str: Returns a string representation of the cart item in the format "{quantity} × {product.name}".
    """
    cart = models.ForeignKey(Cart, related_name="cart_items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    # For package, you can decide how it should appear in a cart


    class Meta:
        unique_together = ('cart', 'product')


    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


# -----------------------
# Payment
# -----------------------


class Payment(models.Model):
    """
    Represents a payment associated with an order.
    Fields:
        order (Order): The order associated with this payment (one-to-one relationship).
        payment_method (str): The method used for payment (e.g., credit card, PayPal).
        amount (Decimal): The amount paid.
        paid_at (datetime): The timestamp when the payment was made (automatically set on creation).
        status (str): The status of the payment. Choices are 'pending', 'completed', or 'failed'.
    Methods:
        str: Returns a string representation of the payment, indicating the associated order.
    """
    order = models.OneToOneField(Order, related_name="payment", on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )


    def __str__(self):
        return f"Payment for Order #{self.order.id}"


# --- Utility & Properties
# for display & analytics - --
@property
def product_overview(self):
    reviews = self.reviews.all()
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    num_reviews = reviews.count()
    return {'avg_rating': avg_rating or 0, 'num_reviews': num_reviews}
Product.overview = product_overview
# e.g., get trending / bestseller, annotate by times_purchased in views.

class Delivery(models.Model):
    """
    Stores shipment/delivery info related to an Order.
    """
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('returned', 'Returned'),
    ]

    # order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='delivery')
    delivery_method = models.CharField(max_length=50)
    carrier = models.CharField(max_length=100, blank=True, null=True)                     # e.g., DHL, La Poste
    tracking_number = models.CharField(max_length=128, blank=True, null=True)
    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending'
    )
    shipping_address = models.TextField()
    estimated_delivery_date = models.DateField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery for Order #{self.order.id} - {self.delivery_status}"
# -----------------------
