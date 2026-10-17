from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime
from .models import Category, Product


def validate_product_name(value):
    if len(value.strip()) < 3:
        raise ValidationError('Назва препарату має містити щонайменше 3 символи.')


class ProductForm(forms.ModelForm):
    name = forms.CharField(label='Назва препарату', validators=[validate_product_name])

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'instruction', 'warning', 'price',
                  'stock_quantity', 'expiry_date', 'rx_required', 'dosage_form']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise ValidationError('Ціна повинна бути більшою за нуль.')
        return price


class ProductSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Пошук', max_length=100)


class QuickMedicineAddForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label="Назва препарату",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'наприклад: Ібупрофен'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Категорія",
        required=False,
        empty_label="— Оберіть категорію —",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount = forms.IntegerField(
        min_value=0,
        label="Кількість (шт)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'наприклад: 50'})
    )
    date = forms.CharField(
        label="Термін придатності (дд.мм.рррр)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '31.12.2028'})
    )
    price = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        initial=55.00,
        label="Ціна (грн)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50'})
    )
    rx_required = forms.BooleanField(
        required=False,
        label="Відпуск за рецептом",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_date(self):
        value = self.cleaned_data.get('date', '').strip()
        try:
            datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValidationError('Введіть дату у форматі дд.мм.рррр (наприклад: 31.12.2028).')
        return value
