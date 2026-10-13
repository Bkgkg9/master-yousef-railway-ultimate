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

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN", "").strip()

RAILWAY_API = "https://backboard.railway.com/graphql/v2"

MENU = ReplyKeyboardMarkup(
    [
        ["🔑 اتصال Railway", "📦 پروژه‌های من"],
        ["🚀 ساخت پروژه", "📊 داشبورد"],
        ["🛠 پشتیبانی", "📢 کانال"],
    ],
    resize_keyboard=True,
)


async def railway_request(query, variables=None):
    if not RAILWAY_API_TOKEN:
        raise RuntimeError(
            "متغیر RAILWAY_API_TOKEN در Railway تنظیم نشده است."
        )

    headers = {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
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
        messages = [
            item.get("message", "خطای نامشخص")
            for item in result["errors"]
        ]
        raise RuntimeError("\n".join(messages))

    return result.get("data", {})


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
    me = data.get("me") or {}
    return me.get("workspaces") or []


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
            "workspaceId": workspace_id,
        }
    }

    data = await railway_request(query, variables)
    return data.get("projectCreate") or {}


def is_admin(update):
    if not ADMIN_ID:
        return False

    user = update.effective_user
    return bool(user and str(user.id) == ADMIN_ID)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    text = (
        "🐺 MASTER YOUSEF RAILWAY ULTIMATE\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {user.first_name}\n"
        "💎 نسخه: ULTIMATE\n"
        "🟢 ربات آنلاین است.\n\n"
        "یکی از گزینه‌های زیر را انتخاب کن."
    )

    await update.message.reply_text(text, reply_markup=MENU)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.effective_user:
        return

    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ این بخش فقط برای مدیر ربات فعال است.",
            reply_markup=MENU,
        )
        return

    if text == "🔑 اتصال Railway":
        try:
            account = await get_account()

            await update.message.reply_text(
                "🟢 اتصال Railway موفق بود!\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 نام حساب: {account.get('name') or 'بدون نام'}\n"
                f"📧 ایمیل: {account.get('email') or 'در دسترس نیست'}\n\n"
                "🔐 توکن فقط در متغیر محرمانه سرور نگهداری می‌شود.",
                reply_markup=MENU,
            )
        except Exception as exc:
            logging.exception("Railway account error")
            await update.message.reply_text(
                f"🔴 اتصال ناموفق بود:\n{str(exc)[:700]}",
                reply_markup=MENU,
            )
        return

    if text == "📦 پروژه‌های من":
        try:
            projects = await get_projects()

            if not projects:
                await update.message.reply_text(
                    "📦 هنوز پروژه‌ای در این حساب پیدا نشد.",
                    reply_markup=MENU,
                )
                return

            lines = ["📦 پروژه‌های Railway", "━━━━━━━━━━━━━━━━━━"]

            for project in projects[:30]:
                lines.append(
                    f"🚀 {project.get('name', 'بدون نام')}\n"
                    f"🆔 {project.get('id', '')}"
                )

            await update.message.reply_text(
                "\n\n".join(lines),
                reply_markup=MENU,
            )
        except Exception as exc:
            logging.exception("Project listing error")
            await update.message.reply_text(
                f"🔴 دریافت پروژه‌ها ناموفق بود:\n{str(exc)[:700]}",
                reply_markup=MENU,
            )
        return

    if text == "🚀 ساخت پروژه":
        context.user_data["waiting_project_name"] = True

        await update.message.reply_text(
            "🚀 ساخت پروژه جدید\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "اسم پروژه را به انگلیسی بفرست.\n"
            "مثال: MASTER-YOUSEF-APP"
        )
        return

    if context.user_data.get("waiting_project_name"):
        name = text

        if not name or len(name) > 100:
            await update.message.reply_text(
                "⚠️ اسم پروژه باید بین ۱ تا ۱۰۰ کاراکتر باشد."
            )
            return

        context.user_data["waiting_project_name"] = False

        try:
            workspaces = await get_workspaces()

            if not workspaces:
                await update.message.reply_text(
                    "🔴 هیچ فضای کاری برای این توکن پیدا نشد.\n"
                    "توکن Railway و دسترسی حساب را بررسی کن.",
                    reply_markup=MENU,
                )
                return

            # استفاده از اولین فضای کاری قابل دسترس
            workspace = workspaces[0]
            workspace_id = workspace.get("id")

            if not workspace_id:
                await update.message.reply_text(
                    "🔴 شناسه فضای کاری از Railway دریافت نشد.",
                    reply_markup=MENU,
                )
                return

            project = await create_project(name, workspace_id)

            if project.get("id"):
                await update.message.reply_text(
                    "✅ پروژه با موفقیت ساخته شد!\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    f"📦 نام: {project.get('name', name)}\n"
                    f"🆔 شناسه: {project['id']}\n"
                    f"🏢 فضای کاری: {workspace.get('name', 'بدون نام')}",
                    reply_markup=MENU,
                )
            else:
                await update.message.reply_text(
                    "🔴 پاسخ ساخت پروژه کامل نبود.\n"
                    "لطفاً Logs سرویس Railway را بررسی کن.",
                    reply_markup=MENU,
                )

        except Exception as exc:
            logging.exception("Project creation error")
            await update.message.reply_text(
                f"🔴 ساخت پروژه ناموفق بود:\n{str(exc)[:700]}",
                reply_markup=MENU,
            )
        return

    if text == "📊 داشبورد":
        try:
            account = await get_account()
            projects = await get_projects()

            await update.message.reply_text(
                "📊 داشبورد MASTER YOUSEF\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 حساب: {account.get('name') or 'بدون نام'}\n"
                f"📦 تعداد پروژه‌ها: {len(projects)}\n"
                "🟢 وضعیت اتصال: فعال",
                reply_markup=MENU,
            )
        except Exception as exc:
            await update.message.reply_text(
                f"🔴 دریافت داشبورد ناموفق بود:\n{str(exc)[:500]}",
                reply_markup=MENU,
            )
        return

    if text == "🛠 پشتیبانی":
        await update.message.reply_text(
            "🛠 پشتیبانی: @SultanOfWolf",
            reply_markup=MENU,
        )
        return

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


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "متغیر BOT_TOKEN در Railway تعریف نشده است."
        )

    if not ADMIN_ID.isdigit():
        raise RuntimeError(
            "متغیر ADMIN_ID باید شناسه عددی تلگرام مدیر باشد."
        )

    if not RAILWAY_API_TOKEN:
        raise RuntimeError(
            "متغیر RAILWAY_API_TOKEN در Railway تعریف نشده است."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logging.info("MASTER YOUSEF RAILWAY ULTIMATE is starting")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

