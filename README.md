# 🌐 LinguaBridge

Gerçek zamanlı çeviri ile görüntülü & sesli arama.
**Firefox ✅ Safari ✅ Chrome ✅ Edge ✅ — Her tarayıcıda çalışır.**

---

## Klasör Yapısı

```
linguabridge/
├── frontend/         ← Vercel deploy eder
│   └── index.html
├── backend/          ← Railway deploy eder
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── vercel.json       ← Vercel config (root'ta durur)
├── railway.toml      ← Railway config (root'ta durur)
└── README.md
```

---

## Deploy Adımları

### 1. GitHub'a yükle
```bash
git init
git add .
git commit -m "LinguaBridge ilk sürüm"
git remote add origin https://github.com/KULLANICI_ADIN/linguabridge.git
git push -u origin main
```

### 2. Railway — Backend
1. railway.app → New Project → Deploy from GitHub
2. `linguabridge` reposunu seç
3. **Settings → Root Directory → `backend`** yaz
4. Deploy et (~5 dakika, Whisper indirilir)
5. **Settings → Domains → Generate Domain** → URL kopyala
6. URL şöyle görünür: `https://linguabridge-xxx.up.railway.app`

### 3. Vercel — Frontend
1. vercel.com → New Project → GitHub'dan `linguabridge` seç
2. **Root Directory → `frontend`** yaz
3. Deploy et (30 saniye)
4. Vercel URL'ini al: `https://linguabridge-xxx.vercel.app`

### 4. Backend URL'ini siteye bağla
1. Vercel siteni aç
2. Üstteki sarı kutucuğa Railway URL'ini yapıştır
3. **Kaydet & Test Et** → ✅ yeşil görünce hazır!

---

## Kullanım

1. Siteyi aç → 6 haneli kod oluşur
2. **Davet Linki** kopyala → WhatsApp/Telegram ile gönder
3. Karşı taraf linke tıklar → kod otomatik girer → Ara'ya basar
4. Bağlantı kurulunca çeviri otomatik başlar
5. Sen Türkçe konuş → karşı tarafa İngilizce/Rusça/istediğin dile gider

---

## Desteklenen 19 Dil

🇹🇷 Türkçe · 🇺🇸 İngilizce · 🇷🇺 Rusça · 🇺🇦 Ukraynaca · 🇩🇪 Almanca
🇫🇷 Fransızca · 🇪🇸 İspanyolca · 🇮🇹 İtalyanca · 🇵🇹 Portekizce · 🇸🇦 Arapça
🇨🇳 Çince · 🇯🇵 Japonca · 🇰🇷 Korece · 🇮🇳 Hintçe · 🇳🇱 Hollandaca
🇵🇱 Lehçe · 🇻🇳 Vietnamca · 🇮🇩 Endonezyaca · 🇸🇪 İsveççe
