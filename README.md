# Telegram Mini TextGen Bot

Bot Telegram sederhana berbasis **Markov chain**.
Bisa menambahkan kalimat ke korpus, melatih model, dan generate teks baru.

## 🚀 Cara Jalankan

1. Clone repo
   ```bash
   git clone https://github.com/username/tele_mini_textgen.git
   cd tele_mini_textgen
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Buat file `.env` (salin dari `.env.example`) dan isi token bot dari BotFather.

4. Jalankan bot
   ```bash
   python3 tele_gpt_mini_bot.py
   ```

## 📱 Perintah di Telegram
- `/add kalimat` → tambah kalimat ke korpus
- `/train` → latih model
- `/gen [prompt]` → generate teks baru
- `/stats` → info korpus & model
- `/dump` → download korpus

## 📂 Folder Data
- `data/corpus.txt` → berisi semua kalimat korpus
- `data/model.json` → model hasil training
