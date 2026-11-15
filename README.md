# HarranCo Daily — إعداد لمرة وحدة

1. أنشئ مستودع GitHub **عام (Public)** وارفع كل ملفات هذا المجلد.
2. من Buffer: Settings ← API ← أنشئ Access Token.
3. في المستودع: Settings ← Secrets and variables ← Actions، وأضف:
   - `BUFFER_TOKEN`
   - `GEMINI_KEY_1`, `GEMINI_KEY_2` (مفاتيح جديدة، مو اللي انكشفت)
   - `ELEVENLABS_KEY` (اختياري)
4. تبويب Actions ← فعّل الـ workflows ← شغّل `harranco-ar` يدوياً مرة للتجربة (Run workflow).
5. بعدها يشتغل لحاله: عربي 12:30 ← ينشر 13:00 | إنجليزي 19:10 ← ينشر 21:00 (توقيت الرياض).

لو Buffer رفض رابط الفيديو، فعّل GitHub Pages على فرع `media` وحط متغير `MEDIA_BASE` برابط الصفحة.
تجربة محلية بدون نشر: `python -m harranco.run ar --dry`
