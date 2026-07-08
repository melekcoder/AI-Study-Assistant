from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    istatistikler = {
        "aktif_ders": 2,
        "ai_ozet": 12,
        "calisma_saati": 5
    }
    son_dersler = [
        {
            "ad": "Nesne Yönelimli Programlama (C++)",
            "zaman": "10 dakika önce",
            "ozet": "Polimorfizm Özet Dosyası",
            "durum": "Tamamlandı"
        },
        {
            "ad": "Fizik 1 (Mekanik)",
            "zaman": "Dün",
            "ozet": "Newton Kanunları Formülleri",
            "durum": "İşleniyor"
        },
        {
            "ad": "Web Tasarımı ve Programlama",
            "zaman": "2 gün önce",
            "ozet": "Flask Rotaları Giriş",
            "durum": "Tamamlandı"
        }
    ]
    return render_template('dashboard.html', istatistik=istatistikler, dersler=son_dersler)


@app.route('/derslerim')
def derslerim():
    ders_listesi = [
        {
            "ad": "Nesne Yönelimli Programlama (C++)",
            "hoca": "Dr. Mehmet Güvenir",
            "ozet_adedi": 5,
            "ilerleme": 75
        },
        {
            "ad": "Fizik 1 (Mekanik)",
            "hoca": "Prof. Dr. Necati Çelik",
            "ozet_adedi": 4,
            "ilerleme": 40
        },
        {
            "ad": "Web Tasarımı ve Programlama",
            "hoca": "Öğr. Gör. Ahmet Demir",
            "ozet_adedi": 3,
            "ilerleme": 90
        }
    ]
    return render_template('derslerim.html', tum_dersler=ders_listesi)

@app.route('/ai_sohbet')
def ai_sohbet():
    ornek_konusma = [
        {
            "gonderen": "kullanici",
            "metin": "Selam! Bugün C++ dersindeki Polimorfizm konusunu anlamadım, kısaca özetler misin?"
        },
        {
            "gonderen": "yapay_zeka",
            "metin": "Selam Melek! Tabii ki. Polimorfizm (Çok Biçimlilik), aynı isimdeki bir fonksiyonun farklı sınıflarda (class) farklı işler yapabilmesidir. Örneğin; 'sesCikar()' fonksiyonu Kedi sınıfında 'Miyav', Köpek sınıfında 'Hav' çıktısı verir. Kod tekrarını önler!"
        },
        {
            "gonderen": "kullanici",
            "metin": "Süper anladım, teşekkürler! Peki Fizik 1 sınavı için formül kağıdı hazırlayabilir miyiz?"
        },
        {
            "gonderen": "yapay_zeka",
            "metin": "Harika bir fikir! Newton Kanunları ve Mekanik konularını kapsayan şık bir formül özetini 'Derslerim' sayfasına şimdiden ekledim, oradan inceleyebilirsin. 🚀"
        }
    ]
    return render_template('ai_sohbet.html', sohbet_gecmisi=ornek_konusma)

if __name__ == "__main__":
    app.run(debug=True)