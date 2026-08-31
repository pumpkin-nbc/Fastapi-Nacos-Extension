"""Discovery shapes, filters, normalization and strategies."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from fastapi_nacos import NacosDiscoveryError, NacosValidationError
from fastapi_nacos.discovery import (
    extract_instances,
    filter_instances,
    normalize_instance,
    select_instance,
)
from fastapi_nacos.naming import list_instances


@pytest.mark.parametrize(
    "response, expected",
    [
        (None, []),
        ([], []),
        ({"hosts": [1]}, [1]),
        ({"instances": [2]}, [2]),
        ({"data": [3]}, [3]),
        ({"data": {"hosts": [4]}}, [4]),
        ({"data": {"instances": [5]}}, [5]),
        ({}, []),
        ({"hosts": None}, []),
    ],
)
def test_extract_instances_supported_shapes(response, expected):
    assert extract_instances(response) == expected


def test_extract_instances_rejects_unknown_shape():
    with pytest.raises(NacosDiscoveryError, match="Unrecognized"):
        extract_instances({"unexpected": "shape"})


def test_normalize_dict_and_object():
    normalized = normalize_instance(
        {
            "ip": " 10.0.0.1 ",
            "port": "8080",
            "serviceName": "orders",
            "clusterName": "BLUE",
            "metadata": {"zone": "east"},
            "weight": "2.5",
            "healthy": "true",
        }
    )
    assert normalized["ip"] == "10.0.0.1"
    assert normalized["port"] == 8080
    assert normalized["service_name"] == "orders"
    assert normalized["cluster_name"] == "BLUE"
    assert normalized["weight"] == 2.5

    obj = SimpleNamespace(ip="10.0.0.2", port=8081, enabled=False)
    assert normalize_instance(obj)["enabled"] is False


@pytest.mark.parametrize(
    "instance",
    [None, {}, {"ip": "", "port": 80}, {"ip": "x", "port": True}, {"ip": "x", "port": 70000}],
)
def test_normalize_rejects_bad_endpoint(instance):
    with pytest.raises(NacosDiscoveryError):
        normalize_instance(instance)


def test_filter_and_selection_strategies():
    instances = [
        {"ip": "a", "clusterName": "BLUE", "metadata": {"zone": "east"}, "weight": 0},
        {"ip": "b", "clusterName": "GREEN", "metadata": {"zone": "west"}, "weight": 5},
    ]
    assert filter_instances(instances, "BLUE", {"zone": "east"}) == [instances[0]]
    assert select_instance(instances, "first") is instances[0]
    with patch("fastapi_nacos.discovery.random.choice", return_value=instances[1]):
        assert select_instance(instances, "random") is instances[1]
    with patch("fastapi_nacos.discovery.random.choices", return_value=[instances[1]]):
        assert select_instance(instances, "weight") is instances[1]
    assert select_instance([], "first") is None
    assert select_instance([dict(instances[0])], "weight")["ip"] == "a"
    with pytest.raises(NacosDiscoveryError, match="Unsupported"):
        select_instance(instances, "round-robin")


def test_naming_list_instances_filters_and_skips_bad_rows():
    client = MagicMock()
    client.list_naming_instance.return_value = {
        "hosts": [
            {"ip": "10.0.0.1", "port": 80, "clusterName": "BLUE", "metadata": {"zone": "east"}},
            {"ip": "", "port": 80, "clusterName": "BLUE", "metadata": {"zone": "east"}},
            {"ip": "10.0.0.2", "port": 81, "clusterName": "GREEN", "metadata": {"zone": "west"}},
        ]
    }
    result = list_instances(
        client,
        {"NACOS_GROUP_NAME": "DEFAULT_GROUP", "NACOS_INSTANCE_NORMALIZE": True},
        "orders",
        cluster="BLUE",
        metadata={"zone": "east"},
    )
    assert [(row["ip"], row["port"]) for row in result] == [("10.0.0.1", 80)]
    client.list_naming_instance.assert_called_once_with(
        "orders", group_name="DEFAULT_GROUP", healthy_only=True, clusters="BLUE"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"service_name": ""},
        {"service_name": "ok", "group": 1},
        {"service_name": "ok", "healthy_only": 1},
        {"service_name": "ok", "cluster": 1},
        {"service_name": "ok", "metadata": []},
    ],
)
def test_naming_list_validation(kwargs):
    with pytest.raises(NacosValidationError):
        list_instances(MagicMock(), {"NACOS_GROUP_NAME": "DEFAULT_GROUP"}, **kwargs)

