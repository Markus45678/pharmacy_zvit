from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва категорії")
    description = models.TextField(blank=True, verbose_name="Опис")
    icon = models.CharField(max_length=50, default="bi-capsule", verbose_name="Іконка")
    color = models.CharField(max_length=20, default="#0068C2", verbose_name="Колір")
    bg_color = models.CharField(max_length=20, default="#E8F4FD", verbose_name="Колір фону")

    class Meta:
        db_table = 'inventory_category'
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('pharmacy:category_detail', kwargs={'pk': self.pk})


class Product(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Назва препарату")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Категорія")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='products_created', verbose_name="Створив")
    description = models.TextField(blank=True, verbose_name="Опис")
    instruction = models.TextField(blank=True, verbose_name="Спосіб застосування")
    warning = models.TextField(blank=True, verbose_name="Застереження")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'), verbose_name="Ціна (грн)")
    stock_quantity = models.IntegerField(default=0, verbose_name="Кількість на складі (шт)")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Термін придатності")
    rx_required = models.BooleanField(default=False, verbose_name="За рецептом (Rx)")
    dosage_form = models.CharField(max_length=100, default="Таблетки", verbose_name="Форма випуску")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата створення")

    class Meta:
        db_table = 'inventory_product'
        verbose_name = "Препарат / Товар"
        verbose_name_plural = "Препарати / Товари"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('pharmacy:product_detail', kwargs={'pk': self.pk})

    @property
    def total_stock(self):
        return self.stock_quantity

    @property
    def earliest_expiry(self):
        return self.expiry_date

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return 999
        return (self.expiry_date - timezone.now().date()).days


Medicine = Product


class Order(models.Model):
    STATUS_CHOICES = (
        ('COMPLETED', 'Виконано'),
        ('CANCELLED', 'Скасовано'),
        ('PENDING', 'В обробці'),
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Створив")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата та час")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED', verbose_name="Статус")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Сума (грн)")
    stock_deducted = models.BooleanField(default=True, verbose_name="Списано зі складу")

    class Meta:
        db_table = 'inventory_order'
        verbose_name = "Замовлення (Продаж)"
        verbose_name_plural = "Замовлення (Продажі)"
        ordering = ['-created_at']

    def __str__(self):
        return f"Замовлення #{self.id} від {self.created_at.strftime('%d.%m.%Y %H:%M')} ({self.total_amount} грн)"

    @property
    def receipt_number(self):
        return f"CHK-{self.created_at.strftime('%Y%m%d')}-{self.id:04d}"


Sale = Order


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Замовлення")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', verbose_name="Препарат")
    quantity = models.IntegerField(default=1, verbose_name="Кількість (шт)")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна за 1 од. (грн)")

    class Meta:
        db_table = 'inventory_orderitem'
        verbose_name = "Позиція замовлення"
        verbose_name_plural = "Позиції замовлення"

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def medicine(self):
        return self.product

    @property
    def sale(self):
        return self.order


SaleItem = OrderItem
