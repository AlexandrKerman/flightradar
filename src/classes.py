import asyncio
import json
from copy import deepcopy
from functools import wraps
from os import getenv
from pathlib import Path
from typing import Any, Generator, Optional

import aiohttp
from dotenv import load_dotenv

from src import base_classes as bc

load_dotenv()
OPENSKY_API = getenv("OPENSKY_API")
OPENSKY_CLIENT = getenv("OPENSKY_CLIENT")


class AeroplanesAPI(bc.BaseAPI):
    __slots__ = ("__aeroplanes", "__box", "__token")
    __openstreet_url = "https://nominatim.openstreetmap.org"
    __opensky_url = "https://opensky-network.org/api"

    def __init__(self):
        self.__aeroplanes = []
        self.__box = {}
        self.__token = None

    async def __get_token(self) -> None:
        async with aiohttp.ClientSession() as session:
            data = {
                "grant_type": "client_credentials",
                "client_id": OPENSKY_CLIENT,
                "client_secret": OPENSKY_API,
            }
            url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
            async with session.post(url, data=data) as response:
                self.__token = (await response.json()).get("access_token")

    @staticmethod
    def retry_connection(limit: int = 5):
        def wrapper(func):
            @wraps(func)
            async def inner(*args, **kwargs) -> aiohttp.ClientResponse | None:
                for i in range(limit):
                    print(f"Попытка подключения к {args[0]}...")
                    res = await func(*args, **kwargs)
                    if res.status == 200:
                        print("Ok")
                        return res
                return None

            return inner

        return wrapper

    async def __get_request(self, url, headers=None, params=None) -> Optional[Any]:
        response = await self.__connect(url, headers, params)
        if response:
            return await response.json()
        print("Error. Attempts limited.")

    @staticmethod
    @retry_connection()
    async def __connect(url: str, headers: dict | None = None, params: dict | None = None) -> aiohttp.ClientResponse:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                await response.read()
                return response

    async def set_box(self, country: str) -> None:
        url = f"{self.__openstreet_url}/search"
        header = {"User-Agent": "aeroplanes-app"}
        payload = {"country": country, "format": "json", "limit": 1}
        box = (await self.__get_request(url, header, payload))[0].get("boundingbox")
        if box:
            self.__box = {"lamin": box[0], "lamax": box[1], "lomin": box[2], "lomax": box[3]}

    async def get_aeroplanes(self, country: str | None = None) -> None:
        url = f"{self.__opensky_url}/states/all"
        if not self.__token:
            await self.__get_token()
        header = {"Authorization": f"Bearer {self.__token}"}
        data = await self.__get_request(url, params=self.__box, headers=header)
        if data:
            if aeroplanes := data.get("states"):
                self.__aeroplanes = [
                    {
                        "ICAO24": i[0].strip(),
                        "Callsign": i[1].strip() if i[1].strip() else "Unknown",
                        "country": i[2].strip(),
                        "time_position": i[3],
                        "last_contact": i[4],
                        "lon": i[5],
                        "lat": i[6],
                        "baro_altitude": i[7],
                        "on_ground": i[8],
                        "velocity": i[9],
                        "true_track": i[10],
                        "vertical_rate": i[11],
                        "sensors": i[12],
                        "geo_altitude": i[13],
                        "squawk": i[14],
                        "spi": i[15],
                        "position_source": i[16],
                    }
                    for i in aeroplanes if i
                ]
            else:
                print("Not states key")
        else:
            print(f"No data: {data}")

    @property
    def aeroplanes(self) -> list:
        return deepcopy(self.__aeroplanes)


