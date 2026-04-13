import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.classes import Aeroplane, AeroplanesAPI, JSONSaver


def test_init():
    api = AeroplanesAPI()
    assert api._AeroplanesAPI__aeroplanes == []
    assert api._AeroplanesAPI__box == {}
    assert api._AeroplanesAPI__token is None


@pytest.mark.asyncio
async def test_get_token(mock_client_session):
    create_mock_response, create_mock_context = mock_client_session
    mock_response = create_mock_response(json_data={"access_token": "fake_token"})
    mock_context = create_mock_context(mock_response)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_context
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        api = AeroplanesAPI()
        await api._AeroplanesAPI__get_token()
        assert api._AeroplanesAPI__token == "fake_token"


@pytest.mark.asyncio
async def test_connect_success(mock_client_session):
    create_mock_response, create_mock_context = mock_client_session
    url = "https://example.com"
    mock_response = create_mock_response(status=200)
    mock_context = create_mock_context(mock_response)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_context
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        response = await AeroplanesAPI._AeroplanesAPI__connect(url)
        assert response.status == 200


@pytest.mark.asyncio
async def test_connect_retry_failure(mock_client_session):
    create_mock_response, create_mock_context = mock_client_session
    url = "https://example.com"
    mock_response = create_mock_response(status=500)
    mock_context = create_mock_context(mock_response)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_context
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        response = await AeroplanesAPI._AeroplanesAPI__connect(url)
        assert response is None


@pytest.mark.asyncio
async def test_get_request():
    api = AeroplanesAPI()
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"key": "value"})

    with patch.object(api, "_AeroplanesAPI__connect", return_value=mock_response) as mock_conn:
        result = await api._AeroplanesAPI__get_request("url")
        assert result == {"key": "value"}
        mock_conn.assert_called_once_with("url", None, None)


@pytest.mark.asyncio
async def test_set_box():
    api = AeroplanesAPI()
    mock_geocode_response = [{"boundingbox": ["10", "20", "30", "40"]}]

    with patch.object(api, "_AeroplanesAPI__get_request", return_value=mock_geocode_response) as mock_get:
        await api.set_box("TestCountry")
        mock_get.assert_called_once()
        assert api._AeroplanesAPI__box == {"lamin": "10", "lamax": "20", "lomin": "30", "lomax": "40"}


@pytest.mark.asyncio
async def test_set_box_no_data():
    api = AeroplanesAPI()
    with patch.object(api, "_AeroplanesAPI__get_request", return_value=[]):
        with pytest.raises(IndexError):
            await api.set_box("Unknown")


@pytest.mark.asyncio
async def test_get_aeroplanes_with_token():
    api = AeroplanesAPI()
    api._AeroplanesAPI__token = "existing_token"
    api._AeroplanesAPI__box = {"lamin": "1", "lamax": "2", "lomin": "3", "lomax": "4"}
    mock_data = {
        "states": [
            [
                "7809ab",
                "CQH6760",
                "China",
                1775729998,
                1775729998,
                123.9414,
                39.2658,
                10698.48,
                False,
                212.99,
                184.02,
                0.33,
                None,
                10881.36,
                None,
                False,
                0,
            ]
        ]
    }

    with patch.object(api, "_AeroplanesAPI__get_request", return_value=mock_data) as mock_get:
        await api.get_aeroplanes()
        mock_get.assert_called_once_with(
            f"{api._AeroplanesAPI__opensky_url}/states/all",
            params=api._AeroplanesAPI__box,
            headers={"Authorization": "Bearer existing_token"},
        )
        assert len(api._AeroplanesAPI__aeroplanes) == 1
        assert api._AeroplanesAPI__aeroplanes[0]["ICAO24"] == "7809ab"


@pytest.mark.asyncio
async def test_get_aeroplanes_no_token():
    api = AeroplanesAPI()
    api._AeroplanesAPI__box = {}
    with (
        patch.object(api, "_AeroplanesAPI__get_token") as mock_token,
        patch.object(api, "_AeroplanesAPI__get_request", return_value={"states": []}) as mock_get,
    ):
        await api.get_aeroplanes()
        mock_token.assert_called_once()
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_aeroplanes_missing_states_key(capsys):
    api = AeroplanesAPI()
    api._AeroplanesAPI__token = "token"
    with patch.object(api, "_AeroplanesAPI__get_request", return_value={"other": "data"}):
        await api.get_aeroplanes()
    captured = capsys.readouterr()
    assert "Not states key" in captured.out


