"""
PDF Canary Builder for CanaryFile Engine.
Constructs valid decoy PDF documents with standard document-level action references
and URI triggers for authorized blue team security telemetry testing.
"""

import uuid
import os
from typing import Optional, Dict, Any
from pypdf import PdfWriter, PdfReader
from pypdf.generic import (
    DictionaryObject,
    NameObject,
    TextStringObject,
    ArrayObject,
    FloatObject,
    NumberObject
)


class PDFCanaryBuilder:
    """Builder class for crafting PDF canary tokens for security monitoring."""

    def __init__(self, listener_url: str):
        """
        :param listener_url: Base URL of the CanaryFile listener server (e.g., http://127.0.0.1:8000)
        """
        self.listener_url = listener_url.rstrip("/")

    def generate_trigger_url(self, token_id: str) -> str:
        """Construct canary trigger endpoint URL for a given token ID."""
        return f"{self.listener_url}/t/{token_id}"

    def build_canary_pdf(
        self,
        output_path: str,
        token_id: Optional[str] = None,
        title: str = "Confidential Telemetry Report"
    ) -> Dict[str, Any]:
        """
        Build a valid decoy PDF document with document-level URI action trigger.

        :param output_path: Filepath destination for the generated PDF.
        :param token_id: Unique token ID string (generated automatically if None).
        :param title: Document title text inside decoy page.
        :return: Metadata dictionary containing token_id, trigger_url, and output_path.
        """
        if not token_id:
            token_id = str(uuid.uuid4())

        trigger_url = self.generate_trigger_url(token_id)

        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)

        # Create URI Action Dictionary (/S /URI /URI (https://...))
        uri_action = DictionaryObject()
        uri_action[NameObject("/S")] = NameObject("/URI")
        uri_action[NameObject("/URI")] = TextStringObject(trigger_url)

        # Document-level OpenAction trigger
        writer._root_object[NameObject("/OpenAction")] = uri_action

        # Standard Link Annotation
        link_annotation = DictionaryObject()
        link_annotation[NameObject("/Type")] = NameObject("/Annot")
        link_annotation[NameObject("/Subtype")] = NameObject("/Link")
        link_annotation[NameObject("/Rect")] = ArrayObject([
            FloatObject(50), FloatObject(700), FloatObject(550), FloatObject(750)
        ])
        link_annotation[NameObject("/A")] = uri_action

        page[NameObject("/Annots")] = ArrayObject([link_annotation])

        # Write output PDF file
        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        return {
            "token_id": token_id,
            "trigger_url": trigger_url,
            "output_path": os.path.abspath(output_path)
        }

    def inject_existing_pdf(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        token_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inject document-level canary trigger into an existing PDF file structure.

        :param input_pdf_path: Path to source PDF document.
        :param output_pdf_path: Destination path for injected PDF.
        :param token_id: Optional token ID string.
        :return: Metadata dictionary.
        """
        if not token_id:
            token_id = str(uuid.uuid4())

        trigger_url = self.generate_trigger_url(token_id)

        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        uri_action = DictionaryObject()
        uri_action[NameObject("/S")] = NameObject("/URI")
        uri_action[NameObject("/URI")] = TextStringObject(trigger_url)

        writer._root_object[NameObject("/OpenAction")] = uri_action

        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        return {
            "token_id": token_id,
            "trigger_url": trigger_url,
            "output_path": os.path.abspath(output_pdf_path)
        }
