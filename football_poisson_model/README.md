# ⚽ Global AI Futbol Tahmin & Canlı Otonom Kupon Botu

**Poisson & Dixon-Coles** istatistiksel motoruyla **13+ dünya ligini** ve güncel İddaa/büro bültenini saniyeler içinde tarayan, **canlı oranlarla Değer Bahislerini (+EV)** ve **%70 - %95 güvenilirlikli** kuponları otomatik oluşturan profesyonel futbol analiz sistemi.

---

## 🌟 Öne Çıkan Canlı Yetenekler

| Özellik | Açıklama |
|---------|----------|
| **📡 Canlı İddaa & Maç Çekici (`live_fetcher.py`)** | 12+ dünya liginden anlık maçları, saatleri ve güncel büro oranlarını (1, X, 2, 2.5 Alt/Üst) 2.9 saniyede çeker. |
| **🔥 Pozitif Değer Bahsi (+EV)** | İddaa oranını Poisson modelinin adil oranıyla kıyaslayarak piyasaya göre en avantajlı ve kazançlı maçları filtreler. |
| **🛡️ 3 Farklı Otonom Kupon Modu** | 1) **Banko Kasa Kuponu** (%70-%95 Güven)<br>2) **Yüksek Oranlı Değer (+EV) Kuponu**<br>3) **2.5 Alt/Üst Gol Kuponu** |
| **🌐 Modern Web Dashboard (`dashboard.py`)** | "⚡ Canlı İddaa Bültenini Yenile" butonu, anlık filtreleme, kupon oluşturucu ve xG tahmin matrisi. |
| **🧠 Akıllı Takım ve Takvim Eşleme** | Takım isimlerini (çeviri, kısaltma, aksan) otomatik tanır; yeni takımlar için lig ortalaması baz alır, maç kaçırmaz. |
| **⚡ Sıfır Dış Bağımlılık (Pure Python)** | `pandas`, `scipy` veya `numpy` zorunluluğu yoktur. Tamamen standart Python ile ışık hızında çalışır. |

---

## 📐 Matematiksel Altyapı

### 1. Beklenen Gol Sayısı ($\lambda$)
$$\lambda_{ev} = \alpha_{ev}(H) \times \beta_{dep}(A) \times \bar{G}_{ev}$$
$$\lambda_{dep} = \alpha_{dep}(A) \times \beta_{ev}(H) \times \bar{G}_{dep}$$

### 2. Dixon-Coles Düzeltmesi ($\rho = -0.08$)
Futbolda sık görülen düşük skorlardaki (0-0, 1-0, 0-1, 1-1) Poisson bağımsızlık sapmasını $\tau(x,y)$ katsayısıyla düzeltir.

### 3. Değer Bahsi (Pozitif Beklenen Değer - +EV)
$$\text{Beklenen Değer (EV \%)} = (P_{\text{model}} \times \text{İddaa Oranı} - 1) \times 100$$
- Eğer **EV > 0** ise; bahis bürosu matematiksel ihtimale göre olması gerekenden **daha yüksek bir oran** açmıştır. Uzun vadede kesin kazanç sağlayan profesyonel fon stratejisidir.

---

## 🚀 Çalıştırma Rehberi

### 1. Web Paneli (Tavsiye Edilen)
```bash
cd football_poisson_model
python dashboard.py
```
- Tarayıcınızda otomatik olarak `http://localhost:5000` açılır.
- Üstteki **"⚡ Canlı İddaa Bültenini Yenile"** butonuna basarak tüm dünya liglerindeki 75+ maçı anlık güncelleyebilirsiniz.
- **Canlı Maç Radarı** sekmesinden *"🔥 En İyi Oranlı Değer Bahisleri (+EV)"* veya *"🛡️ En Net Bankolar"* filtrelerini kullanabilirsiniz.

### 2. Terminalden Canlı Bülteni Çekme
```bash
python live_fetcher.py
```
- Güncel maçları, ligleri ve açılan canlı oranları terminalde tablo halinde listeler.

### 3. Otonom Kupon Botunu Çalıştırma
```bash
python scanner_bot.py
```
- 75 maçı tarar, en yüksek olasılıklı bankoları ve kuponları terminale döker.

---

## 📁 Dosya Yapısı

```
football_poisson_model/
├── live_fetcher.py       # Paralel canlı maç ve oran çekici (ESPN / DraftKings / İddaa)
├── dashboard.py          # Modern koyu tema web arayüzü & tek sayfa uygulama
├── scanner_bot.py        # Otonom radar, filtreler ve 3 farklı kupon mimarisi
├── model.py              # Poisson & Dixon-Coles model motoru + akıllı takım eşleme
├── data_loader.py        # CSV okuma, sütun eşleme, SimpleDataFrame
├── backtester.py         # Out-of-sample geçmiş maç doğrulama motoru
├── predictor_cli.py      # Terminal üzerinden tekil maç tahmin arayüzü
└── data/
    ├── upcoming_fixtures.json   # Canlı çekilen 75+ güncel maç ve oranlar
    └── *.csv                    # 13 ligin geçmiş performans veri setleri
```

---

## ⚠️ Sorumluluk Reddi
Bu sistem istatistiksel bir olasılık analiz aracıdır. Spor karşılaşmalarında kesinlik matematiksel olarak imkansızdır; sistem uzun vadeli pozitif beklenti (+EV) mantığıyla çalışır.
