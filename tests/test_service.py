"""변환/병합/암호화 회귀 테스트."""
from pathlib import Path
import pytest
from pypdf import PdfReader, PdfWriter
from pdf_helper import service


def make_pdf(path: Path, count: int) -> None:
    writer = PdfWriter()
    for _ in range(count):
        writer.add_blank_page(width=300, height=400)
    with path.open("wb") as stream:
        writer.write(stream)


def test_password_is_random_and_valid():
    a, b = service.generate_password(), service.generate_password()
    assert len(a) == len(b) == 16
    assert a != b
    assert all(char in service.PASSWORD_ALPHABET for char in a)
    with pytest.raises(ValueError):
        service.generate_password(11)


@pytest.mark.parametrize("password", [None, "strong-password-123!"])
def test_pdf_merge_preserves_order_and_encryption(tmp_path, monkeypatch, password):
    original = tmp_path / "original.pdf"
    converted = tmp_path / "converted.pdf"
    word = tmp_path / "attachment.docx"
    result = tmp_path / "result.pdf"
    make_pdf(original, 2)
    make_pdf(converted, 3)
    word.write_bytes(b"fake docx - conversion is mocked")
    monkeypatch.setattr(service, "convert_word_to_pdf", lambda path, directory: converted)

    assert service.create_merged_pdf(original, word, result, password) == 5
    reader = PdfReader(result)
    assert reader.is_encrypted == (password is not None)
    if password:
        assert reader.decrypt("incorrect") == 0
        assert reader.decrypt(password) != 0
    assert len(reader.pages) == 5


def test_failed_conversion_does_not_replace_existing_result(tmp_path, monkeypatch):
    original = tmp_path / "original.pdf"
    word = tmp_path / "file.docx"
    output = tmp_path / "existing.pdf"
    make_pdf(original, 1)
    word.write_text("mock")
    output.write_bytes(b"do not modify")
    def fail(*args):
        raise RuntimeError("conversion error")
    monkeypatch.setattr(service, "convert_word_to_pdf", fail)
    with pytest.raises(RuntimeError, match="conversion error"):
        service.create_merged_pdf(original, word, output)
    assert output.read_bytes() == b"do not modify"


def test_output_cannot_overwrite_input(tmp_path):
    original = tmp_path / "original.pdf"
    word = tmp_path / "file.docx"
    make_pdf(original, 1)
    word.write_text("mock")
    with pytest.raises(ValueError, match="다른 경로"):
        service.create_merged_pdf(original, word, original)


def test_convert_rejects_unknown_extension(tmp_path):
    unknown = tmp_path / "file.txt"
    unknown.write_text("hello")
    with pytest.raises(ValueError, match="docx"):
        service.convert_word_to_pdf(unknown, tmp_path)


def test_convert_command_and_result(tmp_path, monkeypatch):
    word = tmp_path / "attachment.docx"
    word.write_text("mock")
    monkeypatch.setattr(service, "find_libreoffice", lambda: "/usr/bin/soffice")

    class Completed:
        returncode = 0
        stderr = ""
        stdout = ""

    def fake_run(cmd, **kwargs):
        assert "--headless" in cmd
        assert "--convert-to" in cmd
        assert kwargs["timeout"] == 120
        output = Path(cmd[cmd.index("--outdir") + 1])
        (output / "attachment.pdf").write_bytes(b"mock pdf")
        return Completed()

    monkeypatch.setattr(service.subprocess, "run", fake_run)
    assert service.convert_word_to_pdf(word, tmp_path).name == "attachment.pdf"
