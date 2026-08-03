"""
Unit tests for CanaryFile Engine document generator & PDF builder.
"""

import pytest
import os
from pypdf import PdfReader
from generator.pdf_injector import PDFCanaryInjector
from generator.builder import PDFCanaryBuilder


def test_create_canary_pdf(tmp_path):
    """Verify decoy canary PDF generation via PDFCanaryInjector."""
    output_pdf = str(tmp_path / "canary_test.pdf")
    injector = PDFCanaryInjector(listener_url="http://127.0.0.1:8000")
    
    token_id = injector.create_canary_pdf(output_pdf_path=output_pdf, token_id="custom-pdf-token")
    
    assert os.path.exists(output_pdf)
    assert token_id == "custom-pdf-token"
    
    reader = PdfReader(output_pdf)
    assert len(reader.pages) == 1
    
    root_dict = reader.trailer["/Root"]
    assert "/OpenAction" in root_dict
    open_action = root_dict["/OpenAction"]
    assert str(open_action["/S"]) == "/URI"
    assert "http://127.0.0.1:8000/t/custom-pdf-token" in str(open_action["/URI"])


def test_inject_existing_pdf(tmp_path):
    """Verify injecting canary payload into existing PDF via PDFCanaryInjector."""
    base_pdf = str(tmp_path / "base.pdf")
    output_pdf = str(tmp_path / "injected.pdf")

    injector = PDFCanaryInjector(listener_url="http://canary.example.com")
    injector.create_canary_pdf(output_pdf_path=base_pdf, token_id="base-token")
    
    new_token_id = injector.inject_pdf(
        input_pdf_path=base_pdf,
        output_pdf_path=output_pdf,
        token_id="injected-token-999"
    )

    assert os.path.exists(output_pdf)
    assert new_token_id == "injected-token-999"

    reader = PdfReader(output_pdf)
    root_dict = reader.trailer["/Root"]
    open_action = root_dict["/OpenAction"]
    assert "http://canary.example.com/t/injected-token-999" in str(open_action["/URI"])


def test_builder_create_canary_pdf(tmp_path):
    """Verify PDFCanaryBuilder build_canary_pdf."""
    output_pdf = str(tmp_path / "builder_test.pdf")
    builder = PDFCanaryBuilder(listener_url="http://127.0.0.1:8000")

    result = builder.build_canary_pdf(output_path=output_pdf, token_id="builder-token-123")

    assert os.path.exists(output_pdf)
    assert result["token_id"] == "builder-token-123"
    assert result["trigger_url"] == "http://127.0.0.1:8000/t/builder-token-123"

    reader = PdfReader(output_pdf)
    root_dict = reader.trailer["/Root"]
    assert "/Files" in root_dict
    files_dict = root_dict["/Files"]
    assert "/Names" in files_dict
    names_array = files_dict["/Names"]
    assert names_array[0] == "CanaryAsset"
    filespec_obj = names_array[1]
    assert str(filespec_obj["/Type"]) == "/Filespec"
    assert str(filespec_obj["/FS"]) == "/URL"
    assert "http://127.0.0.1:8000/t/builder-token-123" in str(filespec_obj["/F"])


def test_builder_inject_existing_pdf(tmp_path):
    """Verify PDFCanaryBuilder inject_existing_pdf."""
    base_pdf = str(tmp_path / "base_builder.pdf")
    output_pdf = str(tmp_path / "injected_builder.pdf")

    builder = PDFCanaryBuilder(listener_url="http://canary.example.com")
    builder.build_canary_pdf(output_path=base_pdf, token_id="base-tok")

    result = builder.inject_existing_pdf(
        input_pdf_path=base_pdf,
        output_pdf_path=output_pdf,
        token_id="injected-builder-tok"
    )

    assert os.path.exists(output_pdf)
    assert result["token_id"] == "injected-builder-tok"

    reader = PdfReader(output_pdf)
    root_dict = reader.trailer["/Root"]
    assert "/Files" in root_dict
    files_dict = root_dict["/Files"]
    filespec_obj = files_dict["/Names"][1]
    assert "http://canary.example.com/t/injected-builder-tok" in str(filespec_obj["/F"])


def test_builder_prefixed_listener_url(tmp_path):
    """Verify trigger URL generation when listener_url contains path prefix."""
    output_pdf = str(tmp_path / "prefixed_builder_test.pdf")
    builder = PDFCanaryBuilder(listener_url="http://127.0.0.1:8000/trigger-test/")

    result = builder.build_canary_pdf(output_path=output_pdf, token_id="prefix-tok-99")

    assert result["trigger_url"] == "http://127.0.0.1:8000/trigger-test/t/prefix-tok-99"

    reader = PdfReader(output_pdf)
    root_dict = reader.trailer["/Root"]
    files_dict = root_dict["/Files"]
    filespec_obj = files_dict["/Names"][1]
    assert "http://127.0.0.1:8000/trigger-test/t/prefix-tok-99" in str(filespec_obj["/F"])


