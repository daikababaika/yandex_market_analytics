-- ============================================================
-- SQL-запросы для анализа продаж Яндекс Маркета
-- PostgreSQL / SQLite / MySQL
-- ============================================================

-- 1. Общая статистика
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    ROUND(SUM(CASE WHEN status = 'Доставлен' THEN total_amount ELSE 0 END), 2) AS total_revenue,
    ROUND(AVG(CASE WHEN status = 'Доставлен' THEN total_amount END), 2) AS avg_check,
    ROUND(AVG(CASE WHEN status = 'Доставлен' THEN rating END), 2) AS avg_rating
FROM orders;


-- 2. Ежемесячная выручка
SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(*) AS orders_count,
    ROUND(SUM(total_amount), 2) AS revenue
FROM orders
WHERE status = 'Доставлен'
GROUP BY month
ORDER BY month;


-- 3. Топ-10 городов по выручке
SELECT
    city,
    COUNT(*) AS orders_count,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(AVG(total_amount), 2) AS avg_check
FROM orders
WHERE status = 'Доставлен'
GROUP BY city
ORDER BY revenue DESC
LIMIT 10;


-- 4. Анализ категорий
SELECT
    category,
    COUNT(*) AS orders_count,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(AVG(total_amount), 2) AS avg_check,
    ROUND(AVG(rating), 2) AS avg_rating,
    ROUND(100.0 * SUM(CASE WHEN status = 'Возврат' THEN 1 ELSE 0 END) / COUNT(*), 1) AS return_rate_pct
FROM orders
GROUP BY category
ORDER BY revenue DESC;


-- 5. Сравнение Яндекс Плюс vs обычные покупатели
SELECT
    CASE WHEN yandex_plus = 'True' THEN 'Яндекс Плюс' ELSE 'Без Плюса' END AS subscriber,
    COUNT(DISTINCT customer_id) AS customers,
    COUNT(*) AS orders_count,
    ROUND(AVG(total_amount), 2) AS avg_check,
    ROUND(AVG(discount_pct), 1) AS avg_discount,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM orders
WHERE status = 'Доставлен'
GROUP BY yandex_plus;


-- 6. Анализ способов доставки
SELECT
    delivery_type,
    COUNT(*) AS orders_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders WHERE status = 'Доставлен'), 1) AS share_pct,
    ROUND(AVG(total_amount), 2) AS avg_check
FROM orders
WHERE status = 'Доставлен'
GROUP BY delivery_type
ORDER BY orders_count DESC;


-- 7. Анализ способов оплаты
SELECT
    payment_method,
    COUNT(*) AS orders_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders WHERE status = 'Доставлен'), 1) AS share_pct,
    ROUND(AVG(total_amount), 2) AS avg_check
FROM orders
WHERE status = 'Доставлен'
GROUP BY payment_method
ORDER BY orders_count DESC;


-- 8. RFM-метрики
SELECT
    customer_id,
    julianday('2025-01-01') - julianday(MAX(order_date)) AS recency_days,
    COUNT(DISTINCT order_id) AS frequency,
    ROUND(SUM(total_amount), 2) AS monetary
FROM orders
WHERE status = 'Доставлен'
GROUP BY customer_id
ORDER BY monetary DESC;


-- 9. Когорты
WITH cohorts AS (
    SELECT
        customer_id,
        MIN(strftime('%Y-%m', order_date)) AS cohort
    FROM orders
    WHERE status = 'Доставлен'
    GROUP BY customer_id
),
activity AS (
    SELECT
        o.customer_id,
        c.cohort,
        strftime('%Y-%m', o.order_date) AS active_month,
        (CAST(strftime('%Y', o.order_date) AS INT) - CAST(substr(c.cohort, 1, 4) AS INT)) * 12 +
        (CAST(strftime('%m', o.order_date) AS INT) - CAST(substr(c.cohort, 6, 2) AS INT)) AS period
    FROM orders o
    JOIN cohorts c ON o.customer_id = c.customer_id
    WHERE o.status = 'Доставлен'
)
SELECT
    cohort,
    period,
    COUNT(DISTINCT customer_id) AS active_customers
FROM activity
GROUP BY cohort, period
ORDER BY cohort, period;


-- 10. Рейтинги по категориям и способам доставки
SELECT
    category,
    delivery_type,
    COUNT(*) AS rated_orders,
    ROUND(AVG(rating), 2) AS avg_rating
FROM orders
WHERE status = 'Доставлен' AND rating IS NOT NULL
GROUP BY category, delivery_type
ORDER BY category, avg_rating DESC;
