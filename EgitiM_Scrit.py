# -*- coding: utf-8 -*-
"""
1) REGRESYON  (Regression)      -> Yarınki kapanış fiyatını tahmin etmek (sayısal tahmin)
2) SINIFLANDIRMA (Classification)-> Yarın yükselir mi? (Evet/Hayır, yani 1/0)
3) KÜMELEME (Clustering)        -> Etiket yok; günleri benzer davranışa göre gruplamak
4) BOYUT AZALTMA (PCA)          -> Feature'ları 2 boyuta indirip görselleştirmek

Not: Bu çalışma eğitim amaçlıdır, yatırım tavsiyesi değildir.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Makine öğrenmesi için (çok temel seviyede kullanacağız)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from sklearn.metrics import mean_absolute_error, accuracy_score, roc_auc_score


# -------------------------------------------------------------------
# 1) Veri çekme (yfinance) + yedek olarak sahte veri üretme
# -------------------------------------------------------------------
def veri_cek(ticker="THYAO.IS", start="2020-01-01"):
    """
    Burada amacım şunu öğretmek:
    - Gerçek veriyle çalışınca her şey daha anlamlı oluyor.
    - Ama bazen paket hatası / internet / API sorunu olur.
      Ders akmasın diye bir "B planı" koymak öğretmenlikte hayat kurtarır.

    Önce yfinance ile çekmeyi deniyoruz.
    Eğer yfinance yoksa / hata verirse, sahte bir kapanış serisi üretip devam ediyoruz.
    """

    try:
        import yfinance as yf

        df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
        df = df.dropna().copy()

        # İsimleri sadeleştirelim (Close sütunu garanti olsun diye)
        df.columns = [c.title() for c in df.columns]

        # Bize en temel şey yeter: "Close"
        # (İstersen daha sonra Volume, Open vs de ekleriz.)
        df = df[["Close"]].copy()

        return df, "yfinance"

    except Exception as e:
        print("\n[UYARI] yfinance ile veri çekemedim. Hata mesajı aşağıda:")
        print("        ", repr(e))
        print("[UYARI] Ders bozulmasın diye SAHTE veri üretiyorum (demo amaçlı).")

        # Sahte günlük kapanış: rastgele yürüyüş (random walk)
        rng = pd.date_range(start=start, periods=600, freq="B")  # B = business day
        prices = 100 + np.cumsum(np.random.normal(0, 1, size=len(rng)))  # basit fiyat yolu

        df = pd.DataFrame({"Close": prices}, index=rng)
        return df, "synthetic"


# -------------------------------------------------------------------
# 2) Feature üretimi
# -------------------------------------------------------------------
def feature_uret(df):
    """
    Feature'lar, modele "beslediğimiz" sayısal girişlerdir.
    Burada özellikle basit seçiyorum

    - return_1: bugünün getirisi (yüzde değişim)
    - ma_5: 5 günlük ortalama
    - ma_20: 20 günlük ortalama
    - vol_10: son 10 gün getirinin oynaklığı (std)

    Ayrıca iki hedef üretiyoruz:
    - y_reg: yarınki kapanış (regresyon hedefi)
    - y_clf: yarın yükselirse 1, düşerse 0 (sınıflandırma hedefi)
    """

    out = df.copy()

    # 1) Günlük getiri (pct_change)
    #    Örnek: bugün 110, dün 100 ise getiri = 0.10 yani %10
    out["return_1"] = out["Close"].pct_change()

    # 2) Basit hareketli ortalama
    out["ma_5"] = out["Close"].rolling(5).mean()
    out["ma_20"] = out["Close"].rolling(20).mean()

    # 3) Volatilite: getirinin standart sapması
    out["vol_10"] = out["return_1"].rolling(10).std()

    # -------------------------------------------------------------
    # Hedefleri (target) hazırlıyoruz.
    # shift(-1) = "yarının" değeri
    # -------------------------------------------------------------
    out["y_reg"] = out["Close"].shift(-1)  # yarınki kapanış
    out["y_clf"] = (out["Close"].shift(-1) > out["Close"]).astype(int)  # yarın > bugün ise 1

    # Modelde kullanacağımız feature listesi
    features = ["return_1", "ma_5", "ma_20", "vol_10"]

    # Rolling / pct_change / shift sonrası NaN oluşur -> temizliyoruz
    out = out.dropna().copy()

    return out, features


# -------------------------------------------------------------------
# 3) Zaman serisi split: train önce, test sonra
# -------------------------------------------------------------------
def zaman_split(df, test_oran=0.2):
    """
    Borsada random split çoğu zaman yanlış olur,
    çünkü geleceği geçmişle karıştırırsın.

    Bu yüzden:
    - İlk %80 -> train
    - Son  %20 -> test
    """
    n = len(df)
    cut = int(n * (1 - test_oran))
    train = df.iloc[:cut].copy()
    test = df.iloc[cut:].copy()
    return train, test


# -------------------------------------------------------------------
# 4) REGRESYON: yarınki kapanışı tahmin et
# -------------------------------------------------------------------
def regresyon_ornegi(train, test, features):
    """
    Burada çok temel LinearRegression kullanıyoruz.
    Hedef: y_reg (yarınki kapanış)

    Not:
    - Bu 'mükemmel tahmin' dersi değil.
    - Amaç: ML mantığını borsaya bağlamak.
    """

    X_train = train[features]
    y_train = train["y_reg"]

    X_test = test[features]
    y_test = test["y_reg"]


    # Pipeline demek: "önce scaler çalışsın, sonra model"
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LinearRegression())
    ])

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)

    print("\n================ REGRESYON ================")
    print("Amaç: Yarınki kapanışı tahmin etmek (sayısal).")
    print(f"MAE (ortalama mutlak hata): {mae:.4f}")

    # Basit çizim: gerçek vs tahmin
    plt.figure()
    plt.plot(test.index, y_test.values, label="Gerçek (yarın kapanış)")
    plt.plot(test.index, preds, label="Tahmin")
    plt.title("Regresyon: Yarınki Kapanış (Gerçek vs Tahmin)")
    plt.legend()
    plt.tight_layout()
    plt.show()


# -------------------------------------------------------------------
# 5) SINIFLANDIRMA: yarın yükselir mi?
# -------------------------------------------------------------------
def siniflandirma_ornegi(train, test, features):
    """
    Burada hedefimiz 0/1:
    - 1 -> yarın kapanış > bugün kapanış (yükseliş)
    - 0 -> değilse

    Model: LogisticRegression
    Çıktı: olasılık (0 ile 1 arasında)
    """

    X_train = train[features]
    y_train = train["y_clf"]

    X_test = test[features]
    y_test = test["y_clf"]

    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("logreg", LogisticRegression(max_iter=300))
    ])

    clf.fit(X_train, y_train)

    # predict_proba -> "1 sınıfının olasılığı"
    proba_up = clf.predict_proba(X_test)[:, 1]
    pred = (proba_up >= 0.5).astype(int)

    acc = accuracy_score(y_test, pred)
    auc = roc_auc_score(y_test, proba_up)

    print("\n============= SINIFLANDIRMA =============")
    print("Amaç: Yarın yükselir mi? (0/1).")
    print(f"Accuracy: {acc:.4f}")
    print(f"ROC-AUC : {auc:.4f}")

    plt.figure()
    plt.plot(test.index, proba_up)
    plt.title("Sınıflandırma: Yarın Yükselme Olasılığı")
    plt.ylabel("P(yarın yükselir)")
    plt.tight_layout()
    plt.show()


# -------------------------------------------------------------------
# 6) KÜMELEME: etiket yok, günleri grupla
# -------------------------------------------------------------------
def kumeleme_ornegi(df, features, k=3):
    """
    Kümelemede hedef yok.
    Biz sadece "benzer günleri" gruplamak istiyoruz.

    En basit yaklaşım:
    - KMeans ile k tane grup oluştur
    - Sonra bu gruplar hangi günlere denk geliyor bak
    """

    X = df[features].copy()

    km = Pipeline([
        ("scaler", StandardScaler()),
        ("kmeans", KMeans(n_clusters=k, n_init=10, random_state=42))
    ])

    labels = km.fit_predict(X)

    out = df.copy()
    out["cluster"] = labels

    print("\n=============== KÜMELEME ================")
    print(f"Amaç: Günleri {k} gruba ayırmak (etiketsiz).")
    print("Küme dağılımı (kaç gün hangi kümede):")
    print(out["cluster"].value_counts().sort_index())

    # Görsel için iki basit eksen seçelim: return_1 ve vol_10
    plt.figure()
    plt.scatter(out["return_1"], out["vol_10"], c=out["cluster"])
    plt.title("Kümeleme: Günler (return_1 vs vol_10)")
    plt.xlabel("return_1")
    plt.ylabel("vol_10")
    plt.tight_layout()
    plt.show()

    return out


# -------------------------------------------------------------------
# 7) PCA: boyut azaltma (2D çizim)
# -------------------------------------------------------------------
def pca_ornegi(df, features):
    """
    PCA şunu yapar:
    - 4 feature'ı (return_1, ma_5, ma_20, vol_10) alır
    - bilgiyi mümkün olduğunca koruyarak 2 boyuta sıkıştırır
    - biz de 2D grafikte görürüz

    Bu, "veri görselleştirme" anlatırken çok işe yarar.
    """

    X = df[features].copy()

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=2, random_state=42))
    ])

    X2 = pipe.fit_transform(X)

    plt.figure()
    renk = df["cluster"] if "cluster" in df.columns else None
    plt.scatter(X2[:, 0], X2[:, 1], c=renk)
    plt.title("PCA: Feature'ları 2 boyuta indirip çiziyoruz")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.tight_layout()
    plt.show()


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    # BIST örnekleri: "THYAO.IS", "ASELS.IS", "KCHOL.IS", "SISE.IS"
    ticker = "THYAO.IS"

    df, kaynak = veri_cek(ticker=ticker, start="2020-01-01")
    print(f"\nVeri kaynağı: {kaynak} | Satır sayısı: {len(df)}")

    df_feat, features = feature_uret(df)
    train, test = zaman_split(df_feat, test_oran=0.2)

    regresyon_ornegi(train, test, features)
    siniflandirma_ornegi(train, test, features)

    df_cluster = kumeleme_ornegi(df_feat, features, k=3)
    pca_ornegi(df_cluster, features)


if __name__ == "__main__":
    main()
