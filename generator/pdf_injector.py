"""
PDF Canary Injector for CanaryFile Engine.
Injects tracking URLs and OpenAction URI payloads into PDF file structures.
"""

from typing import Optional
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, FloatObject, NumberObject
import os
import uuid


class PDFCanaryInjector:
    """Class to handle injection of canary tracking URLs into PDF files."""

    def __init__(self, listener_url: str):
        """
        :param listener_url: Base URL of the CanaryFile listener server (e.g. http://127.0.0.1:8000)
        """
        self.listener_url = listener_url.rstrip("/")

    def generate_token_url(self, token_id: str) -> str:
        """Construct full canary trigger URL for a given token ID."""
        return f"{self.listener_url}/t/{token_id}"

    def inject_pdf(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        token_id: Optional[str] = None
    ) -> str:
        """
        Inject an OpenAction URI dictionary payload into an existing PDF.
        When opened in compatible PDF viewers, the document triggers a HTTP request to the listener.

        :param input_pdf_path: Path to existing source PDF.
        :param output_pdf_path: Output destination path for the weaponized/weapon-tagged PDF.
        :param token_id: Optional unique token ID. Generated automatically if None.
        :return: token_id used.
        """
        if not token_id:
            token_id = str(uuid.uuid4())

        trigger_url = self.generate_token_url(token_id)

        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()

        # Copy all pages from original PDF
        for page in reader.pages:
            writer.add_page(page)

        # Build URI Action dictionary (/S /URI /URI (https://...))
        uri_action = DictionaryObject()
        uri_action[NameObject("/S")] = NameObject("/URI")
        uri_action[NameObject("/URI")] = TextStringObject(trigger_url)

        # Set OpenAction on root catalog dictionary so opening document triggers request
        writer._root_object[NameObject("/OpenAction")] = uri_action

        # Write output PDF
        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        return token_id

    def create_canary_pdf(
        self,
        output_pdf_path: str,
        token_id: Optional[str] = None,
        title: str = "Confidential Report"
    ) -> str:
        """
        Generate a basic decoy PDF with injected canary tracking payload.

        :param output_pdf_path: Destination path for generated PDF.
        :param token_id: Optional unique token ID.
        :param title: Document title printed in PDF.
        :return: token_id used.
        """
        if not token_id:
            token_id = str(uuid.uuid4())

        trigger_url = self.generate_token_url(token_id)

        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)

        # Create OpenAction URI Dictionary
        uri_action = DictionaryObject()
        uri_action[NameObject("/S")] = NameObject("/URI")
        uri_action[NameObject("/URI")] = TextStringObject(trigger_url)

        # Attach OpenAction to Root Catalog
        writer._root_object[NameObject("/OpenAction")] = uri_action

        # Add visual link annotation to the page as well
        link_annotation = DictionaryObject()
        link_annotation[NameObject("/Type")] = NameObject("/Annot")
        link_annotation[NameObject("/Subtype")] = NameObject("/Link")
        link_annotation[NameObject("/Rect")] = ArrayObject([
            FloatObject(50), FloatObject(700), FloatObject(550), FloatObject(750)
        ])
        link_annotation[NameObject("/A")] = uri_action
        
        page[NameObject("/Annots")] = ArrayObject([link_annotation])

        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        return token_id
