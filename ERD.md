# ERD — система управління фармацевтичним складом PharmManager

Діаграма відображає складський облік і роздрібні продажі аптеки. Покупця як облікову сутність система не веде. Сутність `AUTH_USER` — працівник аптеки, який увійшов у систему та зафіксував продаж. Системні таблиці сесій, дозволів і журналу адміністратора не показані.

```mermaid
erDiagram
    AUTH_USER ||--o{ SALE : records
    INVENTORY_CATEGORY ||--o{ INVENTORY_PRODUCT : contains
    SALE ||--o{ SALE_ITEM : contains
    INVENTORY_PRODUCT ||--o{ SALE_ITEM : sold_as

    AUTH_USER {
        int id PK
        string username UK
        string first_name
        string last_name
        string email
        string password
        boolean is_active
        boolean is_staff
        boolean is_superuser
    }

    INVENTORY_CATEGORY {
        int id PK
        string name UK
        text description
        string icon
        string color
        string bg_color
    }

    INVENTORY_PRODUCT {
        int id PK
        int category_id FK
        string name UK
        text description
        text instruction
        text warning
        decimal price
        int stock_quantity
        date expiry_date
        boolean rx_required
        string dosage_form
        datetime created_at
    }

    SALE {
        int id PK
        int created_by_id FK "pharmacy employee"
        datetime created_at
        string status
        decimal total_amount
        boolean stock_deducted
    }

    SALE_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
    }
```

## Зв’язки та правила видалення

- Один працівник може зафіксувати багато продажів; кожен продаж належить одному працівнику. У коді це поле `Order.created_by`, а у фізичній схемі — `inventory_order.created_by_id`.
- Одна категорія містить багато товарів; видалення категорії каскадно видаляє її товари.
- Один продаж містить позиції продажу, кожна з яких посилається на один товар. У Django-коді вони називаються `Order` і `OrderItem`, а фізичні таблиці — `inventory_order` та `inventory_orderitem`; у предметній області це продаж і його рядки, не клієнтське замовлення.
- Видалення продажу або товару каскадно видаляє пов’язані позиції.
- `unit_price` зберігає ціну товару на момент продажу; `total_amount` зберігає суму продажу.

## Уточнення щодо ролі фармацевта

У поточних моделях немає окремої сутності чи поля ролі «фармацевт»: `created_by` посилається на стандартного Django-користувача. Представлення продажу перевіряє, що користувач увійшов (`login_required`), але не обмежує дію окремою роллю фармацевта. Отже, ERD точно показує наявну структуру даних; обмеження продажу лише фармацевтам потребує окремої рольової перевірки в коді.
