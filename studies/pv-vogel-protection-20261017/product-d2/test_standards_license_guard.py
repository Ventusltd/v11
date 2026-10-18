"""Ensure the public D2 export guard catches obvious restricted files."""
from pathlib import Path
import tempfile
import unittest
from standards_license_guard import problems

class LicensingGuardTests(unittest.TestCase):
    def test_safe_original_engineering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"independent-model.md").write_text(
              "IEC 62548-1:2023 §7.2.11 — check the licensed edition; "
              "do not reproduce proprietary normative content.",encoding="utf8")
            self.assertEqual(problems(p),[])
    def test_suspect_scanned_standard_filename(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"iec62548-1-example.pdf").write_bytes(b"NO STANDARD CONTENT - TEST PLACEHOLDER")
            self.assertEqual(len(problems(p)),1)
    def test_suspect_page_image_filename(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"IEC_62738_page1.png").write_bytes(b"NOT A REAL PAGE")
            self.assertEqual(len(problems(p)),1)
    def test_copyrighted_publication_notice(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"suspect.txt").write_text(
              "THIS PUBLICATION IS COPYRIGHT PROTECTED",encoding="utf8")
            self.assertEqual(len(problems(p)),1)
    def test_licensee_footer_pattern(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            # Synthetic footer markers, not a real licensed document.
            (p/"suspect.log").write_text(
              "Customer: SAMPLE; Company: SAMPLE; Licence: demo; Order No.: TEST",encoding="utf8")
            self.assertEqual(len(problems(p)),1)
    def test_nonutf8_requires_review(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"unknown.md").write_bytes(b"\xff\xfe")
            self.assertEqual(len(problems(p)),1)
if __name__=="__main__":
    unittest.main(verbosity=2)
