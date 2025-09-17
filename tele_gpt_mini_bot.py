#!/usr/bin/env python3
import os, json, time, re, logging
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from telegram import Update, ParseMode, InputFile
from telegram.ext import Updater, CommandHandler, CallbackContext, Filters, MessageHandler

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
CORPUS_TXT = DATA_DIR / "corpus.txt"
MODEL_JSON = DATA_DIR / "model.json"
LOG_FILE = BASE / "bot.log"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mini-textgen")

load_dotenv(BASE / ".env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    print("Isi TELEGRAM_BOT_TOKEN di file .env")
    raise SystemExit(1)

START = "<START>"
END = "<END>"

def tokenize(text: str):
    text = text.lower().strip()
    text = re.sub(r"([,.;:!?()\"'])", r" \1 ", text)
    text = re.sub(r"\s+", " ", text).strip()
    toks = text.split(" ")
    return [t for t in toks if t]

def lines():
    if not CORPUS_TXT.exists():
        return []
    return [ln.strip() for ln in CORPUS_TXT.read_text(encoding="utf-8").splitlines() if ln.strip()]

def save_line(s: str):
    with CORPUS_TXT.open("a", encoding="utf-8") as f:
        f.write(s.strip() + "\n")

def build_markov(corpus_lines, order=2):
    trans = defaultdict(list)
    for ln in corpus_lines:
        toks = [START, START] + tokenize(ln) + [END]
        for i in range(2, len(toks)):
            state = (toks[i-2], toks[i-1])
            nxt = toks[i]
            trans[state].append(nxt)
    model = {}
    for state, outs in trans.items():
        cnt = Counter(outs)
        toks = list(cnt.keys())
        probs = (np.array([cnt[t] for t in toks], dtype=np.float32) / sum(cnt.values())).tolist()
        model[str(state)] = {"tokens": toks, "probs": probs}
    return {"order": 2, "model": model, "size": len(corpus_lines), "ts": int(time.time())}

def save_model(m):
    MODEL_JSON.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")

def load_model():
    if not MODEL_JSON.exists():
        return None
    return json.loads(MODEL_JSON.read_text(encoding="utf-8"))

def generate_text(prompt="", max_tokens=15):
    m = load_model()
    if not m:
        return "Model belum dilatih. Jalankan /train dulu."
    model = m["model"]
    seed = tokenize(prompt) if prompt else []
    w1, w2 = START, START
    if len(seed) >= 2:
        w1, w2 = seed[-2], seed[-1]
    elif len(seed) == 1:
        w1, w2 = START, seed[-1]
    out = []
    for _ in range(max_tokens):
        key = str((w1, w2))
        if key not in model:
            key = str((START, START))
            if key not in model:
                break
        dist = model[key]
        toks, probs = dist["tokens"], np.array(dist["probs"])
        nxt = toks[np.random.choice(len(toks), p=probs)]
        if nxt == END:
            break
        out.append(nxt)
        w1, w2 = w2, nxt
    return " ".join(out)

def start(update: Update, ctx: CallbackContext):
    update.message.reply_text("Halo! Bot text-gen Markov siap. Gunakan /add /train /gen /stats /dump /help")

def add_cmd(update: Update, ctx: CallbackContext):
    args = update.message.text.split(" ", 1)
    if len(args) < 2:
        update.message.reply_text("Gunakan: /add <kalimat>")
        return
    save_line(args[1])
    update.message.reply_text("✅ Ditambahkan ke korpus.")

def train_cmd(update: Update, ctx: CallbackContext):
    corpus = lines()
    if not corpus:
        update.message.reply_text("Korpus kosong. Tambah data dulu.")
        return
    model = build_markov(corpus)
    save_model(model)
    update.message.reply_text(f"✅ Model dilatih. Data: {len(corpus)} baris.")

def gen_cmd(update: Update, ctx: CallbackContext):
    txt = update.message.text.strip().split(" ", 1)
    prompt, length = "", 15
    if len(txt) > 1:
        prompt = txt[1]
    out = generate_text(prompt, max_tokens=length)
    update.message.reply_text(f"➡️ {out}")

def stats_cmd(update: Update, ctx: CallbackContext):
    n = len(lines())
    m = load_model()
    info = f"Model: {m['size']} baris" if m else "Model belum dilatih"
    update.message.reply_text(f"Korpus: {n} baris\n{info}")

def dump_cmd(update: Update, ctx: CallbackContext):
    if CORPUS_TXT.exists():
        update.message.reply_document(InputFile(str(CORPUS_TXT)))
    else:
        update.message.reply_text("Belum ada korpus.")

def fallback_text(update: Update, ctx: CallbackContext):
    msg = update.message.text.strip()
    if len(msg.split()) >= 2:
        save_line(msg)
        update.message.reply_text("📝 Ditambahkan. Jalankan /train untuk update model.")

def main():
    if not CORPUS_TXT.exists():
        sample = [
            "saya suka makan nasi goreng",
            "kamu minum kopi di pagi hari",
            "hidup itu indah kalau kita bersyukur",
            "rajin belajar supaya jadi pintar",
            "kalau ada sumur di ladang boleh kita menumpang mandi",
            "pagi hari cerah sekali",
            "jangan menyerah walau susah",
            "teman sejati selalu menemani",
            "makan ayam goreng sambil minum teh",
            "pergi ke pasar membeli sayur",
            "aku suka membaca buku cerita",
            "belajar setiap hari membuat pintar",
            "kerja keras membawa hasil",
            "sore hari angin berhembus sejuk",
            "hujan turun membasahi bumi",
            "matahari bersinar terang di siang hari",
            "aku ingin jalan jalan ke taman",
            "kamu sedang mendengarkan musik",
            "kita makan bersama di rumah",
            "malam ini bintang bertaburan indah",
        ]
        for s in sample:
            save_line(s)
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_cmd))
    dp.add_handler(CommandHandler("train", train_cmd))
    dp.add_handler(CommandHandler("gen", gen_cmd))
    dp.add_handler(CommandHandler("stats", stats_cmd))
    dp.add_handler(CommandHandler("dump", dump_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, fallback_text))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
