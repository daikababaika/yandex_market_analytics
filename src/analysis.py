import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

#настраиваем графики
plt.rcParams.update({
    "figure.figsize": (12, 6),
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})
sns.set_style("whitegrid")

YA_YELLOW = "#FFCC00"
YA_BLACK = "#1A1A1A"
YA_RED = "#FF3333"
PALETTE = ["#FFCC00", "#FF3333", "#4CAF50", "#5B5EA6", "#FF9800", "#00BCD4", "#E91E63", "#607D8B", "#1A1A1A", "#8BC34A"]


def load_data():
    """Загрузка и первичная обработка данных."""
    orders = pd.read_csv("data/orders.csv", parse_dates=["order_date"])
    customers = pd.read_csv("data/customers.csv", parse_dates=["registration_date"])

    orders["month"] = orders["order_date"].dt.to_period("M")
    orders["year_month"] = orders["order_date"].dt.strftime("%Y-%m")

    delivered = orders[orders["status"] == "Доставлен"].copy()

    return orders, customers, delivered

def eda_summary(orders: pd.DataFrame, delivered: pd.DataFrame, customers: pd.DataFrame):
    """Exploratory Data Analysis: основные метрики."""
    print("=" * 65)
    print("  EXPLORATORY DATA ANALYSIS — ЯНДЕКС МАРКЕТ")
    print("=" * 65)

    total_revenue = delivered["total_amount"].sum()
    avg_check = delivered["total_amount"].mean()
    median_check = delivered["total_amount"].median()
    total_orders = len(orders)
    delivery_rate = len(delivered) / total_orders * 100
    return_rate = len(orders[orders["status"] == "Возврат"]) / total_orders * 100
    cancel_rate = len(orders[orders["status"] == "Отменён"]) / total_orders * 100
    unique_customers = orders["customer_id"].nunique()
    plus_customers = customers["yandex_plus"].sum()
    plus_pct = plus_customers / len(customers) * 100
    avg_rating = delivered["rating"].dropna().mean()

    print(f"\n{'Метрика':<40} {'Значение':>20}")
    print("-" * 62)
    print(f"{'Всего заказов':<40} {total_orders:>20,}")
    print(f"{'Уникальных покупателей':<40} {unique_customers:>20,}")
    print(f"{'Подписчиков Яндекс Плюс':<40} {plus_customers:>14,.0f} ({plus_pct:.0f}%)")
    print(f"{'Общая выручка':<40} {total_revenue:>17,.0f} ₽")
    print(f"{'Средний чек':<40} {avg_check:>17,.0f} ₽")
    print(f"{'Медианный чек':<40} {median_check:>17,.0f} ₽")
    print(f"{'Средний рейтинг':<40} {avg_rating:>20.2f}")
    print(f"{'Доставлено':<40} {delivery_rate:>19.1f}%")
    print(f"{'Возвраты':<40} {return_rate:>19.1f}%")
    print(f"{'Отмены':<40} {cancel_rate:>19.1f}%")


def plot_monthly_revenue(delivered: pd.DataFrame):
    monthly = delivered.groupby("year_month")["total_amount"].sum().reset_index()
    monthly.columns = ["month", "revenue"]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(monthly["month"], monthly["revenue"], color=YA_YELLOW, alpha=0.9,
           edgecolor=YA_BLACK, linewidth=0.5)

    z = np.polyfit(range(len(monthly)), monthly["revenue"], 2)
    p = np.poly1d(z)
    ax.plot(monthly["month"], p(range(len(monthly))), color=YA_RED,
            linewidth=2.5, linestyle="--", label="Тренд")

    ax.set_title("Ежемесячная выручка Яндекс Маркет", fontweight="bold", pad=15)
    ax.set_ylabel("Выручка, ₽")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("visuals/01_monthly_revenue.png")
    plt.close()
    print("[✓] visuals/01_monthly_revenue.png")


def plot_category_analysis(delivered: pd.DataFrame):
    cat_stats = delivered.groupby("category").agg(
        revenue=("total_amount", "sum"),
        orders=("order_id", "count"),
        avg_check=("total_amount", "mean"),
    ).sort_values("revenue", ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    axes[0].barh(cat_stats.index, cat_stats["revenue"], color=YA_YELLOW,
                 edgecolor=YA_BLACK, linewidth=0.5, alpha=0.9)
    axes[0].set_title("Выручка по категориям", fontweight="bold")
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M ₽"))

    axes[1].barh(cat_stats.index, cat_stats["avg_check"], color=PALETTE[2],
                 edgecolor=YA_BLACK, linewidth=0.5, alpha=0.85)
    axes[1].set_title("Средний чек по категориям", fontweight="bold")
    axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} ₽"))

    plt.tight_layout()
    plt.savefig("visuals/02_category_analysis.png")
    plt.close()
    print("[✓] visuals/02_category_analysis.png")


