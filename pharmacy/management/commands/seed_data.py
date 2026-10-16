import os
import json
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from pharmacy.models import Category, Product, Order, OrderItem

CATEGORIES_META = {
    "pain": {
        "name": "Знеболюючі",
        "icon": "bi-bandaid",
        "color": "#0068C2",
        "bg_color": "#E8F4FD",
        "description": "Препарати для зняття больового синдрому різної етіології"
    },
    "fever": {
        "name": "Жарознижуючі",
        "icon": "bi-thermometer-half",
        "color": "#856404",
        "bg_color": "#FFF3CD",
        "description": "Засоби для зниження температури тіла при гарячкових станах"
    },
    "antibiotic": {
        "name": "Антибіотики",
        "icon": "bi-capsule",
        "color": "#842029",
        "bg_color": "#F8D7DA",
        "description": "Протимікробні препарати широкого та специфічного спектру дії"
    },
    "cardio": {
        "name": "Кардіо",
        "icon": "bi-heart-pulse",
        "color": "#B02A37",
        "bg_color": "#FDE8E8",
        "description": "Лікарські засоби для підтримки серцево-судинної системи"
    },
    "gastro": {
        "name": "Шлунок",
        "icon": "bi-hospital",
        "color": "#155724",
        "bg_color": "#D4EDDA",
        "description": "Препарати для лікування та нормалізації роботи шлунково-кишкового тракту"
    },
    "vitamin": {
        "name": "Вітаміни",
        "icon": "bi-stars",
        "color": "#856404",
        "bg_color": "#FFF3CD",
        "description": "Вітамінні та мінеральні комплекси для зміцнення організму"
    },
    "antiviral": {
        "name": "Противірусні",
        "icon": "bi-shield-check",
        "color": "#432874",
        "bg_color": "#E2D9F3",
        "description": "Засоби для профілактики та терапії вірусних інфекцій"
    },
    "general": {
        "name": "Загальні препарати",
        "icon": "bi-box-seam",
        "color": "#0F172A",
        "bg_color": "#F1F5F9",
        "description": "Інші лікарські засоби та медичні товари"
    }
}


class Command(BaseCommand):
    help = "Імпортує дані у спрощену 4-табличну реляційну базу даних"

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        admin_user, _ = User.objects.get_or_create(username="admin")
        admin_user.set_password("123")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.first_name = "Головний"
        admin_user.last_name = "Адміністратор"
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("User 'admin' (password: 123, superuser) is ready."))

        pharm_user, _ = User.objects.get_or_create(username="pharm")
        pharm_user.set_password("qwerty")
        pharm_user.is_staff = True
        pharm_user.is_superuser = False
        pharm_user.first_name = "Черговий"
        pharm_user.last_name = "Фармацевт"
        pharm_user.save()
        self.stdout.write(self.style.SUCCESS("User 'pharm' (password: qwerty) is ready."))

        categories = {}
        for slug, meta in CATEGORIES_META.items():
            cat, _ = Category.objects.get_or_create(
                name=meta["name"],
                defaults={
                    "icon": meta["icon"],
                    "color": meta["color"],
                    "bg_color": meta["bg_color"],
                    "description": meta["description"],
                }
            )
            categories[slug] = cat
        self.stdout.write(self.style.SUCCESS(f"Categories ready: {len(categories)}."))

        base_src = r"c:\Users\Hugo\PycharmProjects\Zvit\src\storages"
        info_path = os.path.join(base_src, "medicines_info.json")
        meds_path = os.path.join(base_src, "medicines.json")
        hist_path = os.path.join(base_src, "sales_history.json")

        medicines_info = {}
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                medicines_info = json.load(f)

        medicines_stock = []
        if os.path.exists(meds_path):
            with open(meds_path, "r", encoding="utf-8") as f:
                medicines_stock = json.load(f)

        sales_history = []
        if os.path.exists(hist_path):
            with open(hist_path, "r", encoding="utf-8") as f:
                sales_history = json.load(f)

        med_objects = {}
        for name_key, info in medicines_info.items():
            display_name = name_key.strip().capitalize()
            cat_key = info.get("category", "general")
            cat_obj = categories.get(cat_key, categories["general"])
            rx_req = (info.get("rx", "").strip().lower() == "за рецептом")

            prod, _ = Product.objects.get_or_create(
                name=display_name,
                defaults={
                    "created_by": admin_user,
                    "category": cat_obj,
                    "rx_required": rx_req,
                    "price": Decimal("65.00"),
                    "stock_quantity": 50,
                    "expiry_date": timezone.now().date() + timezone.timedelta(days=730),
                    "dosage_form": "Таблетки",
                    "description": info.get("description", ""),
                    "instruction": info.get("instruction", ""),
                    "warning": info.get("warning", ""),
                }
            )
            med_objects[display_name.lower()] = prod

        for item in medicines_stock:
            raw_name = item.get("name", "").strip()
            if not raw_name:
                continue
            display_name = raw_name.capitalize()
            qty = int(item.get("amount", 0))
            raw_date = item.get("date", "01.01.2028")

            try:
                exp_date = datetime.strptime(raw_date, "%d.%m.%Y").date()
            except Exception:
                exp_date = timezone.now().date() + timezone.timedelta(days=365)

            prod = med_objects.get(raw_name.lower())
            if not prod:
                prod, _ = Product.objects.get_or_create(
                    name=display_name,
                    defaults={
                        "created_by": admin_user,
                        "category": categories["general"],
                        "rx_required": False,
                        "price": Decimal("45.00"),
                        "stock_quantity": qty,
                        "expiry_date": exp_date,
                        "dosage_form": "Таблетки",
                    }
                )
                med_objects[display_name.lower()] = prod
            else:
                prod.stock_quantity = qty
                prod.expiry_date = exp_date
                prod.save()

        self.stdout.write(self.style.SUCCESS(f"Products ready: {len(med_objects)}."))

        for i, h_item in enumerate(sales_history, start=1):
            med_name = h_item.get("name", "").strip().capitalize()
            qty = int(h_item.get("amount", 1))
            sold_at_raw = h_item.get("sold_at", "")

            try:
                sold_at_dt = timezone.make_aware(datetime.strptime(sold_at_raw, "%d.%m.%Y %H:%M:%S"))
            except Exception:
                sold_at_dt = timezone.now()

            prod = med_objects.get(med_name.lower())
            if not prod:
                prod, _ = Product.objects.get_or_create(
                    name=med_name,
                    defaults={
                        "created_by": admin_user,
                        "category": categories["general"],
                        "price": Decimal("50.00"),
                        "stock_quantity": 20,
                        "expiry_date": timezone.now().date() + timezone.timedelta(days=365),
                    }
                )
                med_objects[med_name.lower()] = prod

            subtotal = prod.price * qty

            order = Order.objects.create(
                created_by=pharm_user,
                total_amount=subtotal,
                status="COMPLETED",
                stock_deducted=True,
                created_at=sold_at_dt
            )

            OrderItem.objects.create(
                order=order,
                product=prod,
                quantity=qty,
                unit_price=prod.price
            )

        self.stdout.write(self.style.SUCCESS(f"Orders ready: {len(sales_history)}."))
        self.stdout.write(self.style.SUCCESS("All data successfully migrated!"))
