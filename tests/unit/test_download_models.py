import pytest
from pathlib import Path
from scripts.download_models import is_valid_model_file, verify_or_download_models, ESSENTIAL_MODELS


def test_is_valid_model_file(tmp_path: Path):
    non_existent = tmp_path / "missing.pt"
    assert not is_valid_model_file(non_existent)

    # Empty or small pointer file (< 1MB)
    small_file = tmp_path / "pointer.pt"
    small_file.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
    assert not is_valid_model_file(small_file)

    # Valid large model file (> 1MB)
    large_file = tmp_path / "large_model.pt"
    large_file.write_bytes(b"0" * (1024 * 1024 + 10))
    assert is_valid_model_file(large_file)


def test_verify_or_download_models_check_mode():
    status = verify_or_download_models(auto_download=False)
    assert isinstance(status, dict)
    for model_name in ESSENTIAL_MODELS:
        assert model_name in status
