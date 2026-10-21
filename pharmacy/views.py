from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, Sum

from .models import Category, Product, Order, OrderItem
from .forms import QuickMedicineAddForm, ProductForm, ProductSearchForm

warehouse_required = user_passes_test(lambda user: user.is_superuser)
staff_required = user_passes_test(lambda user: user.is_staff)


class OwnerRequiredMixin(LoginRequiredMixin):
    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user)


class ProductListView(ListView):
    model = Product
    template_name = 'pharmacy/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'created_by')
        self.search_form = ProductSearchForm(self.request.GET)
        if self.search_form.is_valid() and self.search_form.cleaned_data['q']:
            queryset = queryset.filter(name__icontains=self.search_form.cleaned_data['q'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = self.search_form
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'pharmacy/product_detail.html'


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'pharmacy/product_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductUpdateView(OwnerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'pharmacy/product_form.html'


class ProductDeleteView(OwnerRequiredMixin, DeleteView):
    model = Product
    template_name = 'pharmacy/product_confirm_delete.html'
    success_url = reverse_lazy('pharmacy:product_list')


class CategoryListView(ListView):
    model = Category
    template_name = 'pharmacy/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'pharmacy/category_detail.html'


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'pharmacy/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(created_by=self.request.user).prefetch_related('items__product')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'pharmacy/order_detail.html'

    def get_queryset(self):
        return Order.objects.filter(created_by=self.request.user).prefetch_related('items__product')


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Обліковий запис створено. Тепер увійдіть до системи.')
            return redirect(reverse('pharmacy:login'))
    else:
        form = UserCreationForm()
    return render(request, 'pharmacy/register.html', {'form': form})


def _parse_positive_quantity(value):
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


def _sell_product(*, product_id, quantity, user):
    with transaction.atomic():
        product = Product.objects.select_for_update().filter(pk=product_id).first()
        if product is None:
            return None, "not_found"
        if product.stock_quantity < quantity:
            return product, "insufficient_stock"

        product.stock_quantity -= quantity
        product.save(update_fields=['stock_quantity'])
        subtotal = product.price * quantity
        order = Order.objects.create(
            created_by=user,
            total_amount=subtotal,
            status='COMPLETED',
            stock_deducted=True,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price,
        )
    return product, None


def index_redirect(request):
    if not request.user.is_authenticated:
        return redirect('pharmacy:login')
    
    if request.user.is_superuser:
        return redirect('pharmacy:warehouse_dashboard')
    return redirect('pharmacy:pharmacist_catalog')


def user_login_view(request):
    if request.user.is_authenticated:
        return redirect('pharmacy:index')

    error_msg = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Вітаємо, {user.first_name or user.username}!")
            return redirect('pharmacy:index')
        elif error_msg is None:
            error_msg = "Невірний логін або пароль. Спробуйте ще раз."

    quick_accounts = get_user_model().objects.filter(is_active=True).order_by('username')
    quick_accounts_data = [
        {
            'username': account.username,
            'display_name': account.get_full_name() or account.username,
        }
        for account in quick_accounts
    ]
    return render(request, 'pharmacy/login.html', {
        'error': error_msg,
        'quick_accounts_data': quick_accounts_data,
    })


def user_logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Ви вийшли з системи.")
    return redirect('pharmacy:login')


@staff_required
def pharmacist_catalog(request):
    categories = Category.objects.all()
    selected_cat = request.GET.get('cat', 'all')
    search_query = request.GET.get('q', '').strip()
    rx_filter = request.GET.get('rx', 'all')
    stock_filter = request.GET.get('stock', 'all')

    medicines = Product.objects.select_related('category').all()

    if selected_cat and selected_cat != 'all':
        if str(selected_cat).isdigit():
            medicines = medicines.filter(category_id=int(selected_cat))
        else:
            medicines = medicines.filter(category__name__iexact=selected_cat)

    if search_query:
        medicines = medicines.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instruction__icontains=search_query)
        )

    if rx_filter == 'rx':
        medicines = medicines.filter(rx_required=True)
    elif rx_filter == 'otc':
        medicines = medicines.filter(rx_required=False)

    med_list = []
    for med in medicines:
        stock = med.stock_quantity
        if stock_filter == 'in' and stock <= 0:
            continue
        if stock_filter == 'low' and not (0 < stock < 5):
            continue
        if stock_filter == 'none' and stock > 0:
            continue
        med_list.append(med)

    recent_sales = OrderItem.objects.select_related('order', 'product').order_by('-order__created_at')[:25]

    context = {
        'categories': categories,
        'medicines': med_list,
        'selected_cat': selected_cat,
        'search_query': search_query,
        'rx_filter': rx_filter,
        'stock_filter': stock_filter,
        'recent_sales': recent_sales,
    }
    return render(request, 'pharmacy/pharmacist_view.html', context)


