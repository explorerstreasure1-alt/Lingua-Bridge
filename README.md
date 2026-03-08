# 🌐 LinguaBridge

Gerçek zamanlı çeviri ile görüntülü & sesli arama.
Firefox ✅ Safari ✅ Chrome ✅ Edge ✅ Mobil ✅

## Klasör Yapısı
```
Lingua-Bridge/
├── frontend/
│   └── index.html       ← Vercel static
├── api/
│   └── transcribe.js    ← Vercel serverless (Groq proxy)
├── backend/             ← kullanılmıyor
├── vercel.json
└── README.md
```

## Deploy
1. GitHub'a yükle
2. Vercel → New Project → bu repo → deploy
3. Vercel → Settings → Environment Variables:
   GROQ_API_KEY = gsk_xxx...
4. Redeploy → bitti
