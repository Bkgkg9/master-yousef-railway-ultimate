import os
import logging
import httpx

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# MASTER YOUSEF RAILWAY ULTIMATE
# ==============================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN", "").strip()

API_URL = "https://backboard.railway.com/graphql/v2"

MENU = ReplyKeyboardMarkup(
    [
        ["🔑 اتصال Railway", "📦 پروژه‌های من"],
        ["🚀 ساخت پروژه", "📊 داشبورد"],
        ["🛠 پشتیبانی", "📢 کانال"],
    ],
    resize_keyboard=True,
)


# ==============================
# RAILWAY API
# ==============================

async def railway_request(query, variables=None):
    if not RAILWAY_API_TOKEN:
        raise RuntimeError(
            "متغیر RAILWAY_API_TOKEN تنظیم نشده است."
        )

    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            API_URL,
            headers=headers,
            json={
                "query": query,
                "variables": variables or {},
            },
        )

    response.raise_for_status()
    result = response.json()

    if result.get("errors"):
        errors = result["errors"]
        message = "\n".join(
            error.get("message", "خطای نامشخص")
            for error in errors
        )
        raise RuntimeError(message)

    return result.get("data") or {}


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
    return data.get("me") or {}


async def get_workspaces():
    query = """
    query {
        me {
            workspaces {
                id
                name
            }
        }
    }
    """

    data = await railway_request(query)
    account = data.get("me") or {}

    return account.get("workspaces") or []


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
    projects = data.get("projects") or {}

    return [
        edge["node"]
        for edge in projects.get("edges", [])
        if edge.get("node")
    ]


async def create_project(name, workspace_id):
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
            "teamId": workspace_id,
        }
    }

    data = await railway_request(query, variables)

    project = data.get("projectCreate")

    if not project or not project.get("id"):
        raise RuntimeError(
            "Railway پروژه را ایجاد کرد، "
            "اما شناسه پروژه در پاسخ وجود ندارد."
        )

    return project


# ==============================
# PERMISSIONS
# ==============================

def is_admin(update: Update):
    user = update.effective_user

    return bool(
        user
        and ADMIN_ID
        and str(user.id) == ADMIN_ID
    )


# ==============================
# START
# ==============================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    await update.message.reply_text(
        "🐺 MASTER YOUSEF RAILWAY ULTIMATE\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {user.first_name}\n"
        "💎 نسخه: ULTIMATE\n"
        "🟢 ربات آماده است.\n\n"
        "یکی از گزینه‌های منو را انتخاب کن.",
        reply_markup=MENU,
    )


