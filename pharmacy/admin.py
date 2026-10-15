from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Product, Order, OrderItem

admin.site.site_header = "Панель керування складом"
admin.site.site_title = "Склад & Аптека"
admin.site.index_title = "Управління товарами та замовленнями"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'subtotal')
    can_delete = False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price_display', 'stock_badge', 'expiry_badge', 'rx_badge', 'created_at')
    list_filter = ('category', 'rx_required')
    search_fields = ('name', 'description', 'instruction')

    def price_display(self, obj):
        return f"{obj.price:.2f} грн"
    price_display.short_description = "Ціна"

    def rx_badge(self, obj):
        if obj.rx_required:
            return format_html('<span style="background: #F8D7DA; color: #DC3545; padding: 3px 8px; border-radius: 6px; font-weight: bold; font-size: 11px;">За рецептом</span>')
        return format_html('<span style="background: #D4EDDA; color: #155724; padding: 3px 8px; border-radius: 6px; font-weight: bold; font-size: 11px;">Без рецепту</span>')
    rx_badge.short_description = "Відпуск"

    def stock_badge(self, obj):
        qty = obj.stock_quantity
        if qty == 0:
            return format_html('<span style="background: #F8D7DA; color: #DC3545; padding: 4px 8px; border-radius: 6px; font-weight: bold;">0 шт (Немає)</span>')
        elif qty < 5:
            return format_html('<span style="background: #FFF3CD; color: #856404; padding: 4px 8px; border-radius: 6px; font-weight: bold;">{} шт (Закінчується)</span>', qty)
        return format_html('<span style="background: #D4EDDA; color: #155724; padding: 4px 8px; border-radius: 6px; font-weight: bold;">{} шт</span>', qty)
    stock_badge.short_description = "Залишок"

    def expiry_badge(self, obj):
        if not obj.expiry_date:
            return "—"
        today = timezone.now().date()
        date_str = obj.expiry_date.strftime("%d.%m.%Y")
        if obj.expiry_date < today:
            return format_html('<span style="color: #DC3545; font-weight: bold;">{} (Прострочено!)</span>', date_str)
        return date_str
    expiry_badge.short_description = "Термін придатності"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'created_at', 'status', 'total_amount_display', 'stock_deducted')
    list_filter = ('status', 'created_at', 'created_by')
    search_fields = ('id', 'created_by__username')
    inlines = [OrderItemInline]

    def total_amount_display(self, obj):
        return f"{obj.total_amount:.2f} грн"
    total_amount_display.short_description = "Сума"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__created_at',)
