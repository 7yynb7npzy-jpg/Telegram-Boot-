import base64
import io
import logging
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

# تم وضع التوكن الخاص بك هنا
BOT_TOKEN = "8878295509:AAEZ_DyIZu5JQMChlB-5ea4cNVAODRkId3A"
API_BASE = "https://waledpro.com/api/tunnel"
API_KEY = "by-telegram@waledpro"
CHANNEL = "https://t.me/waledpro"

APPS = [
    ("mnr", "MNR TUNNEL PLUS"),
    ("abo", "AboWaged VPN"),
    ("hamo", "Hamo Tunnel Plus"),
    ("hat", "HA Tunnel Plus (.hat)"),
    ("apna", "APNA Tunnel Lite"),
    ("mx", "Mx Tunnel PRO"),
    ("mtm", "MTM Tunnel Lite"),
    ("fx", "Fx Tunnel"),
    ("trm", "TRM Tunnel"),
    ("tss", "TSS Tunnel"),
    ("oc", "Open Custom"),
    ("wolf", "Wolf Custom VPN"),
]

HEADERS = {
    "Content-Type": "application/json",
    "x-app-version": "1.9.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
}


async def async_api_call(path: str, payload: dict, timeout: float = 120.0):
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(API_BASE + path, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()


def main_kb():
    rows = [[InlineKeyboardButton("🔓 " + title, callback_data="tun_" + key)] for key, title in APPS]
    rows.append([InlineKeyboardButton("📢 قناتنا", url=CHANNEL)])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧩 <b>بوت فك تطبيقات التانل</b>\n\nاختر التطبيق:",
        reply_markup=main_kb(),
        parse_mode="HTML",
    )


async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "🧩 <b>اختر التطبيق:</b>", reply_markup=main_kb(), parse_mode="HTML"
    )


async def app_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q.data.startswith("tun_"):
        return
    key = q.data[4:]
    if key == "menu":
        return

    title = dict(APPS).get(key, key)
    await q.answer()

    if key == "hat":
        ctx.user_data["wait_hat"] = True
        await q.message.edit_text(
            "🧵 <b>HA Tunnel Plus</b>\n\nابعت ملف الـ <code>.hat</code> وسوف أبدأ الفك فوراً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tun_menu")]]),
            parse_mode="HTML",
        )
        return

    msg = await q.message.edit_text(f"⏳ جاري الفك على السيرفر: <b>{title}</b>...", parse_mode="HTML")
    try:
        payload = await async_api_call("/decrypt", {"key": API_KEY, "app": key})
        if not payload.get("ok"):
            raise RuntimeError(payload.get("error", "خطأ غير معروف من السيرفر"))

        data = payload["data"]
        await q.message.reply_document(
            document=io.BytesIO(base64.b64decode(data["zip"])),
            filename=f"{data.get('name', key)}.zip",
            caption=f"✅ <b>{title} مفكوك بنجاح!</b>\n📌 الإصدار: <code>{data.get('version', '?')}</code>\n\n📢 @waledpro",
            parse_mode="HTML",
            reply_markup=main_kb(),
        )
        try:
            await msg.delete()
        except Exception:
            pass
    except Exception as e:
        log.error("decrypt %s failed: %s", key, e)
        await msg.edit_text(f"❌ فشل الفك: {str(e)[:150]}", reply_markup=main_kb())


async def hat_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("wait_hat"):
        return

    doc = update.message.document
    if doc.file_name and not doc.file_name.lower().endswith(".hat"):
        await update.message.reply_text("⚠️ يرجى إرسال ملف بصيغة <code>.hat</code> فقط.", parse_mode="HTML")
        return

    ctx.user_data["wait_hat"] = False
    msg = await update.message.reply_text("🔓 تم استلام الملف... جاري الفك ⏳")

    try:
        f = await doc.get_file()
        raw = bytes(await f.download_as_bytearray())
        payload = await async_api_call(
            "/decrypt_hat",
            {"key": API_KEY, "file": base64.b64encode(raw).decode()},
        )
        if not payload.get("ok"):
            raise RuntimeError(payload.get("error", "خطأ غير معروف من السيرفر"))

        data = payload["data"]
        await update.message.reply_document(
            document=io.BytesIO(base64.b64decode(data["zip"])),
            filename="HA_Tunnel_Plus_hat.zip",
            caption="✅ <b>تم فك ملف HA Tunnel Plus بنجاح!</b>\n\n📢 @waledpro",
            parse_mode="HTML",
            reply_markup=main_kb(),
        )
        try:
            await msg.delete()
        except Exception:
            pass
    except Exception as e:
        log.error("hat failed: %s", e)
        await msg.edit_text(f"❌ فشل الفك: {str(e)[:150]}", reply_markup=main_kb())


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu, pattern="^tun_menu$"))
    app.add_handler(CallbackQueryHandler(app_cb, pattern="^tun_"))
    app.add_handler(MessageHandler(filters.Document.ALL, hat_file))

    log.info("tunnel bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
