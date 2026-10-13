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

# ==========================================
# 🐺 MASTER YOUSEF RAILWAY ULTIMATE
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN", "").strip()

RAILWAY_API = "https://backboard.railway.com/graphql/v2"

CHANNEL = "https://t.me/vpnstan1"
SUPPORT = "https://t.me/SultanOfWolf"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

log = logging.getLogger("MASTER_YOUSEF")


# ==========================================
# 🔐 SECURITY
# ==========================================

def is_admin(user_id: int) -> bool:
    return ADMIN_ID.isdigit() and user_id == int(ADMIN_ID)


# ==========================================
# 🚄 RAILWAY API
# ==========================================

async def railway_request(query: str, variables=None):
    if not RAILWAY_API_TOKEN:
        raise RuntimeError(
            "متغیر RAILWAY_API_TOKEN در Railway تنظیم نشده است."
        )

    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {"query": query}

    if variables is not None:
        payload["variables"] = variables

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            RAILWAY_API,
            headers=headers,
            json=payload,
        )

    if response.status_code in (401, 403):
        raise RuntimeError(
            "توکن Railway معتبر نیست یا اجازهٔ دسترسی ندارد."
        )

    response.raise_for_status()
    result = response.json()

    if result.get("errors"):
        errors = result["errors"]
        message = errors[0].get("message", "خطای نامشخص API")
        raise RuntimeError(message[:500])

    if "data" not in result or result["data"] is None:
        raise RuntimeError("پاسخ معتبری از Railway دریافت نشد.")

    return result["data"]


async def get_account():
    query = """
    query {
        me {
            id
            name
            email
        }
    }
    """
    data = await railway_request(query)
    return data["me"]


async def get_projects():
    query = """
    query {
        projects {
            edges {
                node {
                    id
                    name
                    description
                }
            }
        }
    }
    """

    data = await railway_request(query)

    return [
        edge["node"]
        for edge in data["projects"]["edges"]
    ]


async def create_project(name: str):
    query = """
    mutation projectCreate($input: ProjectCreateInput!) {
        projectCreate(input: $input) {
            id
            name
        }
    }
    """

    variables = {
        "input": {
            "name": name,
        }
    }

    data = await railway_request(query, variables)

    return data["projectCreate"]


async def get_project_details(project_id: str):
    query = """
    query project($id: String!) {
        project(id: $id) {
            id
            name
            description

            services {
                edges {
                    node {
                        id
                        name
                    }
                }
            }

            environments {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """

    data = await railway_request(
        query,
        {"id": project_id},
    )

    return data["project"]


# ==========================================
# 🎨 MAIN MENU
# ==========================================

def main_keyboard(user_id: int):
    rows = [
        [
            InlineKeyboardButton(
                "🔑 اتصال Railway",
                callback_data="connect",
            ),
            InlineKeyboardButton(
                "📦 پروژه‌های من",
                callback_data="projects",
            ),
        ],
        [
            InlineKeyboardButton(
                "🚀 ساخت پروژه",
                callback_data="create",
            ),
            InlineKeyboardButton(
                "📊 داشبورد",
                callback_data="dashboard",
            ),
        ],
        [
            InlineKeyboardButton(
                "🛠 پشتیبانی",
                url=SUPPORT,
            ),
            InlineKeyboardButton(
                "📢 کانال",
                url=CHANNEL,
            ),
        ],
    ]

    if is_admin(user_id):
        rows.append([
            InlineKeyboardButton(
                "👑 پنل مدیریت",
                callback_data="admin",
            )
        ])

    return InlineKeyboardMarkup(rows)


def back_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home",
            )
        ]
    ])


async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    text = (
        "🐺 MASTER YOUSEF\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "👑 به پنل حرفه‌ای Railway خوش اومدی!\n\n"
        "🚀 مدیریت پروژه‌ها\n"
        "📦 ساخت پروژه جدید\n"
        "📊 داشبورد حساب\n"
        "🔑 بررسی اتصال Railway\n"
        "🛠 پشتیبانی مستقیم\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {user.first_name}\n"
        "💎 نسخه: ULTIMATE\n"
        "🟢 وضعیت: آنلاین\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=main_keyboard(user.id),
        )
    else:
        await update.effective_message.reply_text(
            text,
            reply_markup=main_keyboard(user.id),
        )


# ==========================================
# 🚀 START
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting_project_name", None)
    await show_home(update, context)


