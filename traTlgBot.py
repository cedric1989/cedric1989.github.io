from tradingview_ta import TA_Handler, Interval
import requests
import time
from datetime import datetime


class TradingViewTarayici:

    def __init__(self, telegram_token, chat_id):
        self.telegram_token = telegram_token
        self.chat_id = chat_id

    def veri_cek(self, sembol, periyot):
        """TradingView'dan veri çek"""
        max_deneme = 3
        for deneme in range(max_deneme):
            try:
                handler = TA_Handler(
                    symbol=sembol,
                    screener="turkey",
                    exchange="BIST",
                    interval=periyot
                )
                return handler.get_analysis()
            except Exception as e:
                if "429" in str(e):  # Rate limit
                    if deneme < max_deneme - 1:
                        bekle = (deneme + 1) * 5
                        print(f"? {bekle}sn bekle...", end=" ", flush=True)
                        time.sleep(bekle)
                        continue
                print(f"? {e}")
                return None
        return None

    def sinyal_kontrol(self, sembol, periyot):
        """
        SINYAL STRATEJISI - KENDI PINE KODUNUZU BURAYA EKLEYIN
        """
        analiz = self.veri_cek(sembol, periyot)
        if not analiz:
            return None

        ind = analiz.indicators
        ozet = analiz.summary

        # Veriler
        fiyat = ind.get('close', 0)
        rsi = ind.get('RSI', 0)
        sma20 = ind.get('SMA20', 0)
        sma50 = ind.get('SMA50', 0)
        ema20 = ind.get('EMA20', 0)
        macd = ind.get('MACD.macd', 0)
        macd_signal = ind.get('MACD.signal', 0)
        volume = ind.get('volume', 0)

        sinyaller = []

        # ========== BURAYA KENDI STRATEJINIZI YAZIN ==========

        # 1. TradingView Genel Tavsiye
        tavsiye = ozet['RECOMMENDATION']
        if tavsiye in ['STRONG_BUY', 'BUY']:
            sinyaller.append(f"?? TV Tavsiye: {tavsiye}")

        # 2. RSI Stratejisi
        if rsi < 30:
            sinyaller.append(f"?? RSI Asiri Satim: {rsi:.1f}")
        elif rsi > 70:
            sinyaller.append(f"?? RSI Asiri Alim: {rsi:.1f}")

        # 3. Golden/Death Cross
        if sma20 > 0 and sma50 > 0:
            fark_yuzde = abs(sma20 - sma50) / sma50 * 100
            if sma20 > sma50 and fark_yuzde < 1.5:
                sinyaller.append("?? Golden Cross Yakin")
            elif sma20 < sma50 and fark_yuzde < 1.5:
                sinyaller.append("?? Death Cross Yakin")

        # 4. MACD Kesisim
        if macd > macd_signal and abs(macd - macd_signal) < 0.5:
            sinyaller.append("?? MACD Pozitif Kesisim")
        elif macd < macd_signal and abs(macd - macd_signal) < 0.5:
            sinyaller.append("?? MACD Negatif Kesisim")

        # 5. Fiyat ve SMA20 Iliskisi
        if fiyat > sma20 and sma20 > 0:
            fark = (fiyat - sma20) / sma20 * 100
            if 0 < fark < 2:
                sinyaller.append(f"? Fiyat SMA20 Üzerinde (%{fark:.1f})")

        # ====================================================

        if not sinyaller:
            return None

        periyot_map = {
            '1m': '1D', '5m': '5D', '15m': '15D', '1h': '1S',
            '4h': '4S', '1d': 'Günlük', '1W': 'Haftalik', '1M': 'Aylik'
        }
        periyot_adi = periyot_map.get(periyot, periyot)

        return {
            'sembol': sembol,
            'periyot': periyot_adi,
            'fiyat': fiyat,
            'rsi': rsi,
            'sma20': sma20,
            'sma50': sma50,
            'tavsiye': tavsiye,
            'al': ozet['BUY'],
            'sat': ozet['SELL'],
            'notr': ozet['NEUTRAL'],
            'sinyaller': sinyaller
        }

    def telegram_gonder(self, mesaj):
        """Telegram'a gönder"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        try:
            requests.post(url, json={
                "chat_id": self.chat_id,
                "text": mesaj,
                "parse_mode": "HTML"
            }, timeout=10)
        except:
            pass

    def mesaj_olustur(self, s):
        """Mesaj formatla"""
        msg = f"?? <b>{s['sembol']}</b> - {s['periyot']}\n\n"
        msg += f"?? Fiyat: ?{s['fiyat']:.2f}\n"
        msg += f"?? RSI: {s['rsi']:.1f}\n"
        msg += f"?? SMA20: ?{s['sma20']:.2f} | SMA50: ?{s['sma50']:.2f}\n\n"
        msg += f"?? TV: {s['tavsiye']} (AL:{s['al']} SAT:{s['sat']} NÖTR:{s['notr']})\n\n"
        msg += "<b>Sinyaller:</b>\n"
        for sinyal in s['sinyaller']:
            msg += f"  • {sinyal}\n"
        msg += f"\n?? {datetime.now().strftime('%H:%M:%S')}"
        return msg

    def tara(self, hisseler, periyotlar):
        """Ana tarama fonksiyonu"""
        print(f"\n{'=' * 60}")
        print(f"?? TARAMA BASLADI - {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"?? {len(hisseler)} hisse x {len(periyotlar)} periyot")
        print(f"{'=' * 60}\n")

        sinyal_sayisi = 0

        for i, hisse in enumerate(hisseler, 1):
            print(f"[{i:2d}/{len(hisseler)}] {hisse:6s} ? ", end="", flush=True)

            bulunan = []
            for periyot in periyotlar:
                sonuc = self.sinyal_kontrol(hisse, periyot)
                if sonuc:
                    bulunan.append(sonuc)

            if bulunan:
                print(f"? {len(bulunan)} sinyal!")
                sinyal_sayisi += len(bulunan)
                for s in bulunan:
                    self.telegram_gonder(self.mesaj_olustur(s))
                    time.sleep(0.3)
            else:
                print("—")

            time.sleep(3)  # TradingView rate limit (artirildi)

        print(f"\n{'=' * 60}")
        print(f"? Tamamlandi - {sinyal_sayisi} sinyal bulundu")
        print(f"{'=' * 60}\n")


# ======================== KULLANIM ========================

if __name__ == "__main__":
    # TELEGRAM AYARLARI
    TELEGRAM_TOKEN = ""
    CHAT_ID = ""

    # Tarayiciyi baslat
    t = TradingViewTarayici(TELEGRAM_TOKEN, CHAT_ID)

    # Taranacak hisseler (2 hisse)
    hisseler = [
        'THYAO', 'TUPRS'
    ]

    # Taranacak periyotlar
    periyotlar = [
        Interval.INTERVAL_1_DAY,  # Günlük
        Interval.INTERVAL_1_WEEK,  # Haftalik
        # Interval.INTERVAL_4_HOURS,  # 4 Saat
        # Interval.INTERVAL_1_HOUR,   # 1 Saat
        # Interval.INTERVAL_15_MINUTES # 15 Dakika
    ]

    # TEK TARAMA
    t.tara(hisseler, periyotlar)

    # SÜREKLI TARAMA (10 dakikada bir)
    # while True:
    #     t.tara(hisseler, periyotlar)
    #     print("? 10 dakika bekleniyor...\n")
    #     time.sleep(600)