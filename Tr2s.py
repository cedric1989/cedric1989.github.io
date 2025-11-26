from tradingview_ta import TA_Handler
import time

# Ayarlar
symbol = "THYAO"  # Hisse kodu
exchange = "BIST"
interval = "15m"  # 15 dakikalık analiz


def bist_analiz():
    try:
        tv = TA_Handler(
            symbol=symbol,
            screener="turkey",
            exchange=exchange,
            interval=interval
        )

        analysis = tv.get_analysis()

        summary = analysis.summary
        oscillators = analysis.oscillators["COMPUTE"]
        ma = analysis.moving_averages["COMPUTE"]

        print("\n======================================")
        print(f"Hisse: {symbol} - Zaman Dilimi: {interval}")
        print("======================================")
        print("Genel Karar:", summary["RECOMMENDATION"])
        print("Buy:", summary["BUY"], "Sell:", summary["SELL"], "Neutral:", summary["NEUTRAL"])

        print("\nOsilatörler:")
        for key, value in oscillators.items():
            print(key, ":", value)

        print("\nHareketli Ortalamalar:")
        for key, value in ma.items():
            print(key, ":", value)

        # Basit sinyal
        karar = summary["RECOMMENDATION"]
        if karar in ["STRONG_BUY", "BUY"]:
            print("Sinyal: AL")
        elif karar in ["STRONG_SELL", "SELL"]:
            print("Sinyal: SAT")
        else:
            print("Sinyal: BEKLE")

    except Exception as e:
        print("Hata:", e)


# Döngü
while True:
    bist_analiz()
    time.sleep(20)
