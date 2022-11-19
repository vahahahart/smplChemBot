from typing import Union
from json import loads

from aiogram.filters import Text
from aiogram.filters.command import Command
from aiogram.dispatcher.router import Router
from aiogram.types import Message, CallbackQuery

from driver_init import main_driver as driver
from bot.text import msg_START, msg_HELP
from bot.keyboard_utils import stat_menu_kb, set_menu_kb

router = Router()


@router.message(Command(commands=['start']))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not await driver.check_user(user_id):
        await driver.add_user(user_id)
    await driver.update_data(user_id, datasets_list='[]', datasets='{}')
    await message.answer('<b>STARTING - smplChem_bot\n</b>' + msg_START)


@router.message(Command(commands=['help']))
async def cmd_help(message: Message):
    await message.answer('<b>HELP\n</b>' + msg_HELP)


@router.message(Command(commands=['cancel']))
async def cmd_cancel(message: Message):
    user_id = message.from_user.id
    state = await driver.get_data(user_id, 'state')
    if state:
        await driver.update_data(user_id, state=None)
        await message.answer(f'Current state "{state}" has been reset.')
    else:
        await message.answer('No active state to cancel')


@router.callback_query(Text(text='STAT'))
@router.message(Command(commands=['statistics']))
async def cmd_statistics(obj: Union[Message, CallbackQuery]):
    user_id = obj.from_user.id
    exist_datasets = await driver.get_data(user_id, 'datasets_list')
    builder = stat_menu_kb(loads(exist_datasets))
    k_args = {'text': 'Choose a dataset from the list below or create a new one:', 'reply_markup': builder.as_markup()}
    if isinstance(obj, Message):
        await obj.answer(**k_args)
    else:
        await obj.message.edit_text(**k_args)


@router.message(Command(commands=['mol_weights']))
async def set_mol_weights_calc(message: Message):
    user_id = message.from_user.id
    await driver.update_data(user_id, state='MOL-WEIGHTS-CALC')
    await message.answer(f'Type a formula to calculate the molecular weight:')


@router.message(Command(commands=['current']))
async def display_current_dataset(message: Message):
    user_id = message.from_user.id
    state = await driver.get_data(user_id, 'state')
    if state:
        action, dataset_name = state.split('-')
        if action == 'FILL':
            full_data = await driver.get_data(user_id, 'datasets')
            try:
                full_data = loads(full_data)[dataset_name]
            except KeyError:
                await message.answer('Current dataset not found')
            builder = set_menu_kb(dataset_name)
            await message.answer(
                f'Dataset <b>{dataset_name}</b>:\n{full_data}\n\nActions:',
                reply_markup=builder.as_markup()
            )
            return
    await message.answer('No active dataset to display')