def plot_orders_by_status(orders: pd.DataFrame):
    status_counts = orders["status"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = [PALETTE[2], YA_RED, PALETTE[7]]
    ax.pie(status_counts, labels=status_counts.index, autopct="%1.1f%%",
           colors=colors, startangle=90, textprops={"fontsize": 12})
    ax.set_title("Распределение статусов заказов", fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("visuals/03_order_status.png")
    plt.close()
    print("[✓] visuals/03_order_status.png")


def plot_city_top(delivered: pd.DataFrame, top_n: int = 10):
    city_revenue = delivered.groupby("city")["total_amount"].sum().nlargest(top_n).sort_values()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(city_revenue.index, city_revenue.values, color=YA_YELLOW,
            edgecolor=YA_BLACK, linewidth=0.5, alpha=0.9)
    ax.set_title(f"Топ-{top_n} городов по выручке", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M ₽"))
    plt.tight_layout()
    plt.savefig("visuals/04_top_cities.png")
    plt.close()
    print("[✓] visuals/04_top_cities.png")
    
def yandex_plus_analysis(delivered: pd.DataFrame):
    print("\n" + "=" * 65)
    print("  АНАЛИЗ ЯНДЕКС ПЛЮС")
    print("=" * 65)

    plus_stats = delivered.groupby("yandex_plus").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
        avg_check=("total_amount", "mean"),
        avg_discount=("discount_pct", "mean"),
        customers=("customer_id", "nunique"),
    )
    plus_stats["orders_per_customer"] = plus_stats["orders"] / plus_stats["customers"]
    plus_stats["revenue_per_customer"] = plus_stats["revenue"] / plus_stats["customers"]
    plus_stats.index = ["Без Плюса", "Яндекс Плюс"]

    print(f"\n{'Метрика':<30} {'Без Плюса':>15} {'Яндекс Плюс':>15}")
    print("-" * 62)
    for col, label, fmt in [
        ("customers", "Покупателей", "{:,.0f}"),
        ("orders", "Заказов", "{:,.0f}"),
        ("orders_per_customer", "Заказов на клиента", "{:.1f}"),
        ("avg_check", "Средний чек, ₽", "{:,.0f}"),
        ("avg_discount", "Ср. скидка, %", "{:.1f}"),
        ("revenue_per_customer", "Выручка на клиента, ₽", "{:,.0f}"),
    ]:
        v1 = fmt.format(plus_stats.loc["Без Плюса", col])
        v2 = fmt.format(plus_stats.loc["Яндекс Плюс", col])
        print(f"{label:<30} {v1:>15} {v2:>15}")

    # Визуализация
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    labels = ["Без Плюса", "Яндекс Плюс"]
    colors_pair = [PALETTE[7], YA_YELLOW]

    # Средний чек
    vals = [plus_stats.loc[l, "avg_check"] for l in labels]
    axes[0].bar(labels, vals, color=colors_pair, edgecolor=YA_BLACK, linewidth=0.5)
    axes[0].set_title("Средний чек", fontweight="bold")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} ₽"))

    # Заказов на клиента
    vals = [plus_stats.loc[l, "orders_per_customer"] for l in labels]
    axes[1].bar(labels, vals, color=colors_pair, edgecolor=YA_BLACK, linewidth=0.5)
    axes[1].set_title("Заказов на клиента", fontweight="bold")

    # Выручка на клиента
    vals = [plus_stats.loc[l, "revenue_per_customer"] for l in labels]
    axes[2].bar(labels, vals, color=colors_pair, edgecolor=YA_BLACK, linewidth=0.5)
    axes[2].set_title("Выручка на клиента", fontweight="bold")
    axes[2].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} ₽"))

    plt.suptitle("Яндекс Плюс vs Обычные покупатели", fontweight="bold", fontsize=15, y=1.02)
    plt.tight_layout()
    plt.savefig("visuals/05_yandex_plus.png")
    plt.close()
    print("\n[✓] visuals/05_yandex_plus.png")

