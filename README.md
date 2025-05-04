# Türkiye Deprem Takip Sistemi

Türkiye Deprem Takip Sistemi, Türkiye'deki depremleri gerçek zamanlı olarak izlemenizi sağlayan web tabanlı bir uygulamadır. AFAD ve Kandilli Rasathanesi gibi resmi kaynaklardan alınan verilerle, son depremleri harita üzerinde görüntüleyebilir ve fay hatları bilgilerine erişebilirsiniz.

![Deprem Takip Sistemi](screenshot.png)

## Özellikler

- **Gerçek Zamanlı Takip**: Türkiye'deki son 150 depremi anlık olarak izleme
- **Etkileşimli Harita**: Deprem konumlarını ve fay hatlarını görsel olarak inceleme
- **Filtreleme Seçenekleri**: Depremleri "En Yeni" veya "En Büyük" olarak sıralama
- **Fay Hatları Bilgisi**: Türkiye'deki önemli fay hatlarının lokasyonları ve risk seviyelerini görüntüleme 
- **Bildirim Sistemi**: Belirli büyüklüğün üzerindeki depremler için anlık bildirim alma
- **Karanlık Mod**: Gece kullanımı için göz yormayan arayüz
- **Mobil Uyumluluk**: Tüm cihazlarda sorunsuz çalışan responsive tasarım

## Kurulum

### Gereksinimler

- Python 3.8+
- PostgreSQL
- Flask

### Adımlar

1. Repoyu klonlayın:
   ```
   git clone https://github.com/burakozcn01/turkiye-deprem-takip.git
   cd turkiye-deprem-takip
   ```

2. Sanal ortam oluşturun ve bağımlılıkları yükleyin:
   ```
   python -m venv venv
   source venv/bin/activate  # Windows için: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. PostgreSQL veritabanı oluşturun:
   ```
   createdb earthquake_db
   ```

4. Çevre değişkenlerini ayarlayın:
   ```
   export DATABASE_URL="postgresql://kullanici:sifre@localhost:5432/earthquake_db"
   export VAPID_PRIVATE_KEY="your_private_key"
   export VAPID_PUBLIC_KEY="your_public_key"
   ```

5. Uygulamayı çalıştırın:
   ```
   python app.py
   ```

6. Tarayıcınızda `http://localhost:5000` adresine gidin.

## Kullanım

### Deprem Takibi

- Uygulama yüklendiğinde, varsayılan olarak son 150 deprem "En Yeni" sıralanmış şekilde görüntülenir.
- "En Büyük" sekmesine tıklayarak depremleri büyüklüklerine göre sıralayabilirsiniz.
- Herhangi bir depreme tıkladığınızda, harita o konuma odaklanır ve detaylı bilgileri görüntüler.

### Fay Hatları

- "Fay Hatları" sekmesine tıklayarak Türkiye'deki fay hatlarını listeleyebilirsiniz.
- Listedeki bir fay hattına tıkladığınızda, harita o bölgeye odaklanır.
- Fay hatları risk seviyelerine göre renklendirilmiştir (Kırmızı: Yüksek Risk, Turuncu: Orta-Yüksek Risk, Sarı: Orta Risk).

### Bildirimler

- "Bildirimler" butonuna tıklayarak, tarayıcı bildirimlerini etkinleştirebilirsiniz.
- Sistem, büyüklüğü 4.0 ve üzeri olan depremler için bildirim gönderecektir.

## Veri Kaynakları

Bu uygulama aşağıdaki resmi kaynaklardan alınan verileri kullanmaktadır:

- AFAD (Afet ve Acil Durum Yönetimi Başkanlığı)
- Kandilli Rasathanesi ve Deprem Araştırma Enstitüsü
- EMSC (Avrupa-Akdeniz Sismoloji Merkezi)

---

**Not**: Bu uygulama bilgilendirme amaçlıdır ve resmi bir uyarı sistemi değildir. Acil durumlarda resmi kurumların uyarılarını takip ediniz.