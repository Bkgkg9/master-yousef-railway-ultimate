import os
import logging
import httpx

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# MASTER YOUSEF ULTIMATE
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

SUPPORT_USERNAME = "SultanOfWolf"
SUPPORT_URL = "https://t.me/SultanOfWolf"

CHANNEL_USERNAME = "@vpnstan1"
CHANNEL_URL = "https://t.me/vpnstan1"

RAILWAY_API = "https://backboard.railway.com/graphql/v2"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logging.getLogger("httpx").setLevel(logging.WARNING)

# اطلاعات کاربران فقط در حافظه موقت نگهداری می‌شود.
user_tokens = {}
user_states = {}
user_projects = {}


# ==============================
# KEYBOARDS
# ==============================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔑 اتصال Railway",
                callback_data="connect",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 پروژه‌های من",
                callback_data="projects",
            ),
            InlineKeyboardButton(
                "➕ ساخت پروژه",
                callback_data="create",
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 داشبورد",
                callback_data="dashboard",
            ),
        ],
        [
            InlineKeyboardButton(
                "🛠 پشتیبانی",
                url=SUPPORT_URL,
            ),
            InlineKeyboardButton(
                "📢 کانال ما",
                url=CHANNEL_URL,
            ),
        ],
        [
            InlineKeyboardButton(
                "📚 راهنما",
                callback_data="help",
            ),
            InlineKeyboardButton(
                "🔌 قطع اتصال",
                callback_data="disconnect",
            ),
        ],
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home",
            ),
        ],
        [
            InlineKeyboardButton(
                "🛠 پشتیبانی",
                url=SUPPORT_URL,
            ),
            InlineKeyboardButton(
                "📢 کانال",
                url=CHANNEL_URL,
            ),
        ],
    ])


# ==============================
# RAILWAY API
# ==============================

async def railway_request(token, query, variables=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            RAILWAY_API,
            headers=headers,
            json={
                "query": query,
                "variables": variables or {},
            },
        )

        response.raise_for_status()
        result = response.json()

    if result.get("errors"):
        raise ValueError(
            result["errors"][0].get(
                "message",
                "Railway API error",
            )
        )

    return result.get("data", {})


# ==============================
# START
# ==============================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    text = (
        "🐺 MASTER YOUSEF\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "👑 به پنل حرفه‌ای Railway خوش اومدی!\n\n"
        "🚀 مدیریت پروژه‌ها\n"
        "📦 ساخت پروژه جدید\n"
        "📊 داشبورد اختصاصی\n"
        "🔑 اتصال حساب Railway\n"
        "🛠 پشتیبانی مستقیم\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {user.first_name}\n"
        "💎 نسخه: ULTIMATE\n"
        "🟢 وضعیت: آنلاین\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن."
    )

    await update.effective_message.reply_text(
        text,
        reply_markup=main_menu(),
    )


# ==============================
# HELP
# ==============================

async def show_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = (
        "📚 راهنمای MASTER YOUSEF\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔑 اتصال Railway:\n"
        "حساب Railway خودت رو متصل کن.\n\n"
        "📦 پروژه‌های من:\n"
        "پروژه‌های قابل‌دسترسی رو مشاهده کن.\n\n"
        "➕ ساخت پروژه:\n"
        "یک پروژه جدید ایجاد کن.\n\n"
        "📊 داشبورد:\n"
        "اطلاعات اتصال و پروژه‌ها رو ببین.\n\n"
        "🛠 پشتیبانی:\n"
        f"@{SUPPORT_USERNAME}\n\n"
        "📢 کانال:\n"
        f"{CHANNEL_USERNAME}\n\n"
        "🐺 سازنده: MASTER YOUSEF"
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=back_menu(),
    )