def delivery_payment_analysis(delivered: pd.DataFrame):
    print("\n" + "=" * 65)
    print("  АНАЛИЗ ДОСТАВКИ И ОПЛАТЫ")
    print("=" * 65)

    # Доставка
    del_stats = delivered.groupby("delivery_type").agg(
        orders=("order_id", "count"),
        avg_check=("total_amount", "mean"),
    ).sort_values("orders", ascending=False)
    del_stats["share_pct"] = del_stats["orders"] / del_stats["orders"].sum() * 100

    print(f"\n{'Способ доставки':<25} {'Заказов':>10} {'Доля':>8} {'Ср. чек':>12}")
    print("-" * 57)
    for idx, row in del_stats.iterrows():
        print(f"{idx:<25} {row['orders']:>10,.0f} {row['share_pct']:>7.1f}% {row['avg_check']:>9,.0f} ₽")

    # Оплата
    pay_stats = delivered.groupby("payment_method").agg(
        orders=("order_id", "count"),
        avg_check=("total_amount", "mean"),
    ).sort_values("orders", ascending=False)
    pay_stats["share_pct"] = pay_stats["orders"] / pay_stats["orders"].sum() * 100

    print(f"\n{'Способ оплаты':<25} {'Заказов':>10} {'Доля':>8} {'Ср. чек':>12}")
    print("-" * 57)
    for idx, row in pay_stats.iterrows():
        print(f"{idx:<25} {row['orders']:>10,.0f} {row['share_pct']:>7.1f}% {row['avg_check']:>9,.0f} ₽")

    # Визуализация
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    axes[0].barh(del_stats.index, del_stats["orders"], color=YA_YELLOW,
                 edgecolor=YA_BLACK, linewidth=0.5, alpha=0.9)
    axes[0].set_title("Заказы по способу доставки", fontweight="bold")

    axes[1].barh(pay_stats.index, pay_stats["orders"], color=PALETTE[3],
                 edgecolor=YA_BLACK, linewidth=0.5, alpha=0.85)
    axes[1].set_title("Заказы по способу оплаты", fontweight="bold")

    plt.tight_layout()
    plt.savefig("visuals/06_delivery_payment.png")
    plt.close()
    print("\n[✓] visuals/06_delivery_payment.png")

