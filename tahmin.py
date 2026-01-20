from tradingview_ta import TA_Handler, Interval
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

ticker = "THYAO"
exchange = "BIST"

handler = TA_Handler(
    symbol=ticker,
    exchange=exchange,
    screener="turkey",
    interval=Interval.INTERVAL_1_DAY
)

veriler = []
for i in range(100):
    try:
        analiz = handler.get_analysis()
        veriler.append({
            'close': analiz.indicators['close'],
            'open': analiz.indicators['open'],
            'high': analiz.indicators['high'],
            'low': analiz.indicators['low']
        })
    except:
        break

df = pd.DataFrame(veriler)

df['Degisim'] = df['close'].pct_change()
df['MA5'] = df['close'].rolling(5).mean()
df['MA20'] = df['close'].rolling(20).mean()
df['RSI'] = 100 - (100 / (1 + df['Degisim'].rolling(14).mean().abs()))
df['Yarin'] = (df['close'].shift(-1) > df['close']).astype(int)
df = df.dropna()

X = df[['Degisim', 'MA5', 'MA20', 'RSI']]
y = df['Yarin']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

tahminler = model.predict(X_test)
dogruluk = model.score(X_test, y_test)

# Grafikler
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Fiyat ve MA
axes[0].plot(df.index, df['close'], label='Fiyat', linewidth=2)
axes[0].plot(df.index, df['MA5'], label='MA5', linestyle='--')
axes[0].plot(df.index, df['MA20'], label='MA20', linestyle='--')
axes[0].set_title(f'{ticker} Fiyat ve Hareketli Ortalamalar')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Tahmin Dogrulugu
test_index = df.index[-len(y_test):]
axes[1].scatter(test_index, y_test, label='Gercek', alpha=0.6, s=50)
axes[1].scatter(test_index, tahminler, label='Tahmin', alpha=0.6, s=50, marker='x')
axes[1].set_title(f'Tahmin vs Gercek (Dogruluk: %{dogruluk*100:.1f})')
axes[1].set_ylabel('0=Kirmizi, 1=Yesil')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(f"\nDogruluk: %{dogruluk*100:.1f}")
tahmin = model.predict(X.iloc[[-1]])[0]
olasilik = model.predict_proba(X.iloc[[-1]])[0]
print(f"Yarin: {'Yesil' if tahmin == 1 else 'Kirmizi'}")
print(f"Olasilik: %{olasilik[tahmin]*100:.1f}")