# ==============================
# MESSAGE HANDLER
# ==============================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    text = update.message.text.strip()

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ این بخش فقط برای مدیر ربات فعال است.",
            reply_markup=MENU,
        )
        return

    # اتصال Railway
    if text == "🔑 اتصال Railway":
        try:
            account = await get_account()

            await update.message.reply_text(
                "🟢 اتصال Railway موفق بود!\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 نام حساب: "
                f"{account.get('name') or 'بدون نام'}\n"
                f"📧 ایمیل: "
                f"{account.get('email') or 'در دسترس نیست'}\n"
                "🔐 توکن در متغیر محرمانه سرور نگهداری می‌شود.",
                reply_markup=MENU,
            )

        except Exception as error:
            logging.exception("Railway connection failed")

            await update.message.reply_text(
                "🔴 اتصال ناموفق بود.\n\n"
                f"علت: {str(error)[:700]}",
                reply_markup=MENU,
            )

        return

    # نمایش پروژه‌ها
    if text == "📦 پروژه‌های من":
        try:
            projects = await get_projects()

            if not projects:
                await update.message.reply_text(
                    "📦 هنوز پروژه‌ای پیدا نشد.\n"
                    "ممکن است توکن به حساب دیگری تعلق داشته باشد.",
                    reply_markup=MENU,
                )
                return

            lines = [
                "📦 پروژه‌های Railway",
                "━━━━━━━━━━━━━━━━━━",
            ]

            for project in projects[:25]:
                lines.append(
                    f"🚀 {project.get('name', 'بدون نام')}\n"
                    f"🆔 {project.get('id', 'نامشخص')}"
                )

            await update.message.reply_text(
                "\n\n".join(lines),
                reply_markup=MENU,
            )

        except Exception as error:
            logging.exception("Get projects failed")

            await update.message.reply_text(
                "🔴 دریافت پروژه‌ها ناموفق بود.\n\n"
                f"علت: {str(error)[:700]}",
                reply_markup=MENU,
            )

        return

    # شروع ساخت پروژه
    if text == "🚀 ساخت پروژه":
        context.user_data["waiting_project_name"] = True

        await update.message.reply_text(
            "🚀 ساخت پروژه جدید\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "اسم پروژه را به انگلیسی بفرست.\n\n"
            "مثال:\n"
            "MASTER-YOUSEF-TEST"
        )

        return

    # دریافت نام و ساخت پروژه
    if context.user_data.get("waiting_project_name"):
        name = text.strip()

        if not name or len(name) > 100:
            await update.message.reply_text(
                "⚠️ نام پروژه باید بین ۱ تا ۱۰۰ کاراکتر باشد."
            )
            return

        context.user_data["waiting_project_name"] = False

        try:
            await update.message.reply_text(
                "⏳ در حال بررسی فضای کاری Railway..."
            )

            workspaces = await get_workspaces()

            if not workspaces:
                await update.message.reply_text(
                    "🔴 هیچ فضای کاری قابل دسترسی پیدا نشد.\n\n"
                    "توکن و دسترسی حساب Railway را بررسی کن.",
                    reply_markup=MENU,
                )
                return

            workspace = workspaces[0]
            workspace_id = workspace.get("id")

            if not workspace_id:
                await update.message.reply_text(
                    "🔴 شناسه فضای کاری دریافت نشد.",
                    reply_markup=MENU,
                )
                return

            await update.message.reply_text(
                "🏢 فضای کاری پیدا شد:\n"
                f"{workspace.get('name', 'بدون نام')}\n\n"
                "⏳ در حال ارسال درخواست ساخت پروژه..."
            )

            project = await create_project(
                name=name,
                workspace_id=workspace_id,
            )

            await update.message.reply_text(
                "✅ پروژه با موفقیت ساخته شد!\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"📦 نام: {project.get('name', name)}\n"
                f"🆔 شناسه: {project.get('id')}\n"
                f"🏢 فضای کاری: "
                f"{workspace.get('name', 'بدون نام')}",
                reply_markup=MENU,
            )

        except Exception as error:
            logging.exception("Project creation failed")

            await update.message.reply_text(
                "🔴 ساخت پروژه ناموفق بود.\n\n"
                f"❌ علت: {str(error)[:700]}\n\n"
                "اگر خطای workspaceId تکرار شد، "
                "باید ساختار درخواست و پاسخ API را بررسی کنیم.",
                reply_markup=MENU,
            )

        return

    # داشبورد
    if text == "📊 داشبورد":
        try:
            account = await get_account()
            projects = await get_projects()

            await update.message.reply_text(
                "📊 داشبورد MASTER YOUSEF\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 حساب: {account.get('name') or 'بدون نام'}\n"
                f"📦 تعداد پروژه‌ها: {len(projects)}\n"
                "🟢 اتصال API: فعال",
                reply_markup=MENU,
            )

        except Exception as error:
            await update.message.reply_text(
                "🔴 دریافت داشبورد ناموفق بود.\n\n"
                f"علت: {str(error)[:500]}",
                reply_markup=MENU,
            )

        return

    # پشتیبانی
    if text == "🛠 پشتیبانی":
        await update.message.reply_text(
            "🛠 پشتیبانی: @SultanOfWolf",
            reply_markup=MENU,
        )
        return

    # کانال
    if text == "📢 کانال":
        await update.message.reply_text(
            "📢 کانال: @vpnstan1",
            reply_markup=MENU,
        )
        return

    await update.message.reply_text(
        "یکی از دکمه‌های منو را انتخاب کن.",
        reply_markup=MENU,
    )


# ==============================
# MAIN
# ==============================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "متغیر BOT_TOKEN در Railway تنظیم نشده است."
        )

    if not ADMIN_ID.isdigit():
        raise RuntimeError(
            "ADMIN_ID باید شناسه عددی تلگرام مدیر باشد."
        )

    if not RAILWAY_API_TOKEN:
        raise RuntimeError(
            "متغیر RAILWAY_API_TOKEN در Railway تنظیم نشده است."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    logging.info(
        "MASTER YOUSEF RAILWAY ULTIMATE is starting"
    )

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

