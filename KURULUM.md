# LinguaBridge — Tam Kurulum Rehberi
## Her Tarayıcıda Çalışır: Firefox ✅ Safari ✅ Chrome ✅ Edge ✅

---

## MİMARİ

```
Sen (Firefox/Safari/Chrome)
  └─ MediaRecorder → ses kaydı (her tarayıcıda çalışır)
       └─ Railway Backend → Faster-Whisper → metin
            └─ MyMemory/Lingva → çeviri
                 └─ P2P DataChannel → karşı tarafa gider
                      └─ TTS ile seslendirilir
```

---

## ADIM 1 — Backend'i Railway'e Deploy Et

### 1.1 Railway hesabı aç
- https://railway.app → GitHub ile giriş yap (ücretsiz)

### 1.2 Backend klasörünü GitHub'a yükle
```bash
cd linguabridge-full/backend
git init
git add .
git commit -m "LinguaBridge backend"
# GitHub'da yeni repo oluştur: linguabridge-backend
git remote add origin https://github.com/KULLANICI/linguabridge-backend.git
git push -u origin main
```

### 1.3 Railway'de proje oluştur
1. railway.app → **New Project**
2. **Deploy from GitHub repo** → `linguabridge-backend` seç
3. Railway otomatik Dockerfile'ı algılar ve build eder
4. Build ~3-5 dakika sürer (Whisper modeli indirilir)
5. **Settings → Domains → Generate Domain** → URL al

### 1.4 Environment variables (isteğe bağlı)
Railway Dashboard → Variables:
```
WHISPER_MODEL = tiny     # tiny/base/small (tiny en hızlı)
DEVICE        = cpu
```

### 1.5 URL'yi test et
Tarayıcıda aç:
```
https://SENIN-URL.up.railway.app/health
```
Şunu görmelisin: `{"status":"ok","whisper":"tiny","device":"cpu"}`

---

## ADIM 2 — Frontend'i Vercel'e Deploy Et

```bash
cd linguabridge-full/frontend
npm i -g vercel
vercel --prod
```
VEYA: vercel.com → New Project → frontend klasörünü zip yükle

---

## ADIM 3 — Bağla

1. Vercel'den aldığın URL'yi aç
2. **Backend URL** kutusuna Railway URL'ini yaz:
   `https://SENIN-URL.up.railway.app`
3. **Kaydet & Test Et** butonuna bas
4. ✅ yeşil gösterge → artık Firefox/Safari da tam çalışır!

---

## RAILWAY ÜCRETSİZ PLAN LİMİTLERİ

| Kısıt | Değer |
|-------|-------|
| Aylık kullanım | 500 saat (yeterli) |
| RAM | 512MB (tiny model için yeterli) |
| CPU | Paylaşımlı |
| Uyku modu | 30dk hareketsizlikte uyur, ilk istek ~10sn geç gelir |

**Uyku modunu önlemek için:**
UptimeRobot (ücretsiz) → 5dk'da bir /health endpoint'ine ping at

---

## SORUN GİDERME

**Backend çalışmıyor?**
- Railway → Deployments → Logs bak
- `WHISPER_MODEL=tiny` olduğundan emin ol

**Ses tanıma çalışmıyor?**
- Mikrofon izni ver (tarayıcı adres çubuğu sol yanı)
- Backend URL kayıtlı mı? (yeşil ✅ göstermeli)

**Çeviri gelmiyor?**
- DataChannel açık mı? Bağlantı kurulduktan sonra her iki taraf da ses alabilmeli

---

## NOTLAR

- Whisper `tiny` model: ~500MB RAM, ~1-2sn gecikme
- Whisper `base` model: ~1GB RAM, daha doğru
- Railway free tier RAM'i aşarsa `tiny` kullan
- Ses 4 saniyelik segmentler halinde işlenir (ayarlanabilir)
