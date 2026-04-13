import json
from unittest.mock import AsyncMock

import pytest

from src.classes import Aeroplane


@pytest.fixture()
def aeroplanes_json():
    aeroplanes = """[
        {
            "ICAO24": "7809ab",
            "Callsign": "CQH6760",
            "country": "China",
            "time_position": 1775729998,
            "last_contact": 1775729998,
            "lon": 123.9414,
            "lat": 39.2658,
            "baro_altitude": 10698.48,
            "on_ground": false,
            "velocity": 212.99,
            "true_track": 184.02,
            "vertical_rate": 0.33,
            "sensors": null,
            "geo_altitude": 10881.36,
            "squawk": null,
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "781a8a",
            "Callsign": "CCA1139",
            "country": "China",
            "time_position": 1775730059,
            "last_contact": 1775730059,
            "lon": 116.2699,
            "lat": 40.1663,
            "baro_altitude": 4747.26,
            "on_ground": false,
            "velocity": 179.68,
            "true_track": 237.63,
            "vertical_rate": 11.38,
            "sensors": null,
            "geo_altitude": 4648.2,
            "squawk": null,
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "781afd",
            "Callsign": "CSN3038",
            "country": "China",
            "time_position": 1775730058,
            "last_contact": 1775730058,
            "lon": 114.1166,
            "lat": 21.8953,
            "baro_altitude": 6096,
            "on_ground": false,
            "velocity": 206.37,
            "true_track": 333.5,
            "vertical_rate": 0.33,
            "sensors": null,
            "geo_altitude": 6477,
            "squawk": null,
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "781bb5",
            "Callsign": "CQH7507",
            "country": "China",
            "time_position": 1775730059,
            "last_contact": 1775730059,
            "lon": 114.8094,
            "lat": 22.7896,
            "baro_altitude": 7917.18,
            "on_ground": false,
            "velocity": 234.52,
            "true_track": 83.58,
            "vertical_rate": -11.05,
            "sensors": null,
            "geo_altitude": 8435.34,
            "squawk": null,
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "781bab",
            "Callsign": "DKH2010",
            "country": "China",
            "time_position": 1775729775,
            "last_contact": 1775729775,
            "lon": 114.2813,
            "lat": 23.8191,
            "baro_altitude": 9494.52,
            "on_ground": false,
            "velocity": 256.33,
            "true_track": 37.74,
            "vertical_rate": 0,
            "sensors": null,
            "geo_altitude": 10104.12,
            "squawk": null,
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "780a7a",
            "Callsign": "Unknown",
            "country": "China",
            "time_position": 1775730030,
            "last_contact": 1775730030,
            "lon": 113.9148,
            "lat": 22.3125,
            "baro_altitude": null,
            "on_ground": true,
            "velocity": 5.92,
            "true_track": 160.31,
            "vertical_rate": null,
            "sensors": null,
            "geo_altitude": null,
            "squawk": null,
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "780a7b",
            "Callsign": "HKC963",
            "country": "China",
            "time_position": 1775730059,
            "last_contact": 1775730060,
            "lon": 121.0391,
            "lat": 24.8029,
            "baro_altitude": 12192,
            "on_ground": false,
            "velocity": 219.35,
            "true_track": 229.66,
            "vertical_rate": 0,
            "sensors": null,
            "geo_altitude": 12954,
            "squawk": "3775",
            "spi": false,
            "position_source": 0
        },
        {
            "ICAO24": "780a7e",
            "Callsign": "CPA421",
            "country": "China",
            "time_position": 1775729899,
            "last_contact": 1775730058,
            "lon": 113.9844,
            "lat": 22.0426,
            "baro_altitude": 1821.18,
            "on_ground": false,
            "velocity": 128.32,
            "true_track": 307.83,
            "vertical_rate": -2.6,
            "sensors": null,
            "geo_altitude": 1859.28,
            "squawk": null,
            "spi": false,
            "position_source": 0
        }
    ]
    """
    return aeroplanes


@pytest.fixture
def sample_plane_dict():
    return {
        "ICAO24": "7809ab",
        "Callsign": "CQH6760",
        "country": "China",
        "time_position": 1775729998,
        "last_contact": 1775729998,
        "lon": 123.9414,
        "lat": 39.2658,
        "baro_altitude": 10698.48,
        "on_ground": False,
        "velocity": 212.99,
        "true_track": 184.02,
        "vertical_rate": 0.33,
        "sensors": None,
        "geo_altitude": 10881.36,
        "squawk": None,
        "spi": False,
        "position_source": 0,
    }


@pytest.fixture
def sample_plane(sample_plane_dict):
    return Aeroplane(**sample_plane_dict)


@pytest.fixture
def planes_list(aeroplanes_json):
    data = json.loads(aeroplanes_json)
    return Aeroplane.cast_to_aeroplane(data)


@pytest.fixture
def mock_client_session():
    def create_mock_response(status=200, json_data=None):
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=json_data or {})
        mock_resp.read = AsyncMock(return_value=None)
        return mock_resp

    def create_mock_context(response):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = response
        return mock_ctx

    return create_mock_response, create_mock_context