@staff_required
def pharmacist_sell(request):
    if request.method != 'POST':
        return redirect('pharmacy:pharmacist_catalog')

    med_id = request.POST.get('medicine_id')
    med_name = request.POST.get('medicine_name', '').strip()
    qty_raw = request.POST.get('quantity', '1')

    qty = _parse_positive_quantity(qty_raw)

    if med_id:
        product = get_object_or_404(Product, id=med_id)
    elif med_name:
        product = Product.objects.filter(name__iexact=med_name).first()
        if not product:
            messages.error(request, f"Препарат '{med_name}' не знайдено.")
            return redirect('pharmacy:pharmacist_catalog')
    else:
        messages.error(request, "Не вказано препарат для продажу.")
        return redirect('pharmacy:pharmacist_catalog')

    product, error = _sell_product(product_id=product.id, quantity=qty, user=request.user)
    if error == "insufficient_stock":
        messages.error(request, f"Неможливо продати {qty} шт.: на складі лише {product.stock_quantity} шт. препарату {product.name}.")
        return redirect('pharmacy:pharmacist_catalog')

    subtotal = product.price * qty
    messages.success(request, f"Успішно продано {product.name} у кількості {qty} шт.! Сума: {subtotal:.2f} грн.")
    return redirect('pharmacy:pharmacist_catalog')


@login_required
@warehouse_required
def warehouse_dashboard(request):
    medicines = Product.objects.select_related('category').all()
    today = timezone.now().date()

    stats = medicines.aggregate(
        total_med_types=Count('id'),
        total_stock_count=Sum('stock_quantity'),
        expired_count=Count('id', filter=Q(expiry_date__lt=today, stock_quantity__gt=0)),
        low_stock_count=Count('id', filter=Q(stock_quantity__gt=0, stock_quantity__lt=5)),
        out_of_stock_count=Count('id', filter=Q(stock_quantity=0)),
    )

    recent_orders = Order.objects.select_related('created_by').prefetch_related('items__product').order_by('-created_at')[:20]
    add_form = QuickMedicineAddForm()
    categories = Category.objects.all()

    context = {
        'medicines': medicines,
        'categories': categories,
        'total_med_types': stats['total_med_types'],
        'total_stock_count': stats['total_stock_count'] or 0,
        'expired_count': stats['expired_count'],
        'low_stock_count': stats['low_stock_count'],
        'out_of_stock_count': stats['out_of_stock_count'],
        'recent_orders': recent_orders,
        'add_form': add_form,
    }
    return render(request, 'pharmacy/warehouse_dashboard.html', context)


