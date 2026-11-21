import os
import sqlite3
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, abort)
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
    # aktif_ders artık gerçek; ai_ozet ve calisma_saati hâlâ örnek (TODO)
    istatistikler = {
        "aktif_ders": len(dersleri_getir(session["user_id"])),
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


def dersleri_getir(user_id):
    """Giriş yapan kullanıcının derslerini, not sayısıyla birlikte getirir."""
    baglanti = get_db()
    satirlar = baglanti.execute(
        """
        SELECT c.id, c.name, c.instructor, c.progress,
               COUNT(n.id) AS not_sayisi
        FROM courses c
        LEFT JOIN notes n ON n.course_id = c.id
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.created_at DESC, c.id DESC
        """,
        (user_id,),
    ).fetchall()
    baglanti.close()
    return satirlar


@app.route("/derslerim", methods=["GET", "POST"])
@login_required
def derslerim():
    user_id = session["user_id"]
    hata = None

    if request.method == "POST":
        ad = request.form.get("name", "").strip()
        hoca = request.form.get("instructor", "").strip()
        ilerleme_metni = request.form.get("progress", "0").strip() or "0"

        if not ad:
            hata = "Ders adı boş olamaz."
        elif len(ad) > 100:
            hata = "Ders adı en fazla 100 karakter olabilir."
        elif not ilerleme_metni.isdigit() or not 0 <= int(ilerleme_metni) <= 100:
            hata = "İlerleme 0 ile 100 arasında bir sayı olmalı."
        else:
            baglanti = get_db()
            baglanti.execute(
                "INSERT INTO courses (user_id, name, instructor, progress) "
                "VALUES (?, ?, ?, ?)",
                (user_id, ad, hoca or None, int(ilerleme_metni)),
            )
            baglanti.commit()
            baglanti.close()
            # POST sonrası yönlendir: sayfa yenilenince form tekrar gönderilmesin
            return redirect(url_for("derslerim"))

    return render_template("derslerim.html",
                           tum_dersler=dersleri_getir(user_id), hata=hata)


@app.route("/ders_sil/<int:ders_id>", methods=["POST"])
@login_required
def ders_sil(ders_id):
    user_id = session["user_id"]
    baglanti = get_db()
    # Önce dersin notları (foreign key yüzünden), sonra ders.
    # İki sorguda da user_id kontrolü var: başkasının dersini silemezsin.
    baglanti.execute(
        "DELETE FROM notes WHERE course_id = ? AND user_id = ?",
        (ders_id, user_id))
    baglanti.execute(
        "DELETE FROM courses WHERE id = ? AND user_id = ?",
        (ders_id, user_id))
    baglanti.commit()
    baglanti.close()
    return redirect(url_for("derslerim"))


# ---------------------------------------------------------------- NOTLAR
# Güvenlik kuralı: her sorguda user_id kontrolü var. Başka kullanıcının
# ders/notuna ulaşmaya çalışan biri 404 alır (var olup olmadığını bile öğrenmez).

BASLIK_MAX = 150
ICERIK_MAX = 20000  # yapay zekâ özeti için de makul bir üst sınır


def ders_getir(ders_id, user_id):
    baglanti = get_db()
    ders = baglanti.execute(
        "SELECT * FROM courses WHERE id = ? AND user_id = ?",
        (ders_id, user_id)).fetchone()
    baglanti.close()
    return ders


def not_getir(not_id, user_id):
    baglanti = get_db()
    satir = baglanti.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (not_id, user_id)).fetchone()
    baglanti.close()
    return satir


def not_dogrula(baslik, icerik):
    """Hata mesajı döndürür, sorun yoksa None."""
    if not baslik:
        return "Not başlığı boş olamaz."
    if len(baslik) > BASLIK_MAX:
        return f"Başlık en fazla {BASLIK_MAX} karakter olabilir."
    if len(icerik) > ICERIK_MAX:
        return f"Not içeriği en fazla {ICERIK_MAX} karakter olabilir."
    return None


@app.route("/ders/<int:ders_id>", methods=["GET", "POST"])
@login_required
def ders_detay(ders_id):
    user_id = session["user_id"]
    ders = ders_getir(ders_id, user_id)
    if ders is None:
        abort(404)

    hata = None
    if request.method == "POST":
        baslik = request.form.get("title", "").strip()
        icerik = request.form.get("content", "").strip()
        hata = not_dogrula(baslik, icerik)
        if hata is None:
            baglanti = get_db()
            baglanti.execute(
                "INSERT INTO notes (user_id, course_id, title, content) "
                "VALUES (?, ?, ?, ?)",
                (user_id, ders_id, baslik, icerik))
            baglanti.commit()
            baglanti.close()
            return redirect(url_for("ders_detay", ders_id=ders_id))

    baglanti = get_db()
    # 'localtime': kayıt UTC tutulur, gösterirken bilgisayarın saatine çevrilir
    notlar = baglanti.execute(
        """
        SELECT id, title, content,
               datetime(created_at, 'localtime') AS tarih
        FROM notes
        WHERE course_id = ? AND user_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (ders_id, user_id)).fetchall()
    baglanti.close()

    return render_template("ders_detay.html", ders=ders, notlar=notlar,
                           hata=hata)


@app.route("/not/<int:not_id>/duzenle", methods=["GET", "POST"])
@login_required
def not_duzenle(not_id):
    user_id = session["user_id"]
    kayit = not_getir(not_id, user_id)
    if kayit is None:
        abort(404)

    hata = None
    baslik, icerik = kayit["title"], kayit["content"] or ""

    if request.method == "POST":
        baslik = request.form.get("title", "").strip()
        icerik = request.form.get("content", "").strip()
        hata = not_dogrula(baslik, icerik)
        if hata is None:
            baglanti = get_db()
            baglanti.execute(
                "UPDATE notes SET title = ?, content = ? "
                "WHERE id = ? AND user_id = ?",
                (baslik, icerik, not_id, user_id))
            baglanti.commit()
            baglanti.close()
            return redirect(url_for("ders_detay", ders_id=kayit["course_id"]))

    ders = ders_getir(kayit["course_id"], user_id)
    return render_template("not_duzenle.html", ders=ders, not_id=not_id,
                           baslik=baslik, icerik=icerik, hata=hata)


@app.route("/not/<int:not_id>/sil", methods=["POST"])
@login_required
def not_sil(not_id):
    user_id = session["user_id"]
    kayit = not_getir(not_id, user_id)
    if kayit is None:
        abort(404)
    baglanti = get_db()
    baglanti.execute("DELETE FROM notes WHERE id = ? AND user_id = ?",
                     (not_id, user_id))
    baglanti.commit()
    baglanti.close()
    return redirect(url_for("ders_detay", ders_id=kayit["course_id"]))


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
