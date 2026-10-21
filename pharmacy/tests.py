from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ProductAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='safe-password')
        self.other_user = User.objects.create_user('other', password='safe-password')
        category = Category.objects.create(name='Тестова категорія')
        self.product = Product.objects.create(
            name='Тестовий препарат', category=category, created_by=self.owner,
            price='10.00', stock_quantity=5,
        )

    def test_only_owner_can_open_update_page(self):
        self.client.login(username='other', password='safe-password')
        response = self.client.get(reverse('pharmacy:product_update', args=[self.product.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_is_assigned_by_create_view(self):
        self.client.login(username='owner', password='safe-password')
        response = self.client.post(reverse('pharmacy:product_create'), {
            'name': 'Новий препарат', 'category': self.product.category.pk,
            'price': '25.00', 'stock_quantity': 3, 'dosage_form': 'Таблетки',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.get(name='Новий препарат').created_by, self.owner)