# ==========================================
# 🔘 BUTTON HANDLER
# ==========================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data

    if action == "home":
        context.user_data.pop("awaiting_project_name", None)
        await show_home(update, context)
        return

    # همه عملیات مدیریتی Railway فقط برای ادمین
    protected = {
        "connect",
        "projects",
        "create",
        "dashboard",
        "admin",
    }

    if action in protected and not is_admin(user_id):
        await query.edit_message_text(
            "🔒 این قابلیت فقط برای مدیر ربات فعاله.",
            reply_markup=back_keyboard(),
        )
        return

    # اتصال واقعی: بررسی توکن حساب
    if action == "connect":
        try:
            account = await get_account()

            name = account.get("name") or "بدون نام"
            email = account.get("email") or "ثبت نشده"

            text = (
                "🟢 اتصال Railway موفق بود!\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 نام حساب: {name}\n"
                f"📧 ایمیل: {email}\n\n"
                "🔐 توکن در متغیر محرمانهٔ سرور نگهداری می‌شود."
            )

        except Exception as exc:
            log.warning("Railway connection failed: %s", exc)

            text = (
                "🔴 اتصال Railway ناموفق بود.\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"❌ علت: {str(exc)[:400]}\n\n"
                "متغیر RAILWAY_API_TOKEN و دسترسی توکن را بررسی کن."
            )

        await query.edit_message_text(
            text,
            reply_markup=back_keyboard(),
        )
        return

    # فهرست پروژه‌ها
    if action == "projects":
        await query.edit_message_text(
            "⏳ در حال دریافت پروژه‌های Railway..."
        )

        try:
            projects = await get_projects()

            if not projects:
                await query.edit_message_text(
                    "📦 هنوز پروژه‌ای در این حساب پیدا نشد.",
                    reply_markup=back_keyboard(),
                )
                return

            rows = []

            for project in projects[:40]:
                name = project.get("name") or "بدون نام"
                project_id = project["id"]

                rows.append([
                    InlineKeyboardButton(
                        f"📁 {name[:45]}",
                        callback_data=f"proj:{project_id}",
                    )
                ])

            rows.append([
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home",
                )
            ])

            await query.edit_message_text(
                f"📦 پروژه‌های Railway\n\n"
                f"تعداد پروژه‌های دریافتی: {len(projects)}\n"
                "برای مشاهدهٔ جزئیات، یک پروژه را انتخاب کن.",
                reply_markup=InlineKeyboardMarkup(rows),
            )

        except Exception as exc:
            log.warning("Projects request failed: %s", exc)

            await query.edit_message_text(
                "❌ دریافت پروژه‌ها ناموفق بود.\n\n"
                f"{str(exc)[:400]}",
                reply_markup=back_keyboard(),
            )

        return

    # شروع ساخت پروژه
    if action == "create":
        context.user_data["awaiting_project_name"] = True

        await query.edit_message_text(
            "🚀 ساخت پروژه جدید\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "اسم پروژه رو در پیام بعدی بفرست.\n\n"
            "⚠️ هنوز پروژه‌ای ساخته نشده؛ "
            "بعد از ارسال اسم، درخواست ساخت اجرا می‌شود.",
            reply_markup=back_keyboard(),
        )
        return

    # داشبورد حساب
    if action == "dashboard":
        try:
            account = await get_account()
            projects = await get_projects()

            text = (
                "📊 داشبورد Railway\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 حساب: {account.get('name') or 'بدون نام'}\n"
                f"📧 ایمیل: {account.get('email') or 'ثبت نشده'}\n"
                f"📦 تعداد پروژه‌ها: {len(projects)}\n"
                "🟢 وضعیت API: متصل\n"
            )

        except Exception as exc:
            log.warning("Dashboard request failed: %s", exc)

            text = (
                "📊 داشبورد Railway\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "🔴 دریافت اطلاعات حساب ناموفق بود.\n\n"
                f"خطا: {str(exc)[:400]}"
            )

        await query.edit_message_text(
            text,
            reply_markup=back_keyboard(),
        )
        return

    # پنل مدیریت
    if action == "admin":
        await query.edit_message_text(
            "👑 پنل مدیریت MASTER YOUSEF\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🔐 دسترسی مدیر تأیید شد.\n"
            "📦 مشاهدهٔ پروژه‌ها: فعال\n"
            "🚀 ساخت پروژه: فعال\n"
            "📊 اطلاعات حساب: فعال\n\n"
            "برای استفاده از امکانات، از منوی اصلی انتخاب کن.",
            reply_markup=back_keyboard(),
        )
        return

    # جزئیات پروژه
    if action.startswith("proj:"):
        project_id = action.split(":", 1)[1]

        await query.edit_message_text(
            "⏳ در حال دریافت جزئیات پروژه..."
        )

        try:
            project = await get_project_details(project_id)

            if not project:
                await query.edit_message_text(
                    "❌ پروژه پیدا نشد.",
                    reply_markup=back_keyboard(),
                )
                return

            services = project.get("services", {}).get("edges", [])
            environments = project.get("environments", {}).get("edges", [])

            service_names = [
                edge["node"].get("name", "بدون نام")
                for edge in services
            ]

            environment_names = [
                edge["node"].get("name", "بدون نام")
                for edge in environments
            ]

            text = (
                "📁 جزئیات پروژه\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                f"📛 نام: {project.get('name', 'بدون نام')}\n"
                f"🆔 شناسه: {project.get('id')}\n"
                f"📝 توضیحات: {project.get('description') or 'ندارد'}\n\n"
                f"🛠 تعداد سرویس‌ها: {len(service_names)}\n"
                f"🌍 تعداد محیط‌ها: {len(environment_names)}\n\n"
                "🛠 سرویس‌ها:\n"
                + ("\n".join(f"• {name}" for name in service_names[:15])
                   or "• هنوز سرویسی ثبت نشده")
                + "\n\n🌍 محیط‌ها:\n"
                + ("\n".join(f"• {name}" for name in environment_names[:15])
                   or "• محیطی پیدا نشد")
            )

            await query.edit_message_text(
                text[:4000],
                reply_markup=back_keyboard(),
            )

        except Exception as exc:
            log.warning("Project details failed: %s", exc)

            await query.edit_message_text(
                "❌ دریافت جزئیات پروژه ناموفق بود.\n\n"
                f"{str(exc)[:400]}",
                reply_markup=back_keyboard(),
            )

        return


