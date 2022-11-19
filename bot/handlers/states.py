from json import JSONEncoder, loads, dumps

from aiogram import F
from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.dispatcher.router import Router

from driver_init import main_driver as driver
from calculations.weight_calculator import formula_to_weight

router = Router()


class SetEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)


class StateFilter(Filter):
    def __init__(self, state: str):
        self.state = state

    async def __call__(self, message: Message):
        user_id = message.from_user.id
        user_state = await driver.get_data(user_id, 'state')
        if message.text and user_state and user_state.find(self.state) >= 0:
            return {'dataset_name': user_state.split('-')[1]}
        return False


@router.message(StateFilter(state='MOL-WEIGHTS-CALC'))
async def get_weight(message: Message):
    try:
        weight = formula_to_weight(message.text)
    except KeyError:
        await message.answer(f'Element out of list!')
        return
    await message.answer(f'Molecular weight:\n<code>{weight}</code>')


@router.message(StateFilter(state='DATASET'))
async def set_name(message: Message):
    user_id = message.from_user.id
    name = message.text

    if len(name) > 10:
        await message.answer(f'Name contains more than 10 characters!')
        return

    datasets_list = await driver.get_data(user_id, 'datasets_list')
    if datasets_list:
        datasets_list = set(loads(datasets_list))
        datasets_list.add(name)
    else:
        datasets_list = {name, }
    await driver.update_data(user_id, datasets_list=dumps(datasets_list, cls=SetEncoder))

    datasets = await driver.get_data(user_id, 'datasets')
    if datasets:
        datasets = loads(datasets)
    else:
        datasets = {}
    datasets.update({name: []})
    await driver.update_data(user_id, datasets=dumps(datasets))

    await driver.update_data(user_id, state=f'FILL-{name}')
    await message.answer(
        'Now you can fill this dataset.\n\nUse /cancel to stop filling and /current to display active dataset.'
    )


@router.message(StateFilter(state='FILL'), F.text.regexp(r'^[\d]*[.,]?[\d]*[eE]?[\+\-]?[\d]+'))
async def fill_dataset(message: Message, dataset_name: str):
    user_id = message.from_user.id
    data = message.text.replace(',', '.')
    full_data = await driver.get_data(user_id, 'datasets')
    full_data = loads(full_data)
    full_data[dataset_name].append(data)
    await driver.update_data(user_id, datasets=dumps(full_data))
    await message.answer(f'{data} added to <b>{dataset_name}</b>')
