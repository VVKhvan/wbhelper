
import logging
import requests
from PIL import Image
from io import BytesIO
from transformers import BlipProcessor, BlipForConditionalGeneration
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

TOKEN = "7679013213:AAE3D5_P4HDtwQhlc7oUXNwJiSzZICE4ht8"

logging.basicConfig(level=logging.INFO)

def generate_caption(image: Image.Image) -> str:
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

def search_wildberries(query: str):
    url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?query={query}&resultset=catalog"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        cards = data.get("data", {}).get("products", [])
        results = []
        for item in cards[:3]:
            name = item.get("name")
            id_ = item.get("id")
            link = f"https://www.wildberries.ru/catalog/{id_}/detail.aspx"
            results.append(f"{name}\n{link}")
        return results if results else ["Ничего не найдено 😔"]
    except Exception as e:
        return [f"Ошибка поиска: {e}"]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    image_bytes = await photo_file.download_as_bytearray()
    image = Image.open(BytesIO(image_bytes)).convert('RGB')

    await update.message.reply_text("🔍 Анализирую изображение...")

    description = generate_caption(image)
    await update.message.reply_text(f"🧠 Похоже, это: *{description}*", parse_mode='Markdown')

    results = search_wildberries(description)
    for res in results:
        await update.message.reply_text(res)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне фото товара, и я найду его на Wildberries 📦")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
