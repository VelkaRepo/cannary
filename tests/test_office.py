"""
Unit tests for Microsoft Word (.docx) canary builder.
"""

import pytest
import os
import zipfile
from generator.office_injector import DOCXCanaryBuilder


def test_build_canary_docx(tmp_path):
    """Verify DOCXCanaryBuilder build_canary_docx."""
    output_docx = str(tmp_path / "canary_test.docx")
    builder = DOCXCanaryBuilder(listener_url="http://127.0.0.1:8000")

    result = builder.build_canary_docx(output_path=output_docx, token_id="docx-token-101")

    assert os.path.exists(output_docx)
    assert result["token_id"] == "docx-token-101"
    assert result["file_type"] == "docx"

    # Verify ZIP archive contents & relationship web bug
    with zipfile.ZipFile(output_docx, "r") as zip_in:
        namelist = zip_in.namelist()
        assert "[Content_Types].xml" in namelist
        assert "word/settings.xml" in namelist
        assert "word/_rels/settings.xml.rels" in namelist

        settings_rels = zip_in.read("word/_rels/settings.xml.rels").decode("utf-8")
        assert "http://127.0.0.1:8000/t/docx-token-101" in settings_rels
        assert "attachedTemplate" in settings_rels


def test_inject_existing_docx(tmp_path):
    """Verify DOCXCanaryBuilder inject_existing_docx."""
    base_docx = str(tmp_path / "base.docx")
    output_docx = str(tmp_path / "injected.docx")

    builder = DOCXCanaryBuilder(listener_url="http://canary.example.com")
    builder.build_canary_docx(output_path=base_docx, token_id="base-docx-tok")

    result = builder.inject_existing_docx(
        input_docx_path=base_docx,
        output_docx_path=output_docx,
        token_id="injected-docx-tok"
    )

    assert os.path.exists(output_docx)
    assert result["token_id"] == "injected-docx-tok"

    with zipfile.ZipFile(output_docx, "r") as zip_in:
        settings_rels = zip_in.read("word/_rels/settings.xml.rels").decode("utf-8")
        assert "http://canary.example.com/t/injected-docx-tok" in settings_rels
