import requests
import pandas as pd
from datetime import datetime
import time

# Hisseler
hisseler = ['THYAO', 'SAHOL', 'EREGL', 'TUPRS', 'AKBNK']


def veri_cek(sembol):
    """Yahoo Finance'dan veri çek"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sembol}.IS?interval=1d&range=1mo"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()['chart']['result'][0]

        timestamps = data['timestamp']
        q = data['indicators']['quote'][0]

        df = pd.DataFrame({
            'Tarih': [datetime.fromtimestamp(t).strftime('%Y-%m-%d') for t in timestamps],
            'Sembol': sembol,
            'Acilis': q['open'],
            'Yuksek': q['high'],
            'Dusuk': q['low'],
            'Kapanis': q['close'],
            'Hacim': q['volume']
        }).dropna()

        # Para akisi = ((H+L+C)/3) * Hacim
        df['Para_Akisi'] = (((df['Yuksek'] + df['Dusuk'] + df['Kapanis']) / 3) * df['Hacim']).round(0)

        print(f"? {sembol} - {len(df)} veri")
        return df
    except:
        print(f"? {sembol} HATA")
        return None


# Ana kod
print("?? Basladi...\n")
tum_veri = []

for sembol in hisseler:
    df = veri_cek(sembol)
    if df is not None:
        tum_veri.append(df)
    time.sleep(2)

# Kaydet
dosya = f"hisse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
pd.concat(tum_veri).to_csv(dosya, index=False, encoding='utf-8-sig')

print(f"\n?? {dosya} kaydedildi!")

