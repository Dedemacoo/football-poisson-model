# ⚽ AI Destekli Futbol Tahmin & Otonom Kupon Motoru
### (Poisson & Dixon-Coles Probability Engine with Live Odds, Injury Lab & Radar)

Canlı bülten maçlarını, iddaa/bahis oranlarını ve sakatlık/kadro eksikliklerini matematiksel **Poisson & Dixon-Coles** dağılımı ile analiz eden otonom kupon ve tahmin platformu.

---

## 🌟 Öne Çıkan Özellikler

1. **⚡ Canlı Fikstür & Güncel Oranlar:**
   - 12+ popüler ligden (Süper Lig, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Şampiyonlar Ligi vb.) 75+ canlı maçı saniyeler içinde çeker.
   - İddaa/bahis oranlarını ondalık (decimal) sisteme dönüştürerek modele entegre eder.

2. **📊 Matematiksel Değer (+EV) Radarı:**
   - Kitapçı oranlarının ima ettiği olasılık ($1/\text{oran}$) ile Poisson modelinin hesapladığı saf olasılığı kıyaslar.
   - Sadece pozitif beklenen değere (+EV) sahip yüksek kazanç fırsatlarını filtreler.

3. **🚑 Sakatlık & Kadro Etki Laboratuvarı:**
   - Yıldız forvet, kaleci ve savunma liderlerinin yokluğunda takımın gol beklentisi ($\lambda$) ve gol yeme riskini anlık olarak simüle eder.
   - Kadro eksikliklerine göre oranların nasıl kaydığını canlı interaktif simülatörle gösterir.

4. **🤖 3 Kademeli Otonom Kupon Botu:**
   - **🛡️ Güvenli Banko Kasa Katlama (%70 - %95 Başarı)**
   - **💎 Yüksek Değerli (+EV) Value Avcısı**
   - **⚽ 2.5 Üst & KG Var Gol Yağmuru**

5. **🎓 İnteraktif Kullanıcı Rehberi & Bahis Akademisi:**
   - Yeni başlayanlar için sıfırdan adım adım rehber, +EV mantığı, Kelly Kriteri kasa yönetimi ve kupon stratejileri.

6. **🚩 Uluslararası Lig Bayrakları:**
   - Süper Lig, Premier League vb. tüm lig ve maçlar yüksek çözünürlüklü ülke bayrak rozetleriyle zenginleştirilmiştir.

---

## 🚀 Hızlı Başlangıç (Lokal)

Windows kullanıcıları için tek tıkla başlatma:
```bash
baslat.bat
```
Veya doğrudan komut satırından:
```bash
python main.py
```
Arayüz otomatik olarak `http://localhost:5000` adresinde açılacaktır.

---

## ☁️ Canlı Sunucuya Yayınlama (Cloud Deployment)

### 1. Render.com (Önerilen - Ücretsiz 7/24)
1. Bu depoyu GitHub hesabınıza push edin.
2. [Render.com](https://render.com) paneline gidin.
3. **New +** -> **Web Service** seçin ve GitHub deponuzu bağlayın.
4. Render depodaki `render.yaml` ve `requirements.txt` dosyalarını otomatik tanıyacaktır.
5. Deploy butonuna basın, birkaç dakika içinde `https://proje-adiniz.onrender.com` adresinde canlıya geçer!

### 2. Railway.app / Koyeb / Fly.io
Depodaki `Dockerfile` veya `Procfile` sayesinde Railway, Koyeb veya Docker destekleyen herhangi bir bulut sunucusunda sıfır konfigürasyon ile doğrudan çalışır.
