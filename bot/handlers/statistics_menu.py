from json import loads, dumps
from contextlib import suppress

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Text, Filter
from aiogram.dispatcher.router import Router
from aiogram.types import CallbackQuery

from driver_init import main_driver as driver
from bot.keyboard_utils import set_menu_kb, stat_menu_kb
from calculations.statistics_calculator import StatisticsSet

router = Router()

class DataSetActionFilter(Filter):
    def __init__(self, action: str):
        self.action = action

    async def __call__(self, callback: CallbackQuery):
        user_id = callback.from_user.id
        callback_action, dataset_name = callback.data.split('-')
        if callback_action == self.action:
            try:
                full_data = await driver.get_data(user_id, 'datasets')
                full_data = loads(full_data)
                dataset = full_data[dataset_name]
            except KeyError:
                await callback.message.edit_text('Current dataset not found')
                await callback.answer()
                return
            return {'dataset_name': dataset_name, 'user_id': user_id, 'dataset': dataset, 'full_data': full_data}
        return False


@router.callback_query(Text(text='CREATE'))
async def menu_callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await driver.update_data(user_id, state='DATASET-NAME')
    await callback.message.edit_text('Choose a name for your dataset (name must contains less then 10 characters).')
    await callback.answer()


@router.callback_query(DataSetActionFilter('SET'))
async def dataset_menu(callback: CallbackQuery, dataset_name: str, dataset):
    builder = set_menu_kb(dataset_name)
    await callback.message.edit_text(
        f'Dataset <b>{dataset_name}</b>:\n{dataset}\n\nActions:',
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(DataSetActionFilter('FILL'))
async def fill_dataset(callback: CallbackQuery, dataset_name, user_id):
    await driver.update_data(user_id, state=f'FILL-{dataset_name}')
    await callback.message.edit_text(
        f'Now you can fill dataset <b>{dataset_name}</b>.\n\nUse /cancel to stop filling and /current to display active dataset.'
    )
    await callback.answer()


@router.callback_query(DataSetActionFilter('CALC'))
async def calc_dataset(callback: CallbackQuery, dataset_name, dataset):
    builder = set_menu_kb(dataset_name)
    try:
        prepared_set = StatisticsSet(dataset)
        descr = prepared_set.descr(prec=None, form=('<code>', '</code>'))
    except ValueError:
        await callback.message.edit_text(
            f'Dataset must contains numbers only!',
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    msg_string = f'Dataset <b>{dataset_name}</b>:\n{dataset}\n\n'
    msg_string += 'N:  {N}\nMin:  {min}\nMax:  {max}\nMean:  {mean}\nStd:  {std}\nConf int:  {conf_int}\n'
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            msg_string.format(**descr) + '\nActions:', reply_markup=builder.as_markup()
        )
        await callback.answer()


@router.callback_query(DataSetActionFilter('REMOVELAST'))
async def removelast_dataset(callback: CallbackQuery, dataset_name, user_id, dataset, full_data):
    builder = set_menu_kb(dataset_name)
    try:
        removed = dataset.pop()
    except IndexError:
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(
                f'Dataset <b>{dataset_name}</b>:\n{dataset}\n\nDataset is empty!\n\nActions:',
                reply_markup=builder.as_markup()
            )
            await callback.answer()
        return
    await driver.update_data(user_id, datasets=dumps(full_data))
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            f'Dataset <b>{dataset_name}</b>:\n{dataset}\n\nRemoved element:  <code>{removed}</code>\n\nActions:',
            reply_markup=builder.as_markup()
        )
        await callback.answer()


@router.callback_query(DataSetActionFilter('DELETE'))
async def delete_dataset(callback: CallbackQuery, dataset_name, user_id, full_data):
    datasets_list = await driver.get_data(user_id, 'datasets_list')
    datasets_list = set(loads(datasets_list))

    try:
        datasets_list.discard(dataset_name)
        full_data.pop(dataset_name)
    except KeyError:
        await callback.message.edit_text('Dataset already has been delete.')
        await callback.answer()
        return

    await driver.update_data(user_id, datasets_list=dumps(list(datasets_list)))
    await driver.update_data(user_id, datasets=dumps(full_data))

    exist_datasets = await driver.get_data(user_id, 'datasets_list')
    builder = stat_menu_kb(loads(exist_datasets))
    await callback.message.edit_text(
        f'Dataset <b>{dataset_name}</b> has been deleted\n\nChoose a dataset from the list below or create a new one:',
        reply_markup=builder.as_markup()
    )
