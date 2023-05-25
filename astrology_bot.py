import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv

from bs4 import BeautifulSoup

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    BotCommand,
    Bot
)

from telegram.ext import (
    ContextTypes,
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from ASTROLOGY_CONSTANTS import (
    ASTROLOGICAL_SIGNS_KEYBOARD,
    ASTROLOGERS_DICT,
    ASTROLOGERS_KEYBOARD,
    ASTROLOGICAL_SIGNS_DICT,
    ABOUT_DICT,
    ABOUT_KEYBOARD,
    FORMATED_ABOUT_DICT
)


import logging
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_inits(application:Application):
    bot : Bot = application.bot
    await bot.set_my_commands([
        BotCommand('start','Start the bot and choose your astrological sign.'),
        BotCommand('anotherastro','Choose another astrologer')
    ])
    await bot.set_my_description("""Astrology Bot - بوت الأبراج
هو بوت يتيح لك معرفة توقعات برجك اليومية من وجهة نظر أكثر من عالم فلك.
اضغط /start واختر برجك لتبدأ...
أهلا وسهلا بك🥳""")

SIGN , ASTRO , ABOUT = range(3)

async def start_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    astro_markup = ReplyKeyboardMarkup(keyboard=ASTROLOGICAL_SIGNS_KEYBOARD,
                                       resize_keyboard=True)
    context.chat_data['current keyboard'] = astro_markup
    if 'setup done' in context.user_data:
        message = 'قم باختيار البرج الذي تريد معرفة توقعات اليوم عنه:'
        context.chat_data['current message'] = message
        await update.message.reply_text(text=message,
                                       reply_markup=astro_markup)
        return SIGN
    
    context.user_data['setup done'] = True
    message = 'أهلا بك في بوت الأبراج قم باختيار البرج الذي تريد أن تعرف توقعات اليوم عنه:'
    context.chat_data['current message'] = message
    await update.message.reply_text(text=message,
                                   reply_markup=astro_markup)
    return SIGN
    
async def sign(update:Update, context:ContextTypes.DEFAULT_TYPE):
    sign = update.message.text
    context.chat_data['sign'] = ASTROLOGICAL_SIGNS_DICT[sign]
    context.chat_data['sign in ar'] = sign
    astrologer_markup = ReplyKeyboardMarkup(keyboard=ASTROLOGERS_KEYBOARD, resize_keyboard=True)
    context.chat_data['current keyboard'] = astrologer_markup
    message = f'من الذي تريد أن تعرف توقعاته عن برج {sign}:'
    context.chat_data['current message'] = message
    await update.message.reply_text(text=message,
                                    reply_markup=astrologer_markup)
    return ASTRO

async def astrologer(update:Update, context:ContextTypes.DEFAULT_TYPE):
    astro = update.message.text
    context.chat_data['astro'] = ASTROLOGERS_DICT[astro]
    context.chat_data['astro in ar'] = astro
    about_markup = ReplyKeyboardMarkup(keyboard=ABOUT_KEYBOARD,resize_keyboard=True)
    context.chat_data['current keyboard'] = about_markup
    sign = context.chat_data['sign in ar']
    message = f"على أي صعيد تريد أن تعرف توقعات {astro} عن برج {sign}؟"
    context.chat_data['current message'] = message
    await update.message.reply_text(text=message,
                                    reply_markup=about_markup)
    return ABOUT

async def about(update:Update, context:ContextTypes.DEFAULT_TYPE):
    astro = context.chat_data['astro']
    astro_in_arabic = context.chat_data['astro in ar']
    sign = context.chat_data['sign']
    sign_in_arabic = context.chat_data['sign in ar']
    about = ABOUT_DICT[update.message.text]
    formated_about = FORMATED_ABOUT_DICT[update.message.text]
    url = f'https://arabhaz.com/wp/{astro}/'
    response = requests.get(url)

    astro_soup = BeautifulSoup(response.text, 'html.parser')

    title = f"توقعات {astro_in_arabic} لبرج {sign_in_arabic} {formated_about} اليوم:\n"

    res = ''
    if about == 'general' and sign_in_arabic in ['العذراء','العقرب','الميزان','القوس']:
        sign_general = astro_soup.find_all('div',{"id":f'general-general'})
        signs = []
        for s in sign_general:
            signs.append(s.find('p',{'class':'newzodiac'}).text)
        
        if sign_in_arabic=='العذراء':
            res = title + signs[0]
        
        elif sign_in_arabic=='الميزان':
            res = title + signs[1]
        
        elif sign_in_arabic=='العقرب':
            res = title + signs[2]
        
        elif sign_in_arabic=='القوس':
            res = title + signs[3]
        
    else:
        res = title + astro_soup.find('div',{"id":f'{sign}-{about}'}).find('p',{'class':'newzodiac'}).text


    await update.message.reply_text(text=res)
    message = f'لمعرفة توقعات برج {sign_in_arabic} من وجهة نظر شخص آخر اضغط /anotherastro، أو اضغط /start لاختيار برج جديد.'
    context.chat_data['current message'] = message
    await update.message.reply_text(text=message)



#FALLBACKS

async def another_astro(update:Update, context:ContextTypes.DEFAULT_TYPE):
    sign = context.chat_data['sign in ar']
    astrologer_markup = ReplyKeyboardMarkup(keyboard=ASTROLOGERS_KEYBOARD, resize_keyboard=True)
    context.chat_data['current keyboard'] = astrologer_markup
    message = f'من أيضاً تريد أن تعرف توقعاته عن برج {sign}:'
    context.chat_data['current message'] = message
    await update.message.reply_text(text=message,
                                    reply_markup=astrologer_markup)
    return ASTRO

async def unkown(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text="أمر غير معروف، الرجاء الاختيار من الكيبورد.",
                                    reply_markup=context.chat_data['current keyboard'])
    await update.message.reply_text(text=context.chat_data['current message'])

def main():
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    token = os.environ.get("BOT_TOKEN")
    app = Application.builder().token(token).post_init(post_inits).build()
    signs_regex = filters.Regex('الحمل|الثور|الجوزاء|السرطان|الأسد|العذراء|الميزان|العقرب|القوس|الجدي|الدلو|الحوت')
    astros_regex = filters.Regex('ماغي فرح|كارمن شماس|جاكلين عقيقي|نجلاء قباني')
    about_regex = filters.Regex('عام|عاطفياً|صحياً|مهنياً')

    start_handler = CommandHandler('start',start_command)
    sign_handler = MessageHandler(signs_regex, sign)
    astrologer_handler = MessageHandler(astros_regex, astrologer)
    about_handler = MessageHandler(about_regex, about)
    another_astro_handler = CommandHandler('anotherastro',another_astro)
    unknown_handler = MessageHandler(filters.TEXT & ~about_regex & ~signs_regex & ~astros_regex & ~filters.COMMAND, unkown)

    conv_handler = ConversationHandler(entry_points=[start_handler],
                                       states={
                                            SIGN:[sign_handler,start_handler],
                                            ASTRO:[astrologer_handler,start_handler],
                                            ABOUT:[about_handler,start_handler]
                                       },
                                       fallbacks=[unknown_handler,another_astro_handler]
    )
    app.add_handler(conv_handler)
    app.run_polling(timeout=100)

if __name__ == '__main__':
    main()
