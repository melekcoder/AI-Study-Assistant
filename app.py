import os
import sqlite3
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Oturum çerezini imzalamak için gizli anahtar.
# Gerçek ortamda SECRET_KEY ortam değişkeni olarak verilecek (koda yazma!).
app.secret_key = os.environ.get("SECRET_KEY", "gelistirme-icin-gecici-anahtar")

DB_YOLU = os.path.join(app.root_path, "database.db")


def get_db():
    baglanti = sqlite3.connect(DB_YOLU)
    baglanti.row_factory = sqlite3.Row  # sütunlara isimle erişmek için
    baglanti.execute("PRAGMA foreign_keys = ON")
    return baglanti


def init_db():
    baglanti = get_db()
    with open(os.path.join(app.root_path, "schema.sql"), encoding="utf-8") as f:
        baglanti.executescript(f.read())
    baglanti.commit()
    baglanti.close()


init_db()


def login_required(view):
    """Giriş yapmamış kullanıcıyı login sayfasına gönderir."""
    @wraps(view)
    def sarmalanmis(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return sarmalanmis


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    kullanici_adi = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    sifre = request.form.get("password", "")
    sifre_tekrar = request.form.get("confirm_password", "")

    if not kullanici_adi or not email or not sifre:
        return render_template("register.html", hata="Tüm alanları doldur.")
    if len(sifre) < 6:
        return render_template("register.html",
                               hata="Şifre en az 6 karakter olmalı.")
    if sifre != sifre_tekrar:
        return render_template("register.html", hata="Şifreler eşleşmiyor.")

    baglanti = get_db()
    try:
        baglanti.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (kullanici_adi, email, generate_password_hash(sifre)),
        )
        baglanti.commit()
    except sqlite3.IntegrityError:
        # username veya email UNIQUE kuralına takıldı
        return render_template(
            "register.html",
            hata="Bu kullanıcı adı veya e-posta zaten kayıtlı.")
    finally:
        baglanti.close()

    return redirect(url_for("login", kayit="ok"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        basari = "Kayıt başarılı, şimdi giriş yapabilirsin." \
            if request.args.get("kayit") == "ok" else None
        return render_template("login.html", basari=basari)

    email = request.form.get("email", "").strip().lower()
    sifre = request.form.get("password", "")

    baglanti = get_db()
    kullanici = baglanti.execute(
        "SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    baglanti.close()

    # Hangisinin yanlış olduğunu söylemiyoruz (güvenlik için tek mesaj)
    if kullanici is None or not check_password_hash(
            kullanici["password_hash"], sifre):
        return render_template("login.html",
                               hata="E-posta veya şifre hatalı.")

    session.clear()
    session["user_id"] = kullanici["id"]
    session["username"] = kullanici["username"]
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    # TODO: bu veriler sonraki adımda veritabanından gelecek
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
    return render_template("dashboard.html", istatistik=istatistikler,
                           dersler=son_dersler,
                           kullanici_adi=session["username"])


@app.route("/derslerim")
@login_required
def derslerim():
    # TODO: sonraki adımda courses tablosuna bağlanacak
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
    return render_template("derslerim.html", tum_dersler=ders_listesi)


@app.route("/ai_sohbet")
@login_required
def ai_sohbet():
    # TODO: gerçek yapay zeka entegrasyonu en son adım
    ornek_konusma = [
        {
            "gonderen": "kullanici",
            "metin": "Selam! Bugün C++ dersindeki Polimorfizm konusunu anlamadım, kısaca özetler misin?"
        },
        {
            "gonderen": "yapay_zeka",
            "metin": f"Selam {session['username']}! Tabii ki. Polimorfizm (Çok Biçimlilik), aynı isimdeki bir fonksiyonun farklı sınıflarda (class) farklı işler yapabilmesidir. Örneğin; 'sesCikar()' fonksiyonu Kedi sınıfında 'Miyav', Köpek sınıfında 'Hav' çıktısı verir. Kod tekrarını önler!"
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
    return render_template("ai_sohbet.html", sohbet_gecmisi=ornek_konusma)


if __name__ == "__main__":
    app.run(debug=True)
