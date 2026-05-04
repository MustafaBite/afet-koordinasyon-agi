# Deploy Rehberi

## AŞAMA 1 — Backend → Render

### Adımlar:
1. https://render.com adresine git ve GitHub hesabınla giriş yap
2. "New Web Service" → repo'yu seç → **Root Directory: `backend`**
3. Ayarlar otomatik `render.yaml`'dan gelecek
4. **Environment Variables** sekmesine şunları ekle:
   - `DATABASE_URL` = `postgresql://postgres.wopzlsanydvkdphciwtg:...@...supabase.com:5432/postgres` (mevcut .env'deki değer)
   - `SECRET_KEY` = güçlü bir secret key
5. Deploy et → Render sana bir URL verecek: `https://resq-api-xxxx.onrender.com`

---

## AŞAMA 2 — Vercel URL'ini Güncelle

Backend URL'ini aldıktan sonra `kriz-paneli/vercel.json` dosyasındaki tüm
`BACKEND_URL_BURAYA_YAZ` değerlerini gerçek URL ile değiştir:

```
# Bul: BACKEND_URL_BURAYA_YAZ
# Değiştir: resq-api-xxxx.onrender.com  (https:// olmadan)
```

---

## AŞAMA 3 — Frontend → Vercel + GitHub Actions

### Vercel Kurulumu:
1. https://vercel.com adresine git, GitHub ile giriş yap
2. "Add New Project" → repo'yu seç → **Root Directory: `kriz-paneli`** yap
3. Deploy et (ilk kez manuel) → `kriz-paneli/vercel.json` otomatik kullanılır

### Vercel Bilgilerini Al:
```bash
# Local terminalde kriz-paneli klasöründe çalıştır:
cd kriz-paneli
npx vercel whoami        # giriş yaptığını doğrula
npx vercel link          # projeyi bağla, .vercel/project.json oluşur
cat .vercel/project.json # orgId ve projectId'yi buradan al
```

### GitHub Secrets Ekle (repo → Settings → Secrets → Actions):
| Secret | Değer |
|--------|-------|
| `VERCEL_TOKEN` | https://vercel.com/account/tokens adresinden oluştur |
| `VERCEL_ORG_ID` | `.vercel/project.json` içindeki `orgId` |
| `VERCEL_PROJECT_ID` | `.vercel/project.json` içindeki `projectId` |

Artık `main` branch'e her push'ta frontend otomatik deploy olur.

---

## AŞAMA 4 — Android APK → EAS Build

### Expo Hesabı Hazırlığı:
1. https://expo.dev adresine git, hesap oluştur/giriş yap
2. https://expo.dev/settings/access-tokens adresinden token oluştur

### GitHub Secret Ekle:
| Secret | Değer |
|--------|-------|
| `EXPO_TOKEN` | Expo access token |
| `BACKEND_URL` | `https://resq-api-xxxx.onrender.com` (Render URL) |

### EAS Projesi Bağla (local terminalde):
```bash
cd mobile
npx eas-cli login
npx eas-cli project:init   # expo.dev'de proje oluşturur, app.json'a owner/extra.eas.projectId ekler
```

### APK Build Tetikle:
GitHub → Actions → "Build Android APK" → "Run workflow" → **preview** seç

APK linki build bittikten sonra Expo dashboard'da ve Actions loglarında görünür.

---

## Özet: Hangi Secrets Nereye

### GitHub Repo Secrets:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `EXPO_TOKEN`
- `BACKEND_URL`

### Render Environment Variables:
- `DATABASE_URL`
- `SECRET_KEY`

---

## Notlar
- Render free tier ilk istekte ~30 sn uyur (cold start). Production'da paid plan düşünülebilir.
- APK `preview` profili internal dağıtım içindir (doğrudan yüklenebilir).
- `production` profili Play Store için AAB üretir.
- WebSocket (`/ws`) Vercel üzerinden proxy edilir ama Render free tier'da timeout olabilir.
