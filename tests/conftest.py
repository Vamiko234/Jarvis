import pytest

from jarvis.config import Config
from jarvis.context import init_context


@pytest.fixture
def config(tmp_path):
    cfg = Config()
    cfg.skills.data_dir = str(tmp_path / "data")
    cfg.skills.file_roots = [str(tmp_path)]
    return cfg


@pytest.fixture
def ctx(config):
    return init_context(config, force_adapter="mock")
