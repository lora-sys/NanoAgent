"""pytest markers for agent tests."""

# Marker 名称常量
UNIT = "unit"
INTEGRATION = "integration"


def pytest_configure(config):
    """注册自定义 markers。"""
    config.addinivalue_line("markers", f"{UNIT}: unit test, mock mode, no network")
    config.addinivalue_line("markers", f"{INTEGRATION}: integration test, real API calls")
