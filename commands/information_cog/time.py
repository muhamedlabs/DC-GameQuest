import asyncio
import sys
from datetime import datetime, timedelta

from BANNED_FILES.config import Time_interval, Update_Interval


def _get_moscow_time() -> str:
    return (datetime.utcnow() + timedelta(hours=3)
    ).strftime("%Y-%m-%d %H:%M:%S")


def _get_kyiv_time() -> str:
    return (datetime.utcnow() + timedelta(hours=2)
    ).strftime("%Y-%m-%d %H:%M:%S")


def _get_hours_time() -> str:
    return (datetime.utcnow() + timedelta(hours=Time_interval)
    ).strftime("%d.%m.%Y %H:%M:%S")


moscow_time = _get_moscow_time()
kyiv_time = _get_kyiv_time()
hours_time = _get_hours_time()


def _update_imported_modules():

    global hours_time
    global moscow_time
    global kyiv_time

    # Получаем новые значения
    new_hours_time = _get_hours_time()
    new_moscow_time = _get_moscow_time()
    new_kyiv_time = _get_kyiv_time()

    # Обновляем переменные самого time.py
    hours_time = new_hours_time
    moscow_time = new_moscow_time
    kyiv_time = new_kyiv_time

    updated_modules = 0

    # Перебираем все загруженные модули
    for module_name, module in list(sys.modules.items()):

        if module is None:
            continue

        try:
            module_dict = vars(module)

            # ----------------------------------------
            # hours_time
            # ----------------------------------------

            if "hours_time" in module_dict:

                # Не трогаем сам этот модуль
                if module is not sys.modules[__name__]:

                    module_dict["hours_time"] = new_hours_time
                    updated_modules += 1

            # ----------------------------------------
            # moscow_time
            # ----------------------------------------

            if "moscow_time" in module_dict:

                if module is not sys.modules[__name__]:
                    module_dict["moscow_time"] = new_moscow_time

            # ----------------------------------------
            # kyiv_time
            # ----------------------------------------

            if "kyiv_time" in module_dict:

                if module is not sys.modules[__name__]:
                    module_dict["kyiv_time"] = new_kyiv_time

        except Exception:
            continue


_time_updater_task = None


async def _time_updater():

    # Первое обновление сразу после запуска
    _update_imported_modules()

    while True:

        try:
            await asyncio.sleep(Update_Interval)

            _update_imported_modules()

        except asyncio.CancelledError:
            break

        except Exception as error:
            print(f"[TIME] Update error: {error}")

            # Если произошла ошибка, не убиваем задачу
            await asyncio.sleep(5)


def start_time_updater():

    global _time_updater_task

    if (
        _time_updater_task is None
        or _time_updater_task.done()
    ):
        _time_updater_task = asyncio.create_task(
            _time_updater()
        )

    return _time_updater_task


def current_time() -> str:     
    return (datetime.utcnow() + 
            timedelta(hours=Time_interval)).strftime("%d.%m.%Y %H:%M:%S") 

def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%d.%m.%Y %H:%M:%S")