@login_required
@warehouse_required
def warehouse_add_product(request):
    if request.method == 'POST':
        form = QuickMedicineAddForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip().capitalize()
            category = form.cleaned_data['category']
            amount = form.cleaned_data['amount']
            raw_date = form.cleaned_data['date'].strip()
            price = form.cleaned_data['price']
            rx_req = form.cleaned_data['rx_required']

            exp_date = datetime.strptime(raw_date, "%d.%m.%Y").date()

            if not category:
                category = Category.objects.first()

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'created_by': request.user,
                    'category': category,
                    'price': price,
                    'stock_quantity': amount,
                    'expiry_date': exp_date,
                    'rx_required': rx_req,
                    'dosage_form': 'Таблетки',
                    'description': f'Препарат {name}.',
                    'instruction': 'Приймати за рекомендацією лікаря.',
                    'warning': 'Зберігати у недоступному для дітей місці.'
                }
            )

            if not created:
                product.stock_quantity += amount
                product.expiry_date = exp_date
                product.price = price
                product.save()

            messages.success(request, f"Препарат '{name}' успішно додано ({amount} шт. до {exp_date.strftime('%d.%m.%Y')})!")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)

    return redirect('pharmacy:warehouse_dashboard')


@login_required
@warehouse_required
def warehouse_edit_product(request):
    if request.method == 'POST':
        med_id = request.POST.get('medicine_id')
        name = request.POST.get('name', '').strip()
        amount_raw = request.POST.get('amount', '0')
        raw_date = request.POST.get('date', '').strip()
        price_raw = request.POST.get('price', '50')

        product = get_object_or_404(Product, id=med_id)

        try:
            amount = max(0, int(amount_raw))
        except ValueError:
            amount = product.stock_quantity

        try:
            price = Decimal(price_raw)
        except Exception:
            price = product.price

        try:
            exp_date = datetime.strptime(raw_date, "%d.%m.%Y").date()
        except Exception:
            exp_date = product.expiry_date

        product.name = name.capitalize()
        product.stock_quantity = amount
        product.price = price
        if exp_date:
            product.expiry_date = exp_date
        product.save()

        messages.success(request, f"Препарат '{product.name}' успішно оновлено!")
    return redirect('pharmacy:warehouse_dashboard')


@login_required
@warehouse_required
def warehouse_sell_product(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        qty_raw = request.POST.get('amount', '1')

        qty = _parse_positive_quantity(qty_raw)

        product = Product.objects.filter(name__iexact=name).first()
        if not product:
            messages.error(request, f"Препарат '{name}' не знайдено на складі.")
            return redirect('pharmacy:warehouse_dashboard')

        product, error = _sell_product(product_id=product.id, quantity=qty, user=request.user)
        if error == "insufficient_stock":
            messages.error(request, f"Недостатньо залишку! В наявності: {product.stock_quantity} шт.")
            return redirect('pharmacy:warehouse_dashboard')

        subtotal = product.price * qty
        messages.success(request, f"Продаж препарату '{product.name}' у кількості {qty} шт. виконано! До сплати: {subtotal:.2f} грн.")
    return redirect('pharmacy:warehouse_dashboard')


@login_required
@warehouse_required
def warehouse_return_product(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        qty_raw = request.POST.get('amount', '1')

        qty = _parse_positive_quantity(qty_raw)

        product = Product.objects.filter(name__iexact=name).first()
        if not product:
            messages.error(request, f"Препарат '{name}' не знайдено для повернення.")
            return redirect('pharmacy:warehouse_dashboard')

        product.stock_quantity += qty
        product.save()

        messages.success(request, f"Повернення препарату '{product.name}' (+{qty} шт.) успішно оформлено!")
    return redirect('pharmacy:warehouse_dashboard')


@login_required
@warehouse_required
def warehouse_delete_expired(request):
    if request.method == 'POST':
        today = timezone.now().date()
        expired = Product.objects.filter(expiry_date__lt=today, stock_quantity__gt=0)
        
        summary = expired.aggregate(count=Count('id'), total_items=Sum('stock_quantity'))
        expired.update(stock_quantity=0)
        count = summary['count']
        total_items = summary['total_items'] or 0

        messages.warning(request, f"Списано {count} прострочених найменувань (загалом {total_items} упаковок). Склад очищено!")
    return redirect('pharmacy:warehouse_dashboard')


@login_required
@warehouse_required
def warehouse_delete_product(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=pk)
        name = product.name
        product.delete()
        messages.info(request, f"Препарат '{name}' успішно видалено зі складу.")
    return redirect('pharmacy:warehouse_dashboard')