def rfm_analysis(delivered: pd.DataFrame) -> pd.DataFrame: 
    print("\n" + "=" * 65)
    print("  RFM-СЕГМЕНТАЦИЯ")
    print("=" * 65)

    snapshot_date = delivered["order_date"].max() + pd.Timedelta(days=1)

    rfm = delivered.groupby("customer_id").agg(
        recency=("order_date", lambda x: (snapshot_date - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("total_amount", "sum"),
    ).reset_index()

    rfm["R_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["RFM_score"] = rfm["R_score"] * 100 + rfm["F_score"] * 10 + rfm["M_score"]

    def assign_segment(row):
        r, f, m = row["R_score"], row["F_score"], row["M_score"]
        if r >= 3 and f >= 3 and m >= 3:
            return "Чемпионы"
        elif r >= 3 and f >= 2:
            return "Лояльные"
        elif r >= 3 and f == 1:
            return "Новички"
        elif r == 2 and f >= 2:
            return "Перспективные"
        elif r == 2 and f == 1:
            return "Нуждаются во внимании"
        elif r == 1 and f >= 3:
            return "Уходящие VIP"
        elif r == 1 and f >= 2:
            return "В зоне риска"
        else:
            return "Спящие"

    rfm["segment"] = rfm.apply(assign_segment, axis=1)

    segment_stats = rfm.groupby("segment").agg(
        customers=("customer_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
    ).sort_values("avg_monetary", ascending=False)

    print(f"\n{'Сегмент':<25} {'Кол-во':>8} {'Ср. дней':>10} {'Ср. заказов':>12} {'Ср. выручка':>14}")
    print("-" * 72)
    for seg, row in segment_stats.iterrows():
        print(f"{seg:<25} {row['customers']:>8.0f} {row['avg_recency']:>10.0f}"
              f" {row['avg_frequency']:>12.1f} {row['avg_monetary']:>11,.0f} ₽")

    return rfm


def plot_rfm(rfm: pd.DataFrame):
    segment_counts = rfm["segment"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    colors = sns.color_palette("Set2", len(segment_counts))
    axes[0].pie(segment_counts, labels=segment_counts.index, autopct="%1.1f%%",
                colors=colors, startangle=90, textprops={"fontsize": 10})
    axes[0].set_title("Распределение RFM-сегментов", fontweight="bold")

    scatter_colors = {
        "Чемпионы": PALETTE[2], "Лояльные": PALETTE[3], "Новички": PALETTE[5],
        "Перспективные": PALETTE[4], "Нуждаются во внимании": PALETTE[6],
        "Уходящие VIP": YA_RED, "В зоне риска": PALETTE[7], "Спящие": "#CCCCCC",
    }
    for seg in rfm["segment"].unique():
        mask = rfm["segment"] == seg
        axes[1].scatter(rfm.loc[mask, "recency"], rfm.loc[mask, "monetary"],
                        label=seg, alpha=0.5, s=20, color=scatter_colors.get(seg, "gray"))

    axes[1].set_title("Recency vs Monetary по сегментам", fontweight="bold")
    axes[1].set_xlabel("Recency (дней)")
    axes[1].set_ylabel("Monetary (₽)")
    axes[1].legend(fontsize=8, loc="upper right")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e3:.0f}K"))

    plt.tight_layout()
    plt.savefig("visuals/07_rfm_segments.png")
    plt.close()
    print("[✓] visuals/07_rfm_segments.png")

def cohort_analysis(delivered: pd.DataFrame):
    print("\n" + "=" * 65)
    print("  КОГОРТНЫЙ АНАЛИЗ")
    print("=" * 65)

    df = delivered.copy()
    df["order_month"] = df["order_date"].dt.to_period("M")

    cohort_map = df.groupby("customer_id")["order_month"].min().rename("cohort")
    df = df.merge(cohort_map, on="customer_id")
    df["period"] = (df["order_month"] - df["cohort"]).apply(lambda x: x.n)

    cohort_table = df.groupby(["cohort", "period"])["customer_id"].nunique().reset_index()
    cohort_pivot = cohort_table.pivot(index="cohort", columns="period", values="customer_id")

    cohort_sizes = cohort_pivot[0]
    retention = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    retention_display = retention.iloc[:12, :12]

    print(f"\nRetention Rate (первые 12 когорт, %):\n")
    print(retention_display.round(1).to_string())

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(retention_display, annot=True, fmt=".0f", cmap="YlOrRd",
                linewidths=0.5, ax=ax, vmin=0, vmax=100,
                cbar_kws={"label": "Retention %"})
    ax.set_title("Когортный анализ: Retention Rate (%)", fontweight="bold", pad=15)
    ax.set_xlabel("Месяц после первой покупки")
    ax.set_ylabel("Когорта (месяц первой покупки)")
    ax.set_yticklabels([str(x) for x in retention_display.index], rotation=0)

    plt.tight_layout()
    plt.savefig("visuals/08_cohort_retention.png")
    plt.close()
    print("\n[✓] visuals/08_cohort_retention.png")

    return retention

def demand_forecast(delivered: pd.DataFrame):
    print("\n" + "=" * 65)
    print("  ПРОГНОЗ СПРОСА")
    print("=" * 65)

    daily = delivered.groupby("order_date").agg(
        orders=("order_id", "count"),
        revenue=("total_amount", "sum"),
    ).reset_index().sort_values("order_date")
    daily.set_index("order_date", inplace=True)

    weekly = daily.resample("W").sum()
    weekly["MA_4w"] = weekly["orders"].rolling(window=4).mean()
    weekly["MA_8w"] = weekly["orders"].rolling(window=8).mean()
    weekly["EWM"] = weekly["orders"].ewm(span=6, adjust=False).mean()

    last_8 = weekly["EWM"].dropna().tail(8)
    trend = np.polyfit(range(len(last_8)), last_8.values, 1)

    forecast_dates = pd.date_range(weekly.index[-1] + pd.Timedelta(weeks=1), periods=8, freq="W")
    forecast_values = [trend[0] * (len(last_8) + i) + trend[1] for i in range(8)]
    forecast = pd.DataFrame({"orders_forecast": forecast_values}, index=forecast_dates)

    print(f"\nПрогноз заказов на ближайшие 8 недель:")
    print(f"{'Неделя':<15} {'Прогноз заказов':>18}")
    print("-" * 35)
    for date, row in forecast.iterrows():
        print(f"{date.strftime('%Y-%m-%d'):<15} {row['orders_forecast']:>18.0f}")

    fig, ax = plt.subplots(figsize=(16, 7))
    ax.plot(weekly.index, weekly["orders"], alpha=0.4, color="gray", label="Факт (недельный)")
    ax.plot(weekly.index, weekly["MA_4w"], color=YA_YELLOW, linewidth=2.5, label="MA 4 недели")
    ax.plot(weekly.index, weekly["MA_8w"], color=PALETTE[2], linewidth=2, label="MA 8 недель")
    ax.plot(weekly.index, weekly["EWM"], color=PALETTE[3], linewidth=2, label="EWM (span=6)")

    ax.plot(forecast.index, forecast["orders_forecast"], color=YA_RED,
            linewidth=2.5, linestyle="--", marker="o", markersize=5, label="Прогноз")
    ax.axvline(weekly.index[-1], color="gray", linestyle=":", alpha=0.7)
    ax.fill_between(forecast.index,
                    [v * 0.85 for v in forecast_values],
                    [v * 1.15 for v in forecast_values],
                    alpha=0.15, color=YA_RED, label="Доверительный интервал (±15%)")

    ax.set_title("Прогноз спроса: заказы по неделям", fontweight="bold", pad=15)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Количество заказов")
    ax.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig("visuals/09_demand_forecast.png")
    plt.close()
    print("\n[✓] visuals/09_demand_forecast.png")

    return forecast

#дополнительные графики
def plot_discount_impact(delivered: pd.DataFrame): 
    discount_stats = delivered.groupby("discount_pct").agg(
        orders=("order_id", "count"),
        avg_check=("total_amount", "mean"),
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(discount_stats["discount_pct"].astype(str), discount_stats["orders"],
            color=YA_YELLOW, alpha=0.85, edgecolor=YA_BLACK, linewidth=0.5, label="Заказов")
    ax1.set_ylabel("Количество заказов", color=YA_BLACK)
    ax1.set_xlabel("Размер скидки (%)")

    ax2 = ax1.twinx()
    ax2.plot(discount_stats["discount_pct"].astype(str), discount_stats["avg_check"],
             color=YA_RED, marker="o", linewidth=2.5, label="Средний чек")
    ax2.set_ylabel("Средний чек, ₽", color=YA_RED)

    ax1.set_title("Влияние скидок на заказы и средний чек", fontweight="bold", pad=15)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    plt.savefig("visuals/10_discount_impact.png")
    plt.close()
    print("[✓] visuals/10_discount_impact.png")


def plot_rating_analysis(delivered: pd.DataFrame):
    rated = delivered.dropna(subset=["rating"])

    cat_rating = rated.groupby("category")["rating"].agg(["mean", "count"]).sort_values("mean")

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(cat_rating.index, cat_rating["mean"], color=YA_YELLOW,
                   edgecolor=YA_BLACK, linewidth=0.5, alpha=0.9)
    ax.set_xlim(3.5, 5.0)
    ax.set_title("Средний рейтинг по категориям", fontweight="bold")
    ax.set_xlabel("Средний рейтинг")

    for bar, count in zip(bars, cat_rating["count"]):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                f"n={count}", va="center", fontsize=9, color=PALETTE[7])

    plt.tight_layout()
    plt.savefig("visuals/11_ratings.png")
    plt.close()
    print("[✓] visuals/11_ratings.png")
    

def main():
    orders, customers, delivered = load_data()

    # EDA
    eda_summary(orders, delivered, customers)
    plot_monthly_revenue(delivered)
    plot_category_analysis(delivered)
    plot_orders_by_status(orders)
    plot_city_top(delivered)
    plot_discount_impact(delivered)
    plot_rating_analysis(delivered)

    # Яндекс Плюс
    yandex_plus_analysis(delivered)

    # Доставка и оплата
    delivery_payment_analysis(delivered)

    # RFM
    rfm = rfm_analysis(delivered)
    plot_rfm(rfm)

    # Когортный анализ
    retention = cohort_analysis(delivered)

    # Прогноз спроса
    forecast = demand_forecast(delivered)

    # Сохранение
    rfm.to_csv("data/rfm_segments.csv", index=False, encoding="utf-8-sig")
    print("\n[✓] data/rfm_segments.csv")
    print(" АНАЛИЗ ЗАВЕРШЁН")


if __name__ == "__main__":
    main()
