import yfinance as yf

# 1) Takip listesi
hisseler = [
    "THYAO.IS", "ASELS.IS", "TUPRS.IS", "BIMAS.IS", "EREGL.IS",
    "SISE.IS", "KCHOL.IS", "SAHOL.IS", "PETKM.IS", "TOASO.IS",
    "YKBNK.IS", "GARAN.IS", "ISCTR.IS", "AKBNK.IS", "FROTO.IS"
]

sonuclar = []  # (kod, anlik_fiyat(float), gun_ici_degisim_%(float))

for kod in hisseler:
    try:
        # auto_adjust'i açikça veriyoruz (FutureWarning yok),
        # group_by="column" ile tek seviyeli sütun aliyoruz.
        df = yf.download(
            kod, period="1d", interval="5m",
            auto_adjust=True, group_by="column", progress=False
        )

        # Veri yoksa atla
        if df.empty:
            continue

        # "Open" ve "Close" sütunlari yoksa atla (nadir durum)
        if ("Open" not in df.columns) or ("Close" not in df.columns):
            continue

        # Tekil skalar degerler: iloc[...] + float(...) ? garanti float
        acilis = float(df["Open"].iloc[0])
        anlik  = float(df["Close"].iloc[-1])

        # Yüzde degisim de float
        degisim = float((anlik - acilis) / acilis * 100.0)

        sonuclar.append((kod, anlik, degisim))

    except Exception as e:
        print("Hata:", kod, "->", e)

if not sonuclar:
    print("Veri bulunamadi. Internet/piyasa saatleri/semboller kontrol edilmeli.")
else:
    # degisim'e göre azalan sirala
    sirali = sorted(sonuclar, key=lambda x: x[2], reverse=True)

    print("En Çok Yükselenler (Top 5)")
    for kod, fiyat, pct in sirali[:5]:
        print(kod, "| Fiyat:", round(fiyat, 2), "| Degisim(%):", round(pct, 2))

    print("\nEn Çok Düsenler (Top 5)")
    for kod, fiyat, pct in sirali[-5:][::-1]:
        print(kod, "| Fiyat:", round(fiyat, 2), "| Degisim(%):", round(pct, 2))

    print("\nBasit Yorumlar (otomatik)")
    yukari_esik = 2.0
    asagi_esik  = -2.0
    for kod, fiyat, pct in sirali:
        if pct > yukari_esik:
            yorum = "Gun ici guclu (> %s%%)" % yukari_esik
        elif pct < asagi_esik:
            yorum = "Gun ici zayif (< %s%%)" % abs(asagi_esik)
        else:
            yorum = "Yatay sayilir"
        print(kod, "->", yorum, "| Fiyat:", round(fiyat, 2), "| Degisim(%):", round(pct, 2))