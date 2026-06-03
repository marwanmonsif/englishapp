# دليل الـ Deploy خطوة بخطوة

---

## الخطوة 1: GitHub

### 1.1 حمّل Git
- روح: https://git-scm.com/download/win
- حمّل وثبّت بـ default settings

### 1.2 عمل account على GitHub
- روح: https://github.com
- اعمل account مجاني

### 1.3 ارفع المشروع على GitHub
افتح CMD في مجلد englishapp واكتب:

```
git init
git add .
git commit -m "first commit"
```

بعدين:
- على GitHub اعمل repository جديد اسمه `englishapp`
- اتبع التعليمات اللي بتظهر عشان ترفع الكود

---

## الخطوة 2: Railway (الاستضافة)

### 2.1 عمل account
- روح: https://railway.app
- اعمل account بـ GitHub (أسهل)

### 2.2 عمل مشروع جديد
1. اضغط **New Project**
2. اختار **Deploy from GitHub repo**
3. اختار الـ repository بتاعك `englishapp`
4. اضغط **Deploy Now**

### 2.3 إضافة PostgreSQL
1. في المشروع اضغط **+ New**
2. اختار **Database → PostgreSQL**
3. Railway هيعمل database أوتوماتيك

### 2.4 إضافة Environment Variables
في المشروع اضغط على الـ service → **Variables** وأضف:

| اسم المتغير | القيمة |
|---|---|
| `SECRET_KEY` | اكتب أي كلام طويل عشوائي مثلاً: `monsif2025xEnglishLMSsecret!@#` |
| `FLASK_ENV` | `production` |
| `PORT` | `5000` |

الـ `DATABASE_URL` بيتضاف أوتوماتيك من الـ PostgreSQL.

### 2.5 شغّل
Railway هيشغل المشروع أوتوماتيك وهيديك رابط زي:
```
https://englishapp-production.up.railway.app
```

---

## الخطوة 3: Domain (اختياري)

### 3.1 اشتري domain
- روح: https://namecheap.com
- ابحث عن اسم زي: `mr-monsif.com` أو `monsif-english.com`
- السعر ~$10 في السنة

### 3.2 ربط الـ domain بـ Railway
1. في Railway اضغط على **Settings → Domains**
2. اضغط **Custom Domain**
3. اكتب الـ domain بتاعك
4. Railway هيديك **CNAME record**
5. روح Namecheap → DNS Settings وأضف الـ CNAME

بعد 5-10 دقايق الـ domain هيشتغل.

---

## ملخص التكلفة

| الخدمة | السعر |
|---|---|
| Railway (Starter) | مجاني لـ 500 ساعة/شهر، بعدين $5/شهر |
| Domain | ~$10/سنة |
| **المجموع** | **~$5/شهر + $10/سنة** |

---

## لو في مشكلة

- Railway بيعرض logs في real-time — لو في error هتشوفه هناك
- تأكد إن كل الـ environment variables اتضافوا صح
