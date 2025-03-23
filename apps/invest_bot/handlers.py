from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import Dispatcher
from .bot_config import BOT_TOKEN, CHANNEL_ID, WEB_APP_URL, create_bot
from django.utils import timezone
from apps.users.models import User
from apps.subscriptions.models import Subscription, SubscriptionPlan
from asgiref.sync import sync_to_async
import logging
import json
import uuid

logger = logging.getLogger(__name__)

PAYMENT_METHODS = {
    "uzcard": "💳 Uzcard",
    "humo": "💳 Humo",
    "visa": "💳 Visa",
    "mastercard": "💳 Mastercard",
}

# Bot va dispatcher ni olish
bot_instance = create_bot()
bot = bot_instance['bot']
dp = bot_instance['dp']

# ✅ Foydalanuvchini yaratish yoki olish
@sync_to_async
def get_or_create_user(telegram_user_id, first_name, last_name, ref_code=None):
    try:
        user, created = User.objects.get_or_create(
            telegram_user_id=telegram_user_id,
            defaults={
                "user_id": telegram_user_id,
                "first_name": first_name,
                "last_name": last_name,
                "created_at": timezone.now(),
                "phone_number": None
            }
        )
        
        # Referral kodni tekshirish
        if created and ref_code:
            try:
                referrer = User.objects.get(referral_code=ref_code)
                referrer.add_referral(user)
                user.is_subscribed = True
                user.save()
            except User.DoesNotExist:
                pass
                
        logger.info(f"{'✅ Yangi foydalanuvchi yaratildi' if created else '✅ Mavjud foydalanuvchi olindi'}: {first_name}")
        return user, created
    except Exception as e:
        logger.error(f"❌ Foydalanuvchini yaratishda xatolik: {e}")
        return None, False

@sync_to_async
def get_subscription_plans():
    return list(SubscriptionPlan.objects.all())