# ==========================================
# 📝 CREATE PROJECT MESSAGE
# ==========================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_project_name"):
        return

    if not is_admin(update.effective_user.id):
        context.user_data.pop("awaiting_project_name", None)
        await update.effective_message.reply_text(
            "🔒 این قابلیت فقط برای مدیر فعاله."
        )
        return

    name = (update.effective_message.text or "").strip()

    if not name or len(name) > 100:
        await update.effective_message.reply_text(
            "❌ اسم پروژه باید بین ۱ تا ۱۰۰ کاراکتر باشد."
        )
        return

    context.user_data.pop("awaiting_project_name", None)

    status = await update.effective_message.reply_text(
        "⏳ درخواست ساخت پروژه ارسال شد..."
    )

    try:
        project = await create_project(name)

        await status.edit_text(
            "🟢 پروژه با موفقیت ساخته شد!\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"📁 نام: {project.get('name')}\n"
            f"🆔 شناسه: {project.get('id')}\n\n"
            "⚠️ پروژه خالی است؛ برای اجرای برنامه باید "
            "یک سرویس و منبع کد به آن اضافه کنی.",
            reply_markup=back_keyboard(),
        )

    except Exception as exc:
        log.warning("Create project failed: %s", exc)

        await status.edit_text(
            "🔴 ساخت پروژه ناموفق بود.\n\n"
            f"❌ علت: {str(exc)[:500]}",
            reply_markup=back_keyboard(),
        )


# ==========================================
# ⚙️ ERROR HANDLER
# ==========================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    log.error(
        "Telegram handler error",
        exc_info=context.error,
    )


# ==========================================
# 🚀 RUN BOT
# ==========================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "متغیر BOT_TOKEN در Railway تعریف نشده است."
        )

    if not ADMIN_ID.isdigit():
        raise RuntimeError(
            "متغیر ADMIN_ID باید شناسهٔ عددی تلگرام مدیر باشد."
        )

    if not RAILWAY_API_TOKEN:
        log.warning(
            "RAILWAY_API_TOKEN تنظیم نشده؛ "
            "امکانات Railway کار نخواهند کرد."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text,
        )
    )

    app.add_error_handler(error_handler)

    print("🐺 MASTER YOUSEF RAILWAY ULTIMATE")
    print("🟢 BOT IS STARTING")
    print("📦 Railway project manager")
    print("🔐 Admin access enabled")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
