
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Назва категорії')),
                ('description', models.TextField(blank=True, verbose_name='Опис')),
                ('icon', models.CharField(default='bi-capsule', max_length=50, verbose_name='Іконка')),
                ('color', models.CharField(default='#0068C2', max_length=20, verbose_name='Колір')),
                ('bg_color', models.CharField(default='#E8F4FD', max_length=20, verbose_name='Колір фону')),
            ],
            options={
                'verbose_name': 'Категорія',
                'verbose_name_plural': 'Категорії',
                'db_table': 'inventory_category',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата та час')),
                ('status', models.CharField(choices=[('COMPLETED', 'Виконано'), ('CANCELLED', 'Скасовано'), ('PENDING', 'В обробці')], default='COMPLETED', max_length=20, verbose_name='Статус')),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Сума (грн)')),
                ('stock_deducted', models.BooleanField(default=True, verbose_name='Списано зі складу')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Створив')),
            ],
            options={
                'verbose_name': 'Замовлення (Продаж)',
                'verbose_name_plural': 'Замовлення (Продажі)',
                'db_table': 'inventory_order',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='Назва препарату')),
                ('description', models.TextField(blank=True, verbose_name='Опис')),
                ('instruction', models.TextField(blank=True, verbose_name='Спосіб застосування')),
                ('warning', models.TextField(blank=True, verbose_name='Застереження')),
                ('price', models.DecimalField(decimal_places=2, default=Decimal('50.00'), max_digits=10, verbose_name='Ціна (грн)')),
                ('stock_quantity', models.IntegerField(default=0, verbose_name='Кількість на складі (шт)')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='Термін придатності')),
                ('rx_required', models.BooleanField(default=False, verbose_name='За рецептом (Rx)')),
                ('dosage_form', models.CharField(default='Таблетки', max_length=100, verbose_name='Форма випуску')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата створення')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='pharmacy.category', verbose_name='Категорія')),
            ],
            options={
                'verbose_name': 'Препарат / Товар',
                'verbose_name_plural': 'Препарати / Товари',
                'db_table': 'inventory_product',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1, verbose_name='Кількість (шт)')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Ціна за 1 од. (грн)')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='pharmacy.order', verbose_name='Замовлення')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='pharmacy.product', verbose_name='Препарат')),
            ],
            options={
                'verbose_name': 'Позиція замовлення',
                'verbose_name_plural': 'Позиції замовлення',
                'db_table': 'inventory_orderitem',
            },
        ),
    ]
