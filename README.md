# MapReduce-Framework-Simulation
Multi-threaded MapReduce Framework Simulation with Pygame
proje 1: Devasa Veriler İçin Paralel MapReduce Framework Simülasyonu

Bu proje, Jeffrey Dean ve Sanjay Ghemawat tarafından 2004 yılında yayınlanan *"MapReduce: Simplified Data Processing on Large Clusters"* bilimsel makalesinden esinlenerek geliştirilmiş, çok kanallı (multi-threaded) bir MapReduce framework simülasyonudur. 

Proje, Pygame arayüzü sayesinde arka planda dönen paralel veri işleme süreçlerini, thread yüklerini ve ölçeklenebilirlik analizlerini canlı olarak görselleştirmektedir.

## 🚀 Öne Çıkan Özellikler & Mühendislik Yaklaşımları

- **Dinamik Dosya Algılama (Data Streaming):** Sistem hard-coded çalışmaz. Çalışma dizinindeki (klasördeki) tüm `.txt` uzantılı dosyaları otomatik tarar und kullanıcıya şık bir seçim arayüzü sunar.
- **Granular Step-by-Step Control (Derin Kullanıcı Etkileşimi):** Simülasyon başlangıcında hız seçimi yapılabilir. Simülasyon esnasında klavye ok tuşlarıyla vites (hız) değiştirilebilir, `SPACE` ile durdurulup `SAĞ OK` ile kare kare (adım adım) algoritmanın karar mekanizması izlenebilir.
- **Sınırsız Kaydırma (Scroll Bound Fix):** Gruplanan ve indirgenen veriler ne kadar büyük olursa olsun, mouse tekerleğiyle paneller aşağı/yukarı kaydırılarak tüm sonuçlar güvenli sınırlarla incelenebilir.
- **Güvenli Eşzamanlılık (Safe Concurrency & Mutex):** Arka planda çalışan Map ve disk okuma thread'lerinin veri tutarlılığını bozmaması (Race Condition oluşmaması) adına `threading.Lock()` (Mutex) mimarisi kullanılmıştır.
- **Uç Durum Koruması (Extreme Edge Case Handling):** Kelime sayısının thread sayısından az olması durumunda oluşabilecek sıfıra bölünme (Division by Zero) veya sonsuz döngü hataları, dinamik chunk boyutu sınırlandırması (`max(1, size)`) ile tamamen engellenmiştir. Tek bir kelimelik dosyalarda bile sistem kusursuz çalışır.

## 🛠 Mimari Tasarım (Architectural Pipeline)

Sistem 4 ana aşamadan oluşur ve arayüzde bu aşamalar mimari olarak birbirinden bağımsız panellerle ayrılmıştır:
1. **Disk Veri Akışı (Input Split / Stream):** Dosyadan bloklar halinde okunan ham verilerin akışı.
2. **Map Aşaması (Paralel İşleme):** 4 farklı Thread'in kendine ayrılan veri parçalarını (chunk) paralel olarak `(kelime, 1)` çiftlerine dönüştürmesi.
3. **Shuffle & Sort (Gruplama):** Map çıktılarının kelime bazlı anahtarlara (keys) göre senkronize şekilde gruplanması.
4. **Reduce Aşaması (Sonuçlar):** Gruplanan kelimelerin toplam frekanslarının (WordCount) hesaplanması.

## 📊 Ölçeklenebilirlik & Amdahl Kanunu Analizi

Simülasyon başarıyla tamamlandığında, sistem otomatik olarak **Amdahl Kanunu Performans Analizi** grafiğini alt panelde dinamik olarak çizer. Farklı çekirdek (Thread) sayılarında elde edilen teorik hızlanma (Speedup) oranları, paralelleştirilemeyen (seri) kod bloklarının algoritma üzerindeki teorik sınırlarını doğrular niteliktedir.

## 💻 Kurulum ve Çalıştırma

Projenin bilgisayarınızda çalışması için `pygame` kütüphanesinin kurulu olması gerekmektedir:

```bash
pip install pygame
