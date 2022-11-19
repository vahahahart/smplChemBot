import asyncio
import json
import logging
from os import getenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.handlers import commands, statistics_menu, states


def set_logging():
    """
    Set logging for Yandex.Cloud logging
    'WARN' level default
    """
    if getenv('START') == 'LOCAL':
        # local logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s]\t%(asctime)s\t%(name)s\t%(message)s'
        )
    else:
        logging_level = getenv('LOGGING_LEVEL')
        root_logger = logging.getLogger()
        root_logger.handlers[0].setFormatter(
            logging.Formatter('[%(levelname)s]\t%(name)s\t%(request_id)s\t%(message)s\n')
        )
        root_logger.setLevel(logging_level if logging_level else 'WARN')


async def set_commands(bot: Bot):
    cmds = [
        BotCommand(command='/help', description='Помощь'),
        BotCommand(command='/statistics', description='Стат. расчеты'),
        BotCommand(command='/current', description='Отобразить активный набор данных'),
        BotCommand(command='/mol_weights', description='Расчеты масс'),
        BotCommand(command='/cancel', description='Отменить текущее действие')
    ]
    await bot.set_my_commands(cmds)


def bot_init() -> tuple[Bot, Dispatcher]:
    set_logging()

    bot = Bot(token=getenv('BOT_TOKEN'), parse_mode='HTML')
    dp = Dispatcher()

    dp.include_router(commands.router)
    dp.include_router(statistics_menu.router)
    dp.include_router(states.router)

    return bot, dp


main_bot, main_dp = bot_init()


async def process_event(event, bot: Bot, dp: Dispatcher):
    """
    Converting a Yandex.Cloud functions event to an update and
    handling the update.
    """

    update = json.loads(event['body'])
    await dp.feed_raw_update(bot, update)


async def handler(event, context):
    """Yandex.Cloud functions handler."""

    if event['httpMethod'] == 'POST':

        await set_commands(main_bot)
        try:
            await process_event(event, main_bot, main_dp)
        except Exception:
            raise
        finally:
            return {'statusCode': 200}

    return {'statusCode': 405}


async def start():
    """Start long polling for tests"""
    await main_bot.delete_webhook(drop_pending_updates=True)
    await set_commands(main_bot)
    await main_dp.start_polling(main_bot)


if __name__ == '__main__':
    asyncio.run(start())
