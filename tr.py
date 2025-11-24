from tradingview_ta import TA_Handler, Interval
import pandas as pd
from datetime import datetime

# Hisseler
hisseler = ["GARAN", "AKBNK", "THYAO", "ASELS", "KRDMD", "PETKM", "EREGL"]

veriler = []

for sembol in hisseler:
    try:
        print(f"{sembol} analizi çekiliyor...")

        # TradingView analiz handler
        handler = TA_Handler(
            symbol=sembol,
            screener="turkey",
            exchange="BIST",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()

        # Basit veri kaydı
        veriler.append({
            "Hisse": sembol,
            "Fiyat": analysis.indicators.get("close", 0),
            "RSI": round(analysis.indicators.get("RSI", 0), 2),
            "MACD": round(analysis.indicators.get("MACD.macd", 0), 2),
            "EMA20": round(analysis.indicators.get("EMA20", 0), 2),
            "EMA50": round(analysis.indicators.get("EMA50", 0), 2),
            "Öneri": analysis.summary.get("RECOMMENDATION", "N/A"),
            "Tarih": datetime.now().strftime("%Y-%m-%d")
        })

    except Exception as e:
        print(f"{sembol} hata: {e}")

# Dataframe ve CSV kaydı
df = pd.DataFrame(veriler)
df.to_csv(f"tradingview_analiz_{datetime.now().strftime('%Y%m%d')}.csv", index=False)

print("\n✅ Analiz tamamlandı ve CSV dosyasına kaydedildi.")
print(df)