def test_aeroplanes_property_returns_deepcopy():
    api = AeroplanesAPI()
    api._AeroplanesAPI__aeroplanes = [{"test": "data"}]
    copy1 = api.aeroplanes
    copy1[0]["test"] = "modified"
    assert api._AeroplanesAPI__aeroplanes[0]["test"] == "data"
    assert copy1 is not api._AeroplanesAPI__aeroplanes


def test_init_with_kwargs(sample_plane_dict):
    plane = Aeroplane(**sample_plane_dict)
    assert plane.ICAO24 == "7809ab"
    assert plane.baro_altitude == 10698.48
    assert plane.on_ground is False


def test_init_empty():
    plane = Aeroplane()
    for attr in Aeroplane.__slots__:
        assert getattr(plane, attr, None) is None


def test_iteration(sample_plane):
    iterator = iter(sample_plane)
    items = list(iterator)
    assert len(items) == len(Aeroplane.__slots__)
    assert items[0] == ("ICAO24", "7809ab")


def test_comparison_tuple_with_both(sample_plane):
    assert sample_plane._Aeroplane__comparison_tuple() == (10698.48, 212.99)


def test_comparison_tuple_missing_data():
    plane = Aeroplane(baro_altitude=5000, velocity=None)
    assert plane._Aeroplane__comparison_tuple() == (5000, 0)


def test_lt(sample_plane):
    plane2 = Aeroplane(baro_altitude=9000, velocity=200)
    assert plane2 < sample_plane


def test_le_equal(sample_plane):
    plane2 = Aeroplane(**sample_plane.get_in_dict())
    assert plane2 <= sample_plane


def test_gt(sample_plane):
    plane2 = Aeroplane(baro_altitude=9000, velocity=200)
    assert sample_plane > plane2


def test_ge(sample_plane):
    plane2 = Aeroplane(**sample_plane.get_in_dict())
    assert sample_plane >= plane2


def test_eq(sample_plane):
    plane2 = Aeroplane(**sample_plane.get_in_dict())
    assert not (sample_plane == plane2)


def test_bool_true(sample_plane):
    assert bool(sample_plane) is True


def test_bool_false_missing_data():
    plane = Aeroplane(baro_altitude=None, velocity=100)
    assert bool(plane) is False


def test_getitem_str(sample_plane):
    assert sample_plane["ICAO24"] == "7809ab"
    assert sample_plane["nonexistent"] is None


def test_getitem_int(sample_plane):
    assert sample_plane[0] == "7809ab"


def test_getitem_slice(sample_plane):
    result = sample_plane[:2]
    assert result == ["7809ab", "CQH6760"]


def test_getitem_invalid_type(sample_plane):
    with pytest.raises(TypeError):
        _ = sample_plane[1.5]


def test_repr(sample_plane):
    r = repr(sample_plane)
    assert r.startswith("Aeroplane(")
    assert "ICAO24=7809ab" in r


def test_str(sample_plane):
    s = str(sample_plane)
    assert "CQH6760 (7809ab) in China" in s


def test_cast_to_aeroplane_gen(aeroplanes_json):
    data = json.loads(aeroplanes_json)
    gen = Aeroplane.cast_to_aeroplane_gen(data[:2])
    planes = list(gen)
    assert len(planes) == 2
    assert all(isinstance(p, Aeroplane) for p in planes)


def test_cast_to_aeroplane_removes_duplicates(capsys):
    data = [
        {"ICAO24": "111", "Callsign": "A", "country": "X"},
        {"ICAO24": "111", "Callsign": "A", "country": "X"},
        {"ICAO24": "222", "Callsign": "B", "country": "Y"},
    ]
    planes = Aeroplane.cast_to_aeroplane(data)
    assert len(planes) == 2
    captured = capsys.readouterr()
    assert "Not unique" in captured.out


def test_get_in_dict(sample_plane):
    d = sample_plane.get_in_dict()
    assert d["ICAO24"] == "7809ab"
    assert d["baro_altitude"] == 10698.48


def test_filter_by_country_static(planes_list):
    filtered = Aeroplane.filter_by_country(["China"], planes_list)
    assert all(p.country == "China" for p in filtered)


def test_filter_by_country_predicate(sample_plane):
    assert sample_plane.filter_predicate(["China"]) is True
    assert sample_plane.filter_predicate(["USA"]) is False


