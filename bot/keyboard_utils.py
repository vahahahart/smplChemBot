from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


back_button = InlineKeyboardButton(
    text='« Back',
    callback_data='STAT'
)


def stat_menu_kb(exist_datasets):
    builder = InlineKeyboardBuilder()
    if exist_datasets:
        for name in exist_datasets:
            builder.add(
                InlineKeyboardButton(
                    text=name,
                    callback_data=f'SET-{name}'
                )
            )
    builder.add(
        InlineKeyboardButton(
            text='Create new...',
            callback_data='CREATE'
        )
    )
    builder.adjust(3)
    return builder


def set_menu_kb(set_name):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Add data',
            callback_data=f'FILL-{set_name}'),
        InlineKeyboardButton(
            text='Get statistics',
            callback_data=f'CALC-{set_name}'),
        InlineKeyboardButton(
            text='Remove last value',
            callback_data=f'REMOVELAST-{set_name}'),
        back_button,
        InlineKeyboardButton(
            text='Delete dataset',
            callback_data=f'DELETE-{set_name}')
    )
    builder.adjust(3)
    return builder