# ==============================
# BUTTON HANDLER
# ==============================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    action = query.data

    if action == "home":
        await query.edit_message_text(
            "🐺 MASTER YOUSEF ULTIMATE\n\n"
            "به پنل اصلی خوش اومدی!",
            reply_markup=main_menu(),
        )
        return

    if action == "help":
        await show_help(update, context)
        return

    if action == "connect":
        user_states[uid] = "waiting_token"

        await query.edit_message_text(
            "🔑 اتصال Railway\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "برای اتصال، روش امن احراز هویت Railway "
            "را در مراحل بعدی تنظیم می‌کنیم.\n\n"
            "فعلاً توکن محرمانه‌ات را داخل تلگرام "
            "برای ربات ارسال نکن.\n\n"
            "برای بازگشت به منوی اصلی دکمه زیر را بزن.",
            reply_markup=back_menu(),
        )

        user_states.pop(uid, None)
        return

    if action == "disconnect":
        user_tokens.pop(uid, None)
        user_projects.pop(uid, None)
        user_states.pop(uid, None)

        await query.edit_message_text(
            "🔌 اطلاعات اتصال موقت حذف شد.",
            reply_markup=back_menu(),
        )
        return

    if action == "projects":
        token = user_tokens.get(uid)

        if not token:
            await query.edit_message_text(
                "📦 پروژه‌های من\n\n"
                "هنوز حساب Railway متصل نشده است.\n"
                "اتصال حساب در نسخه بعدی فعال می‌شود.",
                reply_markup=back_menu(),
            )
            return

        await query.edit_message_text(
            "⏳ در حال دریافت پروژه‌ها...",
        )

        try:
            data = await railway_request(
                token,
                """
                query {
                    projects {
                        edges {
                            node {
                                id
                                name
                            }
                        }
                    }
                }
                """,
            )

            edges = data.get(
                "projects", {}
            ).get("edges", [])

            if not edges:
                text = "📦 پروژه‌ای پیدا نشد."
            else:
                text = "📦 پروژه‌های شما\n\n"

                for index, item in enumerate(
                    edges[:20],
                    start=1,
                ):
                    project = item["node"]
                    text += (
                        f"{index}. {project.get('name', 'بدون نام')}\n"
                        f"🆔 {project.get('id', '')}\n\n"
                    )

                user_projects[uid] = [
                    item["node"] for item in edges
                ]

            await query.edit_message_text(
                text[:4000],
                reply_markup=back_menu(),
            )

        except Exception:
            logging.exception("Project list failed")

            await query.edit_message_text(
                "❌ دریافت پروژه‌ها ناموفق بود.",
                reply_markup=back_menu(),
            )

        return

    if action == "create":
        await query.edit_message_text(
            "➕ ساخت پروژه\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "قابلیت ساخت پروژه بعد از تنظیم امن اتصال "
            "و مجوزهای Railway فعال می‌شود.\n\n"
            "🐺 MASTER YOUSEF",
            reply_markup=back_menu(),
        )
        return

    if action == "dashboard":
        await query.edit_message_text(
            "📊 داشبورد اختصاصی\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🐺 MASTER YOUSEF\n"
            "🔑 وضعیت اتصال: متصل نشده\n"
            f"🛠 پشتیبانی: @{SUPPORT_USERNAME}\n"
            f"📢 کانال: {CHANNEL_USERNAME}\n\n"
            "برای اتصال حساب، ابتدا روش احراز هویت "
            "را تنظیم می‌کنیم.",
            reply_markup=back_menu(),
        )
        return


# ==============================
# ADMIN
# ==============================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not ADMIN_ID or update.effective_user.id != ADMIN_ID:
        await update.effective_message.reply_text(
            "⛔ این دستور مخصوص مدیر ربات است."
        )
        return

    await update.effective_message.reply_text(
        "👑 MASTER YOUSEF ADMIN\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 کاربران دارای اتصال موقت: {len(user_tokens)}\n"
        f"📦 کاربران دارای پروژه در حافظه: {len(user_projects)}\n"
        f"🛠 پشتیبانی: @{SUPPORT_USERNAME}\n"
        f"📢 کانال: {CHANNEL_USERNAME}"
    )


# ==============================
# ERROR HANDLER
# ==============================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logging.error(
        "خطای ربات: %s",
        context.error,
    )


# ==============================
# MAIN
# ==============================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN در متغیرهای محیطی تعریف نشده است."
        )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin_command)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_error_handler(error_handler)

    print("🐺 MASTER YOUSEF ULTIMATE")
    print("🟢 BOT IS ONLINE")
    print(f"🛠 SUPPORT: @{SUPPORT_USERNAME}")
    print(f"📢 CHANNEL: {CHANNEL_USERNAME}")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
