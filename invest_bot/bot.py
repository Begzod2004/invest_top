from aiogram import Bot, Dispatcher
from asgiref.sync import sync_to_async
from subscriptions.models import Subscription
from django.utils.timezone import now
import asyncio
import logging
from signals.models import Signal
from .handlers import router  # Router ni import qilamiz
from .bot_config import BOT_TOKEN, CHANNEL_ID

# Logging ni sozlaymiz
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Router ni dp ga qo'shamiz
dp.include_router(router)

@sync_to_async
def get_expired_subscriptions():
    return list(Subscription.objects.select_related('user').filter(
        status="active",
        expires_at__lte=now()
    ))

@sync_to_async
def save_subscription(subscription):
    subscription.status = "expired"
    subscription.save()

async def add_user_to_channel(user_id):
    """Foydalanuvchini kanalga qo'shish"""
    try:
        await bot.promote_chat_member(CHANNEL_ID, user_id, can_invite_users=True)
        logger.info(f"✅ Foydalanuvchi {user_id} kanalga muvaffaqiyatli qo'shildi")
        return True
    except Exception as e:
        logger.error(f"❌ Foydalanuvchini kanalga qo'shishda xatolik: {e}")
        return False

async def remove_user_from_channel(user_id):
    """Foydalanuvchini kanaldan chiqarish"""
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
        await bot.unban_chat_member(CHANNEL_ID, user_id)  # Unban qilib, qaytadan qo'shish imkoniyatini beramiz
        logger.info(f"❌ Foydalanuvchi {user_id} kanaldan chiqarildi")
        return True
    except Exception as e:
        logger.error(f"❌ Foydalanuvchini kanaldan chiqarishda xatolik: {e}")
        return False

async def check_subscriptions():
    """Obuna muddati tugaganlarni tekshirib, chiqarish"""
    try:
        expired_subs = await get_expired_subscriptions()
        if not expired_subs:
            return
            
        logger.info(f"🔍 {len(expired_subs)} ta obunasi tugagan foydalanuvchilar topildi")
        
        tasks = []
        for sub in expired_subs:
            # Foydalanuvchiga xabar yuborish
            tasks.append(
                asyncio.create_task(
                    bot.send_message(
                        chat_id=sub.user.telegram_user_id,
                        text=f"⚠️ Hurmatli {sub.user.first_name},\n\n"
                             f"Sizning obuna muddatingiz tugadi. Kanaldan chiqarilasiz.\n"
                             f"Obunani yangilash uchun /start buyrug'ini yuboring."
                    )
                )
            )
            
            # Kanaldan chiqarish
            tasks.append(
                asyncio.create_task(
                    remove_user_from_channel(sub.user.telegram_user_id)
                )
            )
            
            tasks.append(
                asyncio.create_task(
                    save_subscription(sub)
                )
            )
        
        # Barcha tasklarni bir vaqtda bajaramiz
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"✅ {len(expired_subs)} ta foydalanuvchi obunasi tugatildi")
            
    except Exception as e:
        logger.error(f"❌ Obunalarni tekshirishda xatolik: {e}")

async def start_checking():
    """Doimiy ravishda obuna tugaganlarni tekshirish"""
    logger.info("🚀 Obunalarni tekshirish jarayoni boshlandi")
    while True:
        await check_subscriptions()
        await asyncio.sleep(6)  # Har soatda tekshiramiz

@sync_to_async
def get_new_signals():
    """Yangi signallarni olish"""
    return list(Signal.objects.filter(is_posted=False))

@sync_to_async
def mark_signal_as_posted(signal):
    """Signalni yuborilgan deb belgilash"""
    Signal.objects.filter(id=signal.id).update(is_posted=True)

async def post_signals():
    """Yangi signallarni kanalga joylash"""
    try:
        new_signals = await get_new_signals()
        if not new_signals:
            return

        for signal in new_signals:
            text = (
                f"📊 *YANGI SIGNAL* 📊\n\n"
                f"🎯 *{signal.instrument}*\n"
                f"📈 Order: {signal.order_type.upper()}\n"
                f"💰 Narx: {signal.target_position}\n"
                f"🛑 Stop Loss: {signal.stop_loss}\n"
                f"✅ Take Profit: {signal.take_profit}\n\n"
                f"⏰ {signal.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
            
            try:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode="Markdown"
                )
                await mark_signal_as_posted(signal)
                logger.info(f"Signal #{signal.id} yuborildi")
            except Exception as e:
                logger.error(f"Signal #{signal.id} yuborishda xatolik: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Signallarni yuborishda xatolik: {e}")

async def start_posting():
    """Signallarni avtomatik joylash"""
    logger.info("Signallarni joylash jarayoni boshlandi")
    while True:
        await post_signals()
        await asyncio.sleep(30)  # Har 30 sekundda yangi signallarni tekshirish

async def check_bot_permissions():
    """Bot huquqlarini tekshirish"""
    try:
        # Bot o'zining huquqlarini tekshiradi
        bot_member = await bot.get_chat_member(CHANNEL_ID, (await bot.me()).id)
        
        # Private kanal uchun kerakli huquqlar
        required_rights = {
            'can_post_messages': True,  # Xabar yuborish
            'can_invite_users': True,   # Foydalanuvchilarni taklif qilish
            'can_restrict_members': True # A'zolarni boshqarish
        }
        
        missing_rights = []
        for right, required in required_rights.items():
            if not getattr(bot_member, right, False):
                missing_rights.append(right)
        
        if missing_rights:
            logger.error(f"❌ Botga quyidagi huquqlar yetishmayapti: {', '.join(missing_rights)}")
            return False
            
        logger.info("✅ Bot barcha kerakli huquqlarga ega")
        return True
            
    except Exception as e:
        if "bot was kicked" in str(e).lower():
            logger.error("❌ Bot kanaldan o'chirilgan. Iltimos, botni kanalga admin sifatida qo'shing")
        else:
            logger.error(f"❌ Bot huquqlarini tekshirishda xatolik: {str(e)}")
        return False

async def start_bot():
    """Botni ishga tushirish"""
    logger.info("🚀 Bot ishga tushmoqda...")
    
    # Bot huquqlarini tekshirish
    await check_bot_permissions()
    
    # Asosiy tasklar
    tasks = [
        asyncio.create_task(start_checking()),
        asyncio.create_task(start_posting()),
        asyncio.create_task(dp.start_polling(bot))
    ]
    
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"❌ Bot ishlashida xatolik: {str(e)}")
    finally:
        # Bot to'xtaganda
        tasks = [t for t in tasks if not t.done()]
        [t.cancel() for t in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)