@sync_to_async
def create_subscription(user_id, plan_id, amount):
    try:
        user = User.objects.get(telegram_user_id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        subscription = Subscription.objects.create(
            user=user,
            subscription_plan=plan,
            amount_paid=amount,
            status="pending"
        )
        return subscription
    except Exception as e:
        logger.error(f"❌ Obuna yaratishda xatolik: {e}")
        return None

# Start komandasi uchun handler
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """Start komandasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text="🌐 Web App'ga kirish",
        web_app={"url": WEB_APP_URL}
    ))
    
    await message.answer(
        "Assalomu alaykum! Top Invest botiga xush kelibsiz.\n"
        "Web App orqali barcha imkoniyatlardan foydalanishingiz mumkin:",
        reply_markup=keyboard
    )

@dp.message_handler(Command('help'))
async def help_command(message: types.Message):
    help_text = """
🤖 Top Invest Bot buyruqlari:

/start - Botni ishga tushirish
/help - Yordam olish
/profile - Profil malumotlarini korish
"""
    await message.answer(help_text)

@dp.message_handler(Command('profile'))
async def profile_command(message: types.Message):
    try:
        user = await sync_to_async(User.objects.get)(telegram_user_id=str(message.from_user.id))
        profile_text = f"""
👤 Sizning profilingiz:

Ism: {user.first_name or 'Korsatilmagan'}
Familiya: {user.last_name or 'Korsatilmagan'}
Username: @{user.username or 'Korsatilmagan'}
Balans: {user.balance} som
Royxatdan otgan sana: {user.date_joined.strftime('%d.%m.%Y')}
"""
        await message.answer(profile_text)
    except User.DoesNotExist:
        await message.answer("Siz hali royxatdan otmagansiz. /start buyrugini bosing.")
    except Exception as e:
        logger.error(f"Profil komandasi xatoligi: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib koring.")

@dp.callback_query_handler(lambda c: c.data.startswith('show_plans'))
async def show_subscription_plans(callback_query: types.CallbackQuery):
    try:
        plans = await get_subscription_plans()
        keyboard = types.InlineKeyboardMarkup()
        
        for plan in plans:
            keyboard.add(types.InlineKeyboardButton(
                text=f"{plan.title} - {plan.price} som ({plan.duration_days} kun)",
                callback_data=f"select_plan:{plan.id}"
            ))
        
        await callback_query.message.edit_text(
            "💰 Quyidagi obuna rejalaridan birini tanlang:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Obuna rejalarini korsatishda xatolik: {e}")
        await callback_query.message.edit_text("Xatolik yuz berdi. Iltimos, /start buyrugini qayta yuboring.")

@dp.callback_query_handler(lambda c: c.data.startswith('select_plan:'))
async def select_payment_method(callback_query: types.CallbackQuery):
    """To'lov usulini tanlash"""
    try:
        plan_id = int(callback_query.data.split(":")[1])
        keyboard = types.InlineKeyboardMarkup()
        
        for method, name in PAYMENT_METHODS.items():
            keyboard.add(types.InlineKeyboardButton(
                text=name,
                callback_data=f"payment:{plan_id}:{method}"
            ))
        
        await callback_query.message.edit_text(
            "💳 To'lov usulini tanlang:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"❌ To'lov usulini tanlashda xatolik: {e}")
        await callback_query.message.edit_text("❌ Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring.")

@dp.callback_query_handler(lambda c: c.data.startswith('payment:'))
async def process_payment(callback_query: types.CallbackQuery):
    """To'lov jarayonini boshlash"""
    try:
        plan_id, payment_method = callback_query.data.split(":")[1:]
        subscription = await create_subscription(
            callback_query.from_user.id,
            int(plan_id),
            0  # To'lov miqdori keyinroq yangilanadi
        )
        
        if not subscription:
            await callback_query.message.edit_text("❌ Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring.")
            return

        await callback_query.message.edit_text(
            "📸 To'lov chekini yuborish uchun rasm yuboring.\n\n"
            "❗️ Muhim: Rasm aniq va to'lov ma'lumotlari ko'rinib turishi kerak."
        )
    except Exception as e:
        logger.error(f"❌ To'lov jarayonida xatolik: {e}")
        await callback_query.message.edit_text("❌ Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring.")

@dp.message_handler(lambda message: message.photo)
async def handle_payment_screenshot(message: types.Message):
    """To'lov chekini qabul qilish"""
    try:
        # Rasmni saqlash
        photo = message.photo[-1]
        subscription = await get_active_subscription(message.from_user.id)
        
        if not subscription:
            await message.answer("❌ Faol obuna topilmadi. Iltimos, /start buyrug'ini qayta yuboring.")
            return

        # To'lov chekini saqlash
        await save_payment_screenshot(subscription.id, photo.file_id)
        
        await message.answer(
            "✅ To'lov cheki qabul qilindi!\n\n"
            "👨‍💼 Administrator tekshiruvidan so'ng obunangiz faollashtiriladi.\n"
            "⏳ Iltimos, kuting..."
        )
    except Exception as e:
        logger.error(f"❌ To'lov chekini saqlashda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring.")

@sync_to_async
def get_active_subscription(user_id):
    try:
        return Subscription.objects.filter(
            user__telegram_user_id=user_id,
            status="pending"
        ).latest('created_at')
    except Subscription.DoesNotExist:
        return None

@sync_to_async
def save_payment_screenshot(subscription_id, file_id):
    subscription = Subscription.objects.get(id=subscription_id)
    subscription.payment_screenshot = file_id
    subscription.status = "waiting_admin"
    subscription.save(update_fields=['payment_screenshot', 'status'])

@sync_to_async
def generate_invite_link(subscription_id):
    subscription = Subscription.objects.get(id=subscription_id)
    return subscription.generate_invite_link()

@dp.callback_query_handler(lambda c: c.data.startswith('approve_payment:'))
async def approve_payment(callback_query: types.CallbackQuery):
    """To'lovni tasdiqlash"""
    try:
        subscription_id = int(callback_query.data.split(":")[1])
        subscription = await get_subscription_by_id(subscription_id)
        
        if not subscription:
            await callback_query.message.edit_text("❌ Obuna topilmadi.")
            return

        # Obunani faollashtirish
        await activate_subscription(subscription_id)
        
        # Taklif havolasini yaratish
        invite_link = await generate_invite_link(subscription_id)
        
        # Foydalanuvchiga xabar yuborish
        await bot.send_message(
            chat_id=subscription.user.telegram_user_id,
            text=f"✅ To'lovingiz tasdiqlandi!\n\n"
                 f"🔗 Sizning 24 soatlik havola: {invite_link}\n\n"
                 f"❗️ Eslatma: Havola 24 soatdan so'ng o'z kuchini yo'qotadi."
        )
        
        await callback_query.message.edit_text(
            f"✅ To'lov tasdiqlandi va foydalanuvchiga havola yuborildi!\n"
            f"👤 Foydalanuvchi: {subscription.user.first_name}\n"
            f"💰 To'lov: {subscription.amount_paid} som\n"
            f"🔗 Havola: {invite_link}"
        )
    except Exception as e:
        logger.error(f"❌ To'lovni tasdiqlashda xatolik: {e}")
        await callback_query.message.edit_text("❌ Xatolik yuz berdi.")

@dp.callback_query_handler(lambda c: c.data.startswith('reject_payment:'))
async def reject_payment(callback_query: types.CallbackQuery):
    """To'lovni rad etish"""
    try:
        subscription_id = int(callback_query.data.split(":")[1])
        subscription = await get_subscription_by_id(subscription_id)
        
        if not subscription:
            await callback_query.message.edit_text("❌ Obuna topilmadi.")
            return

        # Obunani rad etish
        await reject_subscription(subscription_id)
        
        # Foydalanuvchiga xabar yuborish
        await bot.send_message(
            chat_id=subscription.user.telegram_user_id,
            text="❌ Afsuski, to'lovingiz rad etildi.\n\n"
                 "🔄 Iltimos, to'lovni qayta amalga oshiring yoki administrator bilan bog'laning."
        )
        
        await callback_query.message.edit_text(
            f"❌ To'lov rad etildi!\n"
            f"👤 Foydalanuvchi: {subscription.user.first_name}"
        )
    except Exception as e:
        logger.error(f"❌ To'lovni rad etishda xatolik: {e}")
        await callback_query.message.edit_text("❌ Xatolik yuz berdi.")

@sync_to_async
def get_subscription_by_id(subscription_id):
    try:
        return Subscription.objects.select_related('user').get(id=subscription_id)
    except Subscription.DoesNotExist:
        return None

@sync_to_async
def activate_subscription(subscription_id):
    subscription = Subscription.objects.get(id=subscription_id)
    subscription.activate()
    return subscription

@sync_to_async
def reject_subscription(subscription_id):
    subscription = Subscription.objects.get(id=subscription_id)
    subscription.status = "rejected"
    subscription.save(update_fields=['status'])
    return subscription

@dp.message_handler(Command("admin"))
async def admin_panel(message: types.Message):
    """Admin paneli"""
    try:
        user = await get_user_by_id(message.from_user.id)
        if not user or not user.is_admin:
            await message.answer("❌ Sizda administrator huquqlari yo'q.")
            return

        # Kutilayotgan to'lovlarni olish
        pending_payments = await get_pending_payments()
        
        if not pending_payments:
            await message.answer("📝 Hozircha kutilayotgan to'lovlar yo'q.")
            return

        for payment in pending_payments:
            try:
                # To'lov ma'lumotlarini yuborish
                text = (
                    f"💰 Yangi to'lov kutilmoqda!\n\n"
                    f"👤 Foydalanuvchi: {payment.user.first_name}\n"
                    f"📱 Telegram ID: {payment.user.telegram_user_id}\n"
                    f"💳 To'lov miqdori: {payment.amount_paid} som\n"
                    f"📅 Sana: {payment.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
                
                # To'lov chekini yuborish
                screenshot = await get_payment_screenshot(payment.id)
                if screenshot:
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="✅ Tasdiqlash",
                                callback_data=f"approve_payment:{payment.id}"
                            ),
                            types.InlineKeyboardButton(
                                text="❌ Rad etish",
                                callback_data=f"reject_payment:{payment.id}"
                            )
                        ]
                    ])
                    
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=screenshot.file_id,
                        caption=text,
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(f"{text}\n\n❌ To'lov cheki topilmadi.")
            except Exception as e:
                logger.error(f"❌ To'lov ma'lumotlarini yuborishda xatolik: {e}")
                continue
                
    except Exception as e:
        logger.error(f"❌ To'lovlarni tekshirishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

@sync_to_async
def get_user_by_id(telegram_user_id):
    try:
        return User.objects.get(telegram_user_id=telegram_user_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def get_pending_payments():
    return list(Subscription.objects.select_related('user').filter(status="waiting_admin"))

@sync_to_async
def get_payment_screenshot(subscription_id):
    try:
        return Subscription.objects.get(id=subscription_id).payment_screenshot
    except Subscription.DoesNotExist:
        return None

@dp.callback_query_handler(lambda c: c.data == "broadcast")
async def broadcast_menu(callback_query: types.CallbackQuery):
    """Xabar yuborish menyusi"""
    if not (await get_user_by_id(callback_query.from_user.id)).is_admin:
        await callback_query.answer("❌ Sizda administrator huquqlari yo'q!")
        return

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="👥 Barcha foydalanuvchilarga",
            callback_data="broadcast_all"
        )],
        [types.InlineKeyboardButton(
            text="✅ Faqat obunachilarga",
            callback_data="broadcast_subs"
        )],
        [types.InlineKeyboardButton(
            text="🔄 Start bosganlar",
            callback_data="broadcast_active"
        )]
    ])

    await callback_query.message.edit_text(
        "📨 Kimga xabar yubormoqchisiz?",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("broadcast_"))
