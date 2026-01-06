from fastapi import FastAPI, HTTPException, Request
import httpx
import uvicorn
from pydantic import BaseModel
from datetime import datetime

# ================= KONFIGURASI =================
# Ganti dengan data Anda nanti saat deployment
TELEGRAM_TOKEN = "8241929211:AAGEUBrBFIgPuW-9785z3cYLN6WJwVien0g"
CHAT_ID = "7025145364"
WEBHOOK_SECRET = "canislupusfamiliaris" 

app = FastAPI()

# Penyimpanan sementara untuk mencegah sinyal duplikat (Anti-Spam)
# Format: { "SYMBOL_TIMEFRAME": "LAST_SIGNAL" }
last_signals = {}

# Model data yang akan diterima dari TradingView
class SignalPayload(BaseModel):
    symbol: str
    timeframe: str
    signal: str
    price: float
    time: str
    passphrase: str # Security token

@app.get("/")
def home():
    return {"status": "System Online", "message": "TradingView Webhook Ready"}

@app.post("/webhook/tradingview")
async def receive_signal(payload: SignalPayload):
    # 1. KEAMANAN: Validasi Passphrase
    if payload.passphrase != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Akses Ditolak: Token Salah")

    # Kunci unik untuk membedakan emiten & timeframe (Contoh: BBRI_60)
    signal_key = f"{payload.symbol}_{payload.timeframe}"

    # 2. FILTER: Cek Duplikat Sinyal
    # Jika sinyal baru SAMA dengan sinyal terakhir, abaikan.
    if last_signals.get(signal_key) == payload.signal:
        return {"status": "ignored", "reason": "Duplicate signal"}

    # Update sinyal terakhir
    last_signals[signal_key] = payload.signal

    # 3. FORMAT PESAN TELEGRAM
    emoji_sig = "🟢" if payload.signal == "BUY" else "🔴"
    
    # Format Pesan Profesional
    message_text = (
        f"📊 <b>SIGNAL TRADING</b>\n"
        f"──────────────────\n"
        f"📌 <b>Emiten</b>   : {payload.symbol}\n"
        f"⏱ <b>Timeframe</b>: {payload.timeframe}\n"
        f"📈 <b>Signal</b>   : {emoji_sig} <b>{payload.signal}</b>\n"
        f"💰 <b>Harga</b>    : {payload.price}\n"
        f"🕒 <b>Waktu</b>    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB\n"
        f"──────────────────\n"
        f"⚠️ <i>Konfirmasi price action tetap diperlukan.</i>"
    )

    # 4. KIRIM KE TELEGRAM
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(telegram_url, json={
            "chat_id": CHAT_ID,
            "text": message_text,
            "parse_mode": "HTML"
        })

    return {"status": "success", "signal": payload.signal}

# Baris ini hanya untuk menjalankan di komputer lokal
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
