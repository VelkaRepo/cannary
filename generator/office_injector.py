"""
MS Office DOCX Canary Builder & Injector for CanaryFile Engine.
Injects external attachedTemplate relationship web bugs into Microsoft Word (.docx) documents.
"""

import zipfile
import os
import uuid
import tempfile
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any


class DOCXCanaryBuilder:
    """Builder class for crafting Microsoft Word (.docx) canary tokens."""

    def __init__(self, listener_url: str):
        """
        :param listener_url: Base URL of CanaryFile listener server (e.g. http://127.0.0.1:8000)
        """
        self.listener_url = listener_url.rstrip("/")

    def generate_trigger_url(self, token_id: str) -> str:
        """Construct canary trigger endpoint URL for a given token ID."""
        return f"{self.listener_url}/t/{token_id}"

    def build_canary_docx(
        self,
        output_path: str,
        token_id: Optional[str] = None,
        title: str = "Confidential Strategy Document"
    ) -> Dict[str, Any]:
        """
        Build a valid decoy Microsoft Word (.docx) file embedded with a canary template web bug.

        :param output_path: Destination path for generated .docx file.
        :param token_id: Unique token ID string (generated automatically if None).
        :param title: Document title text.
        :return: Metadata dictionary.
        """
        if not token_id:
            token_id = str(uuid.uuid4())

        trigger_url = self.generate_trigger_url(token_id)

        # Standard minimal OpenXML structures for a valid empty DOCX file
        content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
</Types>"""

        document_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>{title}</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>"""

        word_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
</Relationships>"""

        word_settings_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:attachedTemplate r:id="rIdCanary" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
</w:settings>"""

        # Relationship XML pointing attachedTemplate to canary trigger URL
        settings_rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdCanary" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" Target="{trigger_url}" TargetMode="External"/>
</Relationships>"""

        # Write output DOCX ZIP container
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as docx:
            docx.writestr("[Content_Types].xml", content_types_xml)
            docx.writestr("_rels/.rels", document_rels_xml)
            docx.writestr("word/document.xml", document_xml)
            docx.writestr("word/_rels/document.xml.rels", word_rels_xml)
            docx.writestr("word/settings.xml", word_settings_xml)
            docx.writestr("word/_rels/settings.xml.rels", settings_rels_xml)

        return {
            "token_id": token_id,
            "trigger_url": trigger_url,
            "output_path": os.path.abspath(output_path),
            "file_type": "docx"
        }

    def inject_existing_docx(
        self,
        input_docx_path: str,
        output_docx_path: str,
        token_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inject attachedTemplate canary web bug into an existing Microsoft Word (.docx) file.

        :param input_docx_path: Source .docx filepath.
        :param output_docx_path: Destination filepath.
        :param token_id: Optional token ID string.
        :return: Metadata dictionary.
        """
        if not token_id:
            token_id = str(uuid.uuid4())

        trigger_url = self.generate_trigger_url(token_id)

        # Temporary files for ZIP manipulation
        temp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(input_docx_path, "r") as zip_in:
                zip_in.extractall(temp_dir)

            word_dir = os.path.join(temp_dir, "word")
            os.makedirs(word_dir, exist_ok=True)
            word_rels_dir = os.path.join(word_dir, "_rels")
            os.makedirs(word_rels_dir, exist_ok=True)

            settings_path = os.path.join(word_dir, "settings.xml")
            if not os.path.exists(settings_path):
                word_settings_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:attachedTemplate r:id="rIdCanary" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
</w:settings>"""
                with open(settings_path, "w", encoding="utf-8") as f:
                    f.write(word_settings_xml)

            settings_rels_path = os.path.join(word_rels_dir, "settings.xml.rels")
            settings_rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdCanary" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" Target="{trigger_url}" TargetMode="External"/>
</Relationships>"""
            with open(settings_rels_path, "w", encoding="utf-8") as f:
                f.write(settings_rels_xml)

            # Re-pack modified files into output DOCX ZIP archive
            with zipfile.ZipFile(output_docx_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        zip_out.write(full_path, rel_path)

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "token_id": token_id,
            "trigger_url": trigger_url,
            "output_path": os.path.abspath(output_docx_path),
            "file_type": "docx"
        }
