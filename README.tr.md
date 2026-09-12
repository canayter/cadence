# Cadence

*[English](README.md)*

Last.fm dinleme geçmişini gerçek bir Bluesky thread'ine dönüştürür: seçtiğiniz bir hafta, ay ya da herhangi bir aralık için en çok dinlenen sanatçılar, şarkılar ve albümler — ekran görüntüsü ya da elle kopyala-yapıştır yerine, biçimlendirilmiş, gerçek bir AT Protocol thread'i olarak paylaşılır.

Eski adı ScrobbleForge'du. Aynı araç, daha kısa bir isimle.

**Tarayıcıda deneyin:** [ayter.com/cadence](https://ayter.com/cadence) — kurulum gerektirmeyen, tamamen istemci tarafında çalışan tek seferlik bir sürüm.
**Kendi sunucunuzda çalıştırın:** bu depo, otomatik olarak her hafta paylaşım yapabilen sürüm için.
**Yazan:** [Can Ayter](https://ayter.com)

## Neler yapıyor

Last.fm API'sinden seçilen zaman aralığı için (hafta, ay, 3 ay, 6 ay, yıl ya da tüm zamanlar) dinleme verisini çeker, herhangi bir şey paylaşılmadan önce sanatçı, albüm, şarkı ya da türe göre filtrelemenize izin verir, ve sonucu düzgün bir şekilde threadlenmiş bir Bluesky gönderi dizisine dönüştürür. Bir Streamlit arayüzü her şeyi sarmalar — aralığı seçin, thread'i önizleyin, paylaşın.

**Otomatik zamanlama.** Arayüzden bir haftanın günü ve saatini seçerek zamanlayıcıyı başlatın; uygulama çalışmaya devam ettiği sürece dinleme özetinizi her hafta otomatik olarak paylaşır. Bu ayrı bir cron işi ya da barındırılan bir servis değil — çalışan Streamlit uygulamasının içindeki bir arka plan döngüsü; zamanlama özelliğinin neden sadece tarayıcı sürümüyle değil, kendi sunucunuzda çalıştırmayı gerektirdiği de bu yüzden.

## Nasıl organize edildi

Her dosyanın tek bir işi var; bu da otomatik zamanlayıcıyı, zaten çalışan kısımlara dokunmadan eklemeyi mümkün kıldı:

```
cadence/
├── app.py          Streamlit arayüzü: düzen, kontroller, otomatik zamanlayıcı döngüsü
├── lastfm.py       Last.fm API istemcisi — dinleme verisi, en çok dinlenenler
├── digest.py       filtreleme ve biçimlendirme: apply_filters(), build_thread_posts()
├── bluesky.py      biçimlendirilmiş thread'i atproto SDK'sı üzerinden paylaşır
└── requirements.txt
```

## Kendiniz çalıştırmak isterseniz

```bash
git clone https://github.com/canayter/cadence.git
cd cadence
pip install -r requirements.txt
cp .env.example .env    # Last.fm ve Bluesky bilgilerinizi girin
streamlit run app.py
```

`.env` dosyasında bir Last.fm API anahtarı ve kullanıcı adı, ayrıca bir Bluesky kullanıcı adı ve bir **uygulama şifresi** gerekir (Settings → Privacy & Security → App Passwords altından oluşturun — buraya asla gerçek hesap şifrenizi girmeyin).

## Bağımlılıklar

`streamlit`, `pandas`, `requests`, `python-dotenv`, ve Bluesky/AT Protocol tarafı için `atproto`.

## Yazan

**Can Ayter** — [ayter.com](https://ayter.com)

Bağımsız bir proje, Last.fm ya da Bluesky ile bir bağlantısı yoktur. MIT Lisansı.
