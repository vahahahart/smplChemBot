from os import getenv

if getenv('START') == 'LOCAL':
    from database.SQLite_db import BotDB
    main_driver = BotDB('database/bot.db')
else:
    from database.ydb_driver import YDBDriver
    main_driver = YDBDriver(
        table_name=getenv('TABLE_NAME'),
        endpoint=getenv('YDB_ENDPOINT'),
        database=getenv('YDB_DATABASE')
    )