class Aeroplane(bc.BaseAeroplane):
    __slots__ = (
        "ICAO24",
        "Callsign",
        "country",
        "time_position",
        "last_contact",
        "lon",
        "lat",
        "baro_altitude",
        "on_ground",
        "velocity",
        "true_track",
        "vertical_rate",
        "sensors",
        "geo_altitude",
        "squawk",
        "spi",
        "position_source",
    )

    def __init__(self, **kwargs):
        if kwargs:
            for attr in self.__slots__:
                setattr(self, attr, kwargs.get(attr))

    def __iter__(self):
        self.index = -1
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.__slots__):
            return self.__slots__[self.index], self.__getattribute__(self.__slots__[self.index])
        raise StopIteration

    def __comparison_tuple(self):
        if all((self.baro_altitude, self.velocity)):
            return self.baro_altitude, self.velocity
        return self.baro_altitude if self.baro_altitude else 0, self.velocity if self.velocity else 0

    def __lt__(self, other) -> bool:
        if isinstance(other, Aeroplane):
            return self.__comparison_tuple() < other.__comparison_tuple()
        raise TypeError(f"Expected Aeroplane object. Got {type(other)}")

    def __le__(self, other) -> bool:
        if isinstance(other, Aeroplane):

            if all((self.baro_altitude, self.velocity, other.baro_altitude, other.velocity)):
                return self.__comparison_tuple() <= other.__comparison_tuple()

        raise TypeError(f"Expected Aeroplane object. Got {type(other)}")

    def __gt__(self, other) -> bool:
        if isinstance(other, Aeroplane):

            if all((self.baro_altitude, self.velocity, other.baro_altitude, other.velocity)):
                return self.__comparison_tuple() > other.__comparison_tuple()

        raise TypeError(f"Expected Aeroplane object. Got {type(other)}")

    def __ge__(self, other) -> bool:
        if isinstance(other, Aeroplane):

            if all((self.baro_altitude, self.velocity, other.baro_altitude, other.velocity)):
                return self.__comparison_tuple() >= other.__comparison_tuple()

        raise TypeError(f"Expected Aeroplane object. Got {type(other)}")

    def __eq__(self, other) -> bool:
        if isinstance(other, Aeroplane):

            if all((self.baro_altitude, self.velocity, other.baro_altitude, other.velocity)):
                return self.__comparison_tuple() == other.__comparison_tuple

        raise TypeError(f"Expected Aeroplane object. Got {type(other)}")

    def __repr__(self) -> str:
        return f"Aeroplane({', '.join([f'{i}={self.__getattribute__(i)}' for i in self.__slots__])})"

    def __str__(self) -> str:
        return (
            f"{self.Callsign} ({self.ICAO24}) in {self.country} have velocity {self.velocity} "
            f"and flies in {self.baro_altitude if self.baro_altitude else 0} above the sea level."
        )

    def __bool__(self) -> bool:
        return all((self.baro_altitude, self.velocity))

    def __getitem__(self, item):
        if isinstance(item, str):
            if item in self.__slots__:
                return self.__getattribute__(item)
            return None
        elif isinstance(item, int):
            return self.__getattribute__(self.__slots__[item])
        raise TypeError(f"Expected int or str. Got {type(item)}: {item}")

    @classmethod
    def cast_to_aeroplane_gen(cls, aeroplanes) -> Generator:
        for i in aeroplanes:
            yield cls(**i)

    @classmethod
    def cast_to_aeroplane(cls, aeroplanes) -> list:
        aeroplanes_ = []
        for i in aeroplanes:
            if i in aeroplanes_:
                print(f'Not unique: {i.get('Callsign')} ({i.get('ICAO24')})')
                continue
            aeroplanes_.append(i)
        return [cls(**i) for i in aeroplanes_]

    def get_in_dict(self):
        return {k: self.__getattribute__(k) for k in self.__slots__}

    @staticmethod
    def filter_by_country(countries: list[str], planes: list | tuple) -> list:
        return [i for i in planes if i.country in countries]

    def filter_predicate(self, countries: list):
        return self.country in countries

    @staticmethod
    def get_top(data: list['Aeroplane'] | tuple['Aeroplane'], top_n: int = 5) -> list:
        return [i for i in sorted(filter (lambda x: x.baro_altitude, data), key=lambda x: x.baro_altitude)][:5]

    @staticmethod
    def filter_by_range(data: list['Aeroplane'] | tuple['Aeroplane'], range_: tuple[int, int]) -> list:
        return [i for i in data if i.baro_altitude and range_[0] <= i.baro_altitude <= range_[1]]

    @staticmethod
    def filter_by_ground (data: list['Aeroplane'] | tuple['Aeroplane'], is_grounded: bool) -> list:
        return [i for i in data if i.on_ground == is_grounded]

    @staticmethod
    def get_slice(data: list['Aeroplane'] | tuple['Aeroplane'], head: int = 3, tail: int = 2):
        return data[:head].extend(data[tail:])

class JSONSaver(bc.BaseFile):
    __slots__ = ("path", "data")

    def __init__(self, file_path: str, file_name: str):
        self.path = Path(file_path) / file_name
        if self.path.suffix != ".json":
            self.path = self.path.with_suffix(".json")
        self.data = []
        self.__create_path()

    def __create_path(self):
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.touch()
            if self.data:
                with open(self.path, 'w') as file:
                    json.dump('[]', file)
            else:
                self.save_file()


    def update_data(self, data: list) -> None:
        if isinstance(data, list):
            self.data = [i.get_in_dict() for i in data]
        else:
            raise TypeError(f"expected list. Got {type(data)}")

    def add_aeroplane(self, aeroplane) -> None:
        self.data.append(aeroplane.get_in_dict())

    def delete_aeroplane(self, board_id) -> None:
        for i in self.data:
            if i["ICAO24"] == board_id:
                self.data.remove(i)
                break

    def read_aeroplane(self) -> None:
        self.__create_path()
        with open(self.path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    def save_file(self) -> None:
        self.__create_path()
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2, ensure_ascii=False)

    def get_fullpath(self):
        return Path.resolve(self.path)

async def main() -> None:
    # api = AeroplanesAPI()
    # await api.set_box('China')
    # await api.get_aeroplanes('China')
    # aeroplanes = api.aeroplanes
    # aeroplanes = Aeroplane.cast_to_aeroplane(aeroplanes[:3])
    # # print(*aeroplanes, sep='\n\n')
    saver = JSONSaver("../data", "test")
    # for i in aeroplanes:
    #     saver.add_aeroplane(i)
    # print(*saver.data, sep='\n\n')
    # saver.delete_aeroplane('781c77')
    # print()
    # print()
    # print()
    # print(*saver.data, sep='\n\n')
    # saver.save_file()

    saver.read_aeroplane()
    print(json.dumps(saver.data, indent=2))
    planes = Aeroplane.cast_to_aeroplane(saver.data)
    print(planes)


if __name__ == "__main__":
    asyncio.run(main())