async def set_broadcast_type(callback_query: types.CallbackQuery):
    """Xabar turini tanlash"""
    if not (await get_user_by_id(callback_query.from_user.id)).is_admin:
        await callback_query.answer("❌ Sizda administrator huquqlari yo'q!")
        return

    broadcast_type = callback_query.data.split("_")[1]
    await callback_query.message.edit_text(
        "📝 Endi xabarni yuboring (matn, rasm, video yoki audio).\n"
        "❌ Bekor qilish uchun /cancel buyrug'ini yuboring."
    )
    
    # Foydalanuvchi holatini o'zgartiramiz
    user = await get_user_by_id(callback_query.from_user.id)
    user.temp_data = {"broadcast_type": broadcast_type}
    await save_user(user)

@dp.message_handler(lambda message: message.text)
async def handle_broadcast_message(message: types.Message):
    """Xabarni yuborish"""
    user = await get_user_by_id(message.from_user.id)
    if not user or not user.is_admin or not hasattr(user, 'temp_data'):
        return

    if message.text == "/cancel":
        user.temp_data = {}
        await save_user(user)
        await message.answer("❌ Xabar yuborish bekor qilindi.")
        return

    broadcast_type = user.temp_data.get("broadcast_type")
    if not broadcast_type:
        return

    # Foydalanuvchilarni tanlash
    users = []
    if broadcast_type == "all":
        users = await get_all_users()
    elif broadcast_type == "subs":
        users = await get_subscribed_users()
    elif broadcast_type == "active":
        users = await get_active_users()

    # Xabarni yuborish
    success = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(
                chat_id=int(user.telegram_user_id),
                text=message.text
            )
            success += 1
        except Exception as e:
            logger.error(f"❌ Xabar yuborishda xatolik: {e}")
            failed += 1

    # Natijani yuborish
    await message.answer(
        f"📊 Xabar yuborish yakunlandi:\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Muvaffaqiyatsiz: {failed}"
    )

    # Foydalanuvchi holatini tozalash
    user.temp_data = {}
    await save_user(user)

