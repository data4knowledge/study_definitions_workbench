def mock_transmit_role_enabled_true(mocker, path="app.routers.transmissions"):
    # The path below could ne made configurable
    mock = mocker.patch(f"{path}.transmit_role_enabled")
    print(f"MOCK: {mock}")
    mock.side_effect = [True]
    return mock


def mock_transmit_role_enabled_false(mocker, path="app.routers.transmissions"):
    # The path below could ne made configurable
    mock = mocker.patch(f"{path}.transmit_role_enabled")
    mock.side_effect = [False]
    return mock
