"""
Генерация синтетического датасета продаж Яндекс Маркета.
Данные имитируют реальные паттерны: сезонность, возвраты,
повторные покупки, Яндекс Плюс, способы доставки.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(2024)

# --- Параметры ---
N_CUSTOMERS = 2500
N_ORDERS = 18000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

# --- Категории Яндекс Маркета ---
CATEGORIES = {
    "Электроника и гаджеты": {"price_range": (2000, 120000), "weight": 0.18},
    "Бытовая техника": {"price_range": (1500, 90000), "weight": 0.14},
    "Одежда и обувь": {"price_range": (500, 20000), "weight": 0.15},
    "Дом и дача": {"price_range": (300, 35000), "weight": 0.12},
    "Красота и гигиена": {"price_range": (150, 10000), "weight": 0.10},
    "Детские товары": {"price_range": (300, 15000), "weight": 0.08},
    "Продукты и напитки": {"price_range": (100, 6000), "weight": 0.07},
    "Спорт и туризм": {"price_range": (400, 40000), "weight": 0.06},
    "Авто и мото": {"price_range": (200, 50000), "weight": 0.05},
    "Книги и канцелярия": {"price_range": (100, 4000), "weight": 0.05},
}

CITIES = [
    ("Москва", 0.28), ("Санкт-Петербург", 0.13), ("Новосибирск", 0.05),
    ("Екатеринбург", 0.05), ("Казань", 0.05), ("Нижний Новгород", 0.04),
    ("Краснодар", 0.04), ("Самара", 0.03), ("Ростов-на-Дону", 0.04),
    ("Воронеж", 0.03), ("Пермь", 0.02), ("Красноярск", 0.02),
    ("Челябинск", 0.02), ("Уфа", 0.02), ("Тюмень", 0.02),
    ("Другие", 0.16),
]

DELIVERY_TYPES = ["Курьер Яндекс", "Пункт выдачи", "Почта России", "Экспресс-доставка"]
DELIVERY_WEIGHTS = [0.35, 0.40, 0.10, 0.15]

PAYMENT_METHODS = ["Картой онлайн", "СБП", "При получении", "Яндекс Пэй", "В кредит"]
PAYMENT_WEIGHTS = [0.38, 0.18, 0.15, 0.22, 0.07]

STATUSES = ["Доставлен", "Возврат", "Отменён"]
STATUS_WEIGHTS = [0.83, 0.09, 0.08]


def generate_customers(n: int) -> pd.DataFrame:
    """Генерация базы покупателей с учётом подписки Яндекс Плюс."""
    cities, city_weights = zip(*CITIES)

    customers = pd.DataFrame({
        "customer_id": [f"YM{str(i).zfill(6)}" for i in range(1, n + 1)],
        "city": np.random.choice(cities, size=n, p=city_weights),
        "registration_date": [
            START_DATE + timedelta(days=int(np.random.exponential(scale=220)))
            for _ in range(n)
        ],
        "age_group": np.random.choice(
            ["18-24", "25-34", "35-44", "45-54", "55+"],
            size=n, p=[0.18, 0.33, 0.24, 0.15, 0.10]
        ),
        "gender": np.random.choice(["М", "Ж"], size=n, p=[0.45, 0.55]),
        "yandex_plus": np.random.choice([True, False], size=n, p=[0.42, 0.58]),
    })

    customers["registration_date"] = customers["registration_date"].clip(upper=END_DATE)
    return customers


def seasonal_multiplier(date: datetime) -> float:
    """Сезонный коэффициент: пики в ноябре-декабре и марте (8 марта)."""
    month = date.month
    multipliers = {
        1: 0.85, 2: 0.80, 3: 1.05, 4: 0.90, 5: 0.95,
        6: 0.85, 7: 0.80, 8: 0.90, 9: 1.00, 10: 1.05,
        11: 1.45, 12: 1.55,
    }
    return multipliers.get(month, 1.0)


def generate_orders(n: int, customers: pd.DataFrame) -> pd.DataFrame:
    """Генерация заказов с учётом сезонности, Плюса и способов доставки."""
    categories = list(CATEGORIES.keys())
    cat_weights = [CATEGORIES[c]["weight"] for c in categories]

    orders = []
    for _ in range(n):
        customer = customers.sample(1).iloc[0]

        days_range = (END_DATE - customer["registration_date"]).days
        if days_range <= 0:
            days_range = 1

        attempts = 0
        while attempts < 10:
            order_date = customer["registration_date"] + timedelta(
                days=np.random.randint(0, days_range)
            )
            if np.random.random() < seasonal_multiplier(order_date) / 1.55:
                break
            attempts += 1

        category = np.random.choice(categories, p=cat_weights)
        price_min, price_max = CATEGORIES[category]["price_range"]
        base_price = np.random.lognormal(
            mean=np.log((price_min + price_max) / 4), sigma=0.6
        )
        price = np.clip(base_price, price_min, price_max)

        quantity = np.random.choice([1, 2, 3, 4, 5], p=[0.58, 0.24, 0.10, 0.05, 0.03])

        # Подписчики Плюс чаще получают кешбэк-скидки
        if customer["yandex_plus"]:
            discount = np.random.choice([0, 5, 10, 15, 20, 25, 30],
                                        p=[0.20, 0.15, 0.20, 0.18, 0.12, 0.10, 0.05])
        else:
            discount = np.random.choice([0, 5, 10, 15, 20, 25, 30],
                                        p=[0.45, 0.15, 0.18, 0.10, 0.07, 0.03, 0.02])

        status = np.random.choice(STATUSES, p=STATUS_WEIGHTS)
        delivery = np.random.choice(DELIVERY_TYPES, p=DELIVERY_WEIGHTS)
        payment = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)

        total = round(price * quantity * (1 - discount / 100), 2)

        # Рейтинг (только для доставленных)
        rating = None
        if status == "Доставлен" and np.random.random() < 0.35:
            rating = np.random.choice([1, 2, 3, 4, 5], p=[0.03, 0.05, 0.12, 0.30, 0.50])

        orders.append({
            "order_id": f"YMO{str(len(orders) + 1).zfill(7)}",
            "customer_id": customer["customer_id"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "category": category,
            "price": round(price, 2),
            "quantity": quantity,
            "discount_pct": discount,
            "total_amount": total,
            "status": status,
            "delivery_type": delivery,
            "payment_method": payment,
            "city": customer["city"],
            "yandex_plus": customer["yandex_plus"],
            "rating": rating,
        })

    return pd.DataFrame(orders)


def main():
    print("Генерация покупателей...")
    customers = generate_customers(N_CUSTOMERS)

    print("Генерация заказов...")
    orders = generate_orders(N_ORDERS, customers)

    customers.to_csv("data/customers.csv", index=False, encoding="utf-8-sig")
    orders.to_csv("data/orders.csv", index=False, encoding="utf-8-sig")

    plus_share = customers["yandex_plus"].mean() * 100
    print(f"\nГотово!")
    print(f"  Покупателей: {len(customers)} (Яндекс Плюс: {plus_share:.0f}%)")
    print(f"  Заказов: {len(orders)}")
    print(f"  Период: {orders['order_date'].min()} — {orders['order_date'].max()}")
    print(f"  Общая выручка: {orders[orders['status'] == 'Доставлен']['total_amount'].sum():,.0f} ₽")


if __name__ == "__main__":
    main()