def test_get_top(planes_list):
    top = Aeroplane.get_top(planes_list, top_n=3)
    altitudes = [p.baro_altitude for p in top]
    assert altitudes == sorted(altitudes, reverse=True)
    assert len(top) == 3


def test_filter_by_range(planes_list):
    filtered = Aeroplane.filter_by_range(planes_list, (5000, 8000))
    for p in filtered:
        assert 5000 <= p.baro_altitude <= 8000


def test_filter_by_ground(planes_list):
    on_ground = Aeroplane.filter_by_ground(planes_list, True)
    assert all(p.on_ground is True for p in on_ground)
    in_air = Aeroplane.filter_by_ground(planes_list, False)
    assert all(p.on_ground is False for p in in_air)


def test_get_slice(planes_list):
    result = Aeroplane.get_slice(planes_list, head=2, tail=2)
    assert result is None


def test_init_creates_path_with_json_suffix(tmp_path):
    saver = JSONSaver(str(tmp_path), "test_file")
    assert saver.path.suffix == ".json"
    assert saver.path.name == "test_file.json"


def test_init_creates_directory_and_file(tmp_path):
    file_path = tmp_path / "subdir"
    saver = JSONSaver(str(file_path), "data")
    assert saver.path.exists()
    assert saver.path.parent == file_path


def test_getitem_returns_values_for_key(tmp_path):
    saver = JSONSaver(str(tmp_path), "test")
    saver.data = [{"ICAO24": "abc", "Callsign": "FLY1"}, {"ICAO24": "def", "Callsign": "FLY2"}]
    assert saver["ICAO24"] == ["abc", "def"]
    with pytest.raises(TypeError):
        saver[0]


def test_is_unique(tmp_path):
    saver = JSONSaver(str(tmp_path), "test")
    saver.data = [{"ICAO24": "abc"}]
    assert saver._JSONSaver__is_unique({"ICAO24": "def"}) is True
    assert saver._JSONSaver__is_unique({"ICAO24": "abc"}) is False


def test_update_data(planes_list, tmp_path):
    saver = JSONSaver(str(tmp_path), "test")
    saver.update_data(planes_list[:2])
    assert len(saver.data) == 2
    assert saver.data[0]["ICAO24"] == planes_list[0].ICAO24
    with pytest.raises(TypeError):
        saver.update_data("")


def test_add_aeroplane_new(tmp_path, sample_plane):
    saver = JSONSaver(str(tmp_path), "test")
    saver.add_aeroplane(sample_plane)
    assert len(saver.data) == 1
    assert saver.data[0]["ICAO24"] == "7809ab"


def test_add_aeroplane_update_existing(tmp_path, sample_plane):
    saver = JSONSaver(str(tmp_path), "test")
    saver.add_aeroplane(sample_plane)
    modified = Aeroplane(**sample_plane.get_in_dict())
    modified.baro_altitude = 9999
    saver.add_aeroplane(modified)
    assert len(saver.data) == 1
    assert saver.data[0]["baro_altitude"] == 9999


def test_delete_aeroplane(tmp_path, planes_list):
    saver = JSONSaver(str(tmp_path), "test")
    saver.update_data(planes_list[:2])
    icao = planes_list[0].ICAO24
    saver.delete_aeroplane(icao)
    assert len(saver.data) == 1
    assert saver.data[0]["ICAO24"] != icao


def test_read_aeroplane(tmp_path):
    file_path = tmp_path / "test.json"
    test_data = [{"ICAO24": "123"}]
    file_path.write_text(json.dumps(test_data))
    saver = JSONSaver(str(tmp_path), "test")
    saver.read_aeroplane()
    assert saver.data == test_data


def test_save_file(tmp_path):
    saver = JSONSaver(str(tmp_path), "save_test")
    saver.data = [{"key": "value"}]
    saver.save_file()
    assert saver.path.exists()
    with open(saver.path) as f:
        saved = json.load(f)
    assert saved == [{"key": "value"}]


def test_get_fullpath(tmp_path):
    saver = JSONSaver(str(tmp_path), "path_test")
    assert saver.get_fullpath() == saver.path.resolve()


def test_read_aeroplane_creates_file_if_missing(tmp_path):
    saver = JSONSaver(str(tmp_path), "missing")
    saver.read_aeroplane()
    assert saver.path.exists()
    with open(saver.path) as f:
        content = json.load(f)
    assert content == []
