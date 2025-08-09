# EduMap — O‘zbekistonda ta’lim xaritasi

Loyiha: hududlar bo‘yicha ta’limga kirish, sifat va resurslar farqlarini vizualizatsiya qilish, tahlil va AI asosida tavsiyalar ishlab chiqish.

## Ishga tushirish

1) Talablar o‘rnatish:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Ilovani ishga tushirish:

```bash
python app.py
```

Brauzerda `http://localhost:5000` manzilini oching.

## Ma’lumotlar
- Demo ma’lumotlar: `data/regions.csv`
- Ularni haqiqiy ma’lumotlarga almashtiring (stat.uz, EMIS, Maktab.uz).

## Vizualizatsiya
- Ilova Folium xaritasini `/map` orqali hosil qiladi.
- Agar Tableau/Power BI embed qilmoqchi bo‘lsangiz, `static/index.html` ichidagi map panelidagi iframe adresini o‘z public dashboard linkingizga almashtiring.

## API lar
- `/api/regions` — viloyatlar ro‘yxati
- `/api/stats?region=...` — hudud statistikasi
- `/api/compare?metric=avg_score` — taqqoslash uchun metrik bo‘yicha ro‘yxat
- `/api/clusters` — KMeans klasterlari
- `/api/predict` — POST, input: features; output: avg_score va dropout bashorati
- `/api/sentiment` — POST, input: text; output: sentiment
- `/api/recommendations?region=...` — heuristik tavsiyalar

## AI
- Regressiya (LinearRegression, RandomForestRegressor)
- KMeans clustering
- VADER sentiment (NLP)

## Frontend
- Oddiy HTML/CSS/JS; Chart.js diagrammalari; Folium xarita iframe orqali.

