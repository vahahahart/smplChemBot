import asyncio
import ydb


async def execute_query(pool, query, param=None):
    # checkout a session to execute query.
    with pool.async_checkout() as session_holder:
        try:
            # wait for the session checkout to complete.
            session = await asyncio.wait_for(
                asyncio.wrap_future(session_holder), timeout=5
            )
        except asyncio.TimeoutError:
            raise ydb.SessionPoolEmpty('SessionPoolEmpty')

        prepared_query = session.prepare(query)

        return await asyncio.wrap_future(
            session.transaction().async_execute(
                query=prepared_query,
                parameters=param,
                commit_tx=True,
                settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2),
            )
        )


class YDBDriver:
    def __init__(self, table_name, endpoint, database):
        self.table = table_name
        driver = ydb.Driver(endpoint=endpoint, database=database)
        self.session_pool = ydb.SessionPool(driver)
        self.cached = {}

    async def check_user(self, user_id):
        query = f'DECLARE $user_id AS Uint64;\nSELECT user_id FROM `{self.table}` WHERE user_id = $user_id;'
        param = {'$user_id': user_id}
        result = await ydb.aio.retry_operation(execute_query, None, self.session_pool, query, param)
        return bool(result[0].rows)

    async def add_user(self, user_id):
        query = f'DECLARE $user_id AS Uint64;\nINSERT INTO `{self.table}` (user_id) VALUES ($user_id);'
        param = {'$user_id': user_id}
        await ydb.aio.retry_operation(execute_query, None, self.session_pool, query, param)

    async def update_data(self, user_id, **data):

        if str(user_id) in self.cached:
            self.cached[str(user_id)].update(**data)
        else:
            self.cached.update({str(user_id): data})

        declare_query = 'DECLARE $user_id AS Uint64;\n'
        update_query = f'UPDATE `{self.table}` SET '
        query_list = []
        param = {'$user_id': user_id}
        for key, value in data.items():
            declare_query += f'DECLARE ${key} AS Utf8?;\n'
            query_list.append(f'{key} = ${key}')
            param.update({f'${key}': value})
        query = declare_query + update_query + ', '.join(query_list) + ' WHERE user_id = $user_id;'
        await ydb.aio.retry_operation(execute_query, None, self.session_pool, query, param)

    async def get_data(self, user_id, data):

        if str(user_id) in self.cached:
            if data in self.cached[str(user_id)]:
                return self.cached[str(user_id)][data]
        else:
            self.cached.update({str(user_id): {}})

        get_query = 'DECLARE $user_id AS Uint64; SELECT {} FROM `{}` WHERE user_id = $user_id;'
        query = get_query.format(data, self.table)
        param = {'$user_id': user_id}
        results = await ydb.aio.retry_operation(execute_query, None, self.session_pool, query, param)
        result = list(results[0].rows[0].values())[0]
        self.cached[str(user_id)].update({data: result})
        return result

    async def get_data_dict(self, user_id, *data_list):
        get_query = 'DECLARE $user_id AS Uint64; SELECT {} FROM `{}` WHERE user_id = $user_id;'
        query = get_query.format(', '.join(data_list), self.table)
        param = {'$user_id': user_id}
        results = await ydb.aio.retry_operation(execute_query, None, self.session_pool, query, param)
        return dict(zip(data_list, list(results[0].rows[0].values())))
