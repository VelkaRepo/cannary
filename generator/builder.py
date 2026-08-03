"""
PDF Canary Builder for CanaryFile Engine.
Constructs valid decoy PDF documents with ISO 32000-1 external file specification
references for authorized blue team security telemetry testing.
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

    def _build_filespec_object(self, target_url: str) -> DictionaryObject:
        """Construct an ISO 32000-1 File Specification dictionary for external URL references."""
        filespec = DictionaryObject()
        filespec[NameObject("/Type")] = NameObject("/Filespec")
        filespec[NameObject("/F")] = TextStringObject(target_url)
        filespec[NameObject("/UF")] = TextStringObject(target_url)
        filespec[NameObject("/FS")] = NameObject("/URL")
        return filespec

    def build_canary_pdf(
        self,
        output_path: str,
        token_id: Optional[str] = None,
        title: str = "Confidential Telemetry Report"
    ) -> Dict[str, Any]:
        """
        Build a valid decoy PDF document using passive external file specifications.

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

        # Build ISO 32000-1 File Specification object
        filespec_obj = self._build_filespec_object(trigger_url)
        
        # Register the filespec object into the writer's object collection
        filespec_ref = writer._add_object(filespec_obj)

        # Attach as a collection/embedded reference or root-level reference structure
        # (Using safe catalog mapping depending on parser requirements)
        writer._root_object[NameObject("/Files")] = DictionaryObject({
            NameObject("/Names"): ArrayObject([TextStringObject("CanaryAsset"), filespec_ref])
        })

        # Standard Link Annotation fallback if needed, referencing filespec or cleaned up
        # Keeping minimal safe structures for rendering validation

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
        Inject passive canary file specification into an existing PDF file structure.

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

        filespec_obj = self._build_filespec_object(trigger_url)
        filespec_ref = writer._add_object(filespec_obj)

        writer._root_object[NameObject("/Files")] = DictionaryObject({
            NameObject("/Names"): ArrayObject([TextStringObject("CanaryAsset"), filespec_ref])
        })

        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        return {
            "token_id": token_id,
            "trigger_url": trigger_url,
            "output_path": os.path.abspath(output_pdf_path)
        }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build a Canary PDF document.")
    parser.add_argument("--output", default="test_canary.pdf", help="Output path for the generated PDF")
    parser.add_argument("--listener", default="http://127.0.0.1:8000", help="Listener server URL")
    parser.add_argument("--token", default=None, help="Optional token ID")
    
    args = parser.parse_args()

    builder = PDFCanaryBuilder(listener_url=args.listener)
    result = builder.build_canary_pdf(output_path=args.output, token_id=args.token)
    
    print(f"[+] Canary PDF successfully generated!")
    print(f"    - Output Path : {result['output_path']}")
    print(f"    - Trigger URL : {result['trigger_url']}")
    print(f"    - Token ID    : {result['token_id']}")