import telebot
from telebot import types
import PyPDF2
import random
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

foydalanuvchi_holati = {}

def pdfdan_savollar_olish(pdf_fayl):
    matn = ""
    with open(pdf_fayl, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for sahifa in reader.pages:
            matn += sahifa.extract_text()
    qismlar = matn.split("Javob:")
    savollar_va_javoblar = []
    for i in range(len(qismlar) - 1):
        savol_qismi = qismlar[i].strip()
        satrlar = [s for s in savol_qismi.splitlines() if s.strip()]
        savol = "\n".join(satrlar[-3:])
        javob = qismlar[i + 1].split("\n")[0].strip()
        savollar_va_javoblar.append((savol, javob))
    return savollar_va_javoblar

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "👋 Assalomu alaykum!\n"
        "PDF-dan quizz yaratadigan bot.\n\n"
        "Menga PDF fayl yuboring (formatda: 'Javob:' bilan).")

@bot.message_handler(content_types=['document'])
def pdf_qabul(message):
    if message.document.mime_type != 'application/pdf':
        bot.send_message(message.chat.id, "⚠️ Faqat PDF fayl yuboring.")
        return
    fayl = bot.get_file(message.document.file_id)
    yuklangan = bot.download_file(fayl.file_path)
    pdf_nom = f"{message.chat.id}_quiz.pdf"
    with open(pdf_nom, "wb") as f:
        f.write(yuklangan)
    savollar = pdfdan_savollar_olish(pdf_nom)
    if not savollar:
        bot.send_message(message.chat.id, "❌ 'Javob:' formatidagi savollar topilmadi.")
        return
    foydalanuvchi_holati[message.chat.id] = {"savollar": savollar, "index": 0, "togri": 0}
    bot.send_message(message.chat.id, "✅ Quiz yuklandi! Boshlaymiz...")
    savol_yuborish(message.chat.id)

def savol_yuborish(chat_id):
    holat = foydalanuvchi_holati.get(chat_id)
    if not holat:
        return
    if holat["index"] < len(holat["savollar"]):
        savol, togri_javob = holat["savollar"][holat["index"]]
        variantlar = [togri_javob]
        boshqa = [j for _, j in holat["savollar"] if j != togri_javob]
        if len(boshqa) >= 3:
            variantlar += random.sample(boshqa, 3)
        random.shuffle(variantlar)
        markup = types.InlineKeyboardMarkup()
        for v in variantlar:
            markup.add(types.InlineKeyboardButton(v, callback_data=v))
        bot.send_message(chat_id, f"🧠 Savol {holat['index'] + 1}:\n{savol}", reply_markup=markup)
    else:
        jami = len(holat["savollar"])
        togri = holat["togri"]
        bot.send_message(chat_id, f"🏁 Test yakunlandi!\nTo‘g‘ri javoblar: {togri}/{jami}")
        del foydalanuvchi_holati[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def javobni_tekshirish(call):
    chat_id = call.message.chat.id
    holat = foydalanuvchi_holati.get(chat_id)
    if not holat:
        bot.answer_callback_query(call.id, "⚠️ Avval PDF yuboring.")
        return
    savol, togri_javob = holat["savollar"][holat["index"]]
    tanlangan = call.data
    if tanlangan == togri_javob:
        holat["togri"] += 1
        bot.answer_callback_query(call.id, "✅ To‘g‘ri!")
    else:
        bot.answer_callback_query(call.id, f"❌ Noto‘g‘ri. To‘g‘ri javob: {togri_javob}")
    holat["index"] += 1
    savol_yuborish(chat_id)

bot.infinity_polling()