@dp.callback_query_handler(lambda c: c.data == "generate_ref")
async def generate_referral(callback_query: types.CallbackQuery):
    """Referral havola yaratish"""
    user = await get_user_by_id(callback_query.from_user.id)
    if not user.is_admin:
        await callback_query.answer("❌ Sizda administrator huquqlari yo'q!")
        return

    ref_link = user.get_referral_link()
    await callback_query.message.edit_text(
        f"🔗 Sizning referral havolangiz:\n\n"
        f"`{ref_link}`\n\n"
        f"Bu havola orqali kirgan foydalanuvchilar avtomatik obunachi bo'ladi.",
        parse_mode="Markdown"
    )

@sync_to_async
def get_all_users():
    """Barcha foydalanuvchilarni olish"""
    return list(User.objects.all())

@sync_to_async
def get_subscribed_users():
    """Obunachi foydalanuvchilarni olish"""
    return list(User.objects.filter(is_subscribed=True))

@sync_to_async
def get_active_users():
    """Faol foydalanuvchilarni olish"""
    return list(User.objects.filter(telegram_user_id__isnull=False))

@sync_to_async
def save_user(user):
    """Foydalanuvchi ma'lumotlarini saqlash"""
    user.save()
    return user

def register_handlers(dp: Dispatcher):
    """Handlerlarni royxatdan otkazish"""
    # Bu funksiya hozircha bo'sh, chunki handlerlar dekoratorlar orqali ro'yxatdan o'tkazilgan
    pass 