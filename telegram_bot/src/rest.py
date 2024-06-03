import aiohttp
import asyncio
import logging as log

from .settings.config import URL_REST, MAX_CONNECTIONS


class Schedule_Service_API:
    def __init__(self, url_rest=URL_REST, max_connections=MAX_CONNECTIONS) -> None:
        self.url_rest = url_rest
        self.session = aiohttp.ClientSession(auth=aiohttp.BasicAuth("admin", "admin"))
        self.semaphore = asyncio.Semaphore(max_connections)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_pathways(self):
        url_pathways = f"{self.url_rest}/pathways"
        async with self.semaphore:
            async with self.session.get(url_pathways) as response:
                if response.status == 200:
                    log.info("Pathways has been recieved from REST API.")
                    data = await response.json()
                    return data
                else:
                    response_json = await response.json()
                    log.critical(
                        f"Pathways has not been recieved from REST API.\n{response_json}"
                    )
                    return None

    async def get_last_update(self):
        url_last_update = f"{self.url_rest}/timetable"
        async with self.semaphore:
            async with self.session.get(url_last_update) as response:
                if response.status == 200:
                    log.info("Last update has been recieved from REST API.")
                    data = await response.json()
                    return data
                else:
                    response_json = await response.json()
                    log.critical(
                        f"Last update has not been recieved from REST API.\n{response_json}"
                    )
                    return None

    async def get_groups(self, pathway_id: int):
        url_groups = f"{self.url_rest}/groups"
        params = {"pathwayId": pathway_id}
        async with self.semaphore:
            async with self.session.get(url_groups, params=params) as response:
                if response.status == 200:
                    log.info("Groups has been recieved from REST API.")
                    data = await response.json()
                    return data
                else:
                    response_json = await response.json()
                    log.critical(
                        f"Groups has not been recieved from REST API.\n{response_json}"
                    )
                    return None

    async def get_lessons_week(self, group_id: int):
        url_schedule = f"{self.url_rest}/lessons/groups/{group_id}/week"
        async with self.semaphore:
            async with self.session.get(url_schedule) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                        log.info("Data has been recieved from REST API.")
                        return data
                    except aiohttp.ContentTypeError:
                        return log.critical(
                            "Data has NOT been recieved from REST API.\n"
                            "The server returned an unsupported content type.\n"
                            f"text: '{await response.text()}'"
                        )

                else:
                    response_json = await response.json()
                    return log.critical(
                        f"Data has not been recieved from REST API.\n{response_json}"
                    )

    async def get_lessons_day(self, group_id: int):
        url_schedule = f"{self.url_rest}/lessons/groups/{group_id}/day"
        async with self.semaphore:
            async with self.session.get(url_schedule) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                        log.info("Data has been recieved from REST API.")
                        return data
                    except aiohttp.ContentTypeError:
                        return log.critical(
                            "Data has NOT been recieved from REST API.\n"
                            "The server returned an unsupported content type.\n"
                            f"text: '{await response.text()}'"
                        )

                else:
                    response_json = await response.json()
                    return log.critical(
                        f"Data has not been recieved from REST API.\n{response_json}"
                    )


async def get_pathways():
    async with Schedule_Service_API() as api:
        return await api.get_pathways()


async def get_last_update():
    async with Schedule_Service_API() as api:
        data: dict[str, str] = await api.get_last_update()
        return data["addDate"][:10], data["id"]


async def get_groups(pathway_id: int):
    async with Schedule_Service_API() as api:
        return await api.get_groups(pathway_id)


async def get_lessons_week(group_id: int):
    async with Schedule_Service_API() as api:
        return await api.get_lessons_week(group_id)


async def get_lessons_day(group_id: int):
    async with Schedule_Service_API() as api:
        return await api.get_lessons_day(group_id)
