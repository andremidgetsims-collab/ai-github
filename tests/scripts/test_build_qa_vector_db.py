"""Unit tests for scripts/build-qa-vector-db.py"""

import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies so tests run without them installed
# ---------------------------------------------------------------------------
for mod in [
    "langchain",
    "langchain.text_splitter",
    "langchain_community",
    "langchain_community.document_loaders",
    "langchain_community.vectorstores",
    "langchain_openai",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

# Provide the names the script imports
sys.modules["langchain.text_splitter"].RecursiveCharacterTextSplitter = MagicMock()
sys.modules["langchain_community.document_loaders"].PyPDFLoader = MagicMock()
sys.modules["langchain_community.vectorstores"].Chroma = MagicMock()
sys.modules["langchain_openai"].OpenAIEmbeddings = MagicMock()

# Now we can import the module under test
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
import importlib

build_qa = importlib.import_module("build-qa-vector-db")


class TestDownloadPdfs(unittest.TestCase):
    def test_skips_existing_files(self, tmp_path=None):
        """Already-present PDFs are not re-downloaded."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            # Patch the download dir to a temp location
            fake_pdf = Path(tmp) / "owasp_testing_guide_v4.pdf"
            fake_pdf.write_bytes(b"%PDF fake")

            with patch.object(build_qa, "PDF_DOWNLOAD_DIR", Path(tmp)):
                with patch.object(
                    build_qa,
                    "PDF_URLS",
                    [{"url": "http://example.com/fake.pdf", "filename": fake_pdf.name}],
                ):
                    result = build_qa.download_pdfs()

            self.assertEqual(result, [str(fake_pdf)])

    def test_handles_download_error_gracefully(self):
        """A failed download is skipped; other files still processed."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(build_qa, "PDF_DOWNLOAD_DIR", Path(tmp)):
                with patch.object(
                    build_qa,
                    "PDF_URLS",
                    [{"url": "http://bad-url-that-fails.invalid/x.pdf", "filename": "x.pdf"}],
                ):
                    with patch("requests.get", side_effect=Exception("network error")):
                        result = build_qa.download_pdfs()

            self.assertEqual(result, [])


class TestChunkPdfs(unittest.TestCase):
    def test_attaches_source_metadata(self):
        """Each chunk gets a 'source' metadata key set to the filename."""
        fake_doc = MagicMock()
        fake_doc.metadata = {}

        mock_loader = MagicMock()
        mock_loader.load.return_value = [fake_doc]

        mock_splitter = MagicMock()
        # Return one chunk whose metadata we can inspect
        chunk = MagicMock()
        chunk.metadata = {}
        mock_splitter.split_documents.return_value = [chunk]

        with patch.object(build_qa, "PyPDFLoader", return_value=mock_loader):
            with patch.object(
                build_qa,
                "RecursiveCharacterTextSplitter",
                return_value=mock_splitter,
            ):
                result = build_qa.chunk_pdfs(["/tmp/owasp_testing_guide_v4.pdf"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].metadata["source"], "owasp_testing_guide_v4.pdf")

    def test_skips_unreadable_pdf(self):
        """A PDF that raises on load is skipped; result is empty."""
        mock_loader = MagicMock()
        mock_loader.load.side_effect = Exception("bad pdf")

        with patch.object(build_qa, "PyPDFLoader", return_value=mock_loader):
            result = build_qa.chunk_pdfs(["/tmp/broken.pdf"])

        self.assertEqual(result, [])


class TestMainGuardsApiKey(unittest.TestCase):
    def test_exits_when_api_key_missing(self):
        """main() exits with code 1 when OPENAI_API_KEY is not set."""
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                build_qa.main()
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
