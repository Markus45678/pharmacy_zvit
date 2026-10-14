from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_product_owners(apps, schema_editor):
    Product = apps.get_model('pharmacy', 'Product')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    owner = User.objects.filter(is_superuser=True).order_by('id').first() or User.objects.order_by('id').first()
    if owner is None:
        owner = User.objects.create(username='system_owner', is_active=False)
    Product.objects.filter(created_by__isnull=True).update(created_by=owner)


class Migration(migrations.Migration):
    dependencies = [('pharmacy', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='product', name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='products_created', to=settings.AUTH_USER_MODEL,
                                    verbose_name='Створив'),
        ),
        migrations.RunPython(assign_product_owners, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product', name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products_created',
                                    to=settings.AUTH_USER_MODEL, verbose_name='Створив'),
        ),
    ]
