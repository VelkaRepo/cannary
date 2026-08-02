"""
Unit tests for CanaryFile Engine document generator & injector.
"""

import pytest
import os
from pypdf import PdfReader
from generator.pdf_injector import PDFCanaryInjector


def test_create_canary_pdf(tmp_path):
    """Verify decoy canary PDF generation."""
    output_pdf = str(tmp_path / "canary_test.pdf")
    injector = PDFCanaryInjector(listener_url="http://127.0.0.1:8000")
    
    token_id = injector.create_canary_pdf(output_pdf_path=output_pdf, token_id="custom-pdf-token")
    
    assert os.path.exists(output_pdf)
    assert token_id == "custom-pdf-token"
    
    # Read generated PDF and verify OpenAction URI
    reader = PdfReader(output_pdf)
    assert len(reader.pages) == 1
    
    root_dict = reader.trailer["/Root"]
    assert "/OpenAction" in root_dict
    open_action = root_dict["/OpenAction"]
    assert str(open_action["/S"]) == "/URI"
    assert "http://127.0.0.1:8000/t/custom-pdf-token" in str(open_action["/URI"])


def test_inject_existing_pdf(tmp_path):
    """Verify injecting canary payload into existing PDF."""
    base_pdf = str(tmp_path / "base.pdf")
    output_pdf = str(tmp_path / "injected.pdf")

    injector = PDFCanaryInjector(listener_url="http://canary.example.com")
    
    # First create a basic base PDF
    injector.create_canary_pdf(output_pdf_path=base_pdf, token_id="base-token")
    
    # Inject new token into existing PDF
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
