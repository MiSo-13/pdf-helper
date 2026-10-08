"""여러 PDF/Word 파일의 입력 순서 및 실패 시 파일 보존 검증."""
from pathlib import Path
import pytest
from pypdf import PdfReader, PdfWriter
from pdf_helper import service


def make_pdf(path: Path, widths: list[int]):
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=300)
    with path.open("wb") as stream:
        writer.write(stream)


def test_merge_multiple_mixed_documents_in_order(tmp_path, monkeypatch):
    pdf_a = tmp_path / "a.pdf"
    pdf_b = tmp_path / "b.pdf"
    word_a = tmp_path / "first.docx"
    word_b = tmp_path / "second.docx"
    converted_a = tmp_path / "converted_a.pdf"
    converted_b = tmp_path / "converted_b.pdf"
    make_pdf(pdf_a, [100, 101])
    make_pdf(pdf_b, [400])
    make_pdf(converted_a, [200])
    make_pdf(converted_b, [300, 301])
    word_a.write_text("mock")
    word_b.write_text("mock")
    workdirs = []

    def convert(path, directory):
        workdirs.append(directory)
        return {word_a: converted_a, word_b: converted_b}[path]

    monkeypatch.setattr(service, "convert_word_to_pdf", convert)
    output = tmp_path / "merged.pdf"
    count = service.merge_documents([pdf_a, word_a, word_b, pdf_b], output, "secret-password")
    assert count == 6
    reader = PdfReader(output)
    assert reader.is_encrypted
    assert reader.decrypt("secret-password") != 0
    assert [int(page.mediabox.width) for page in reader.pages] == [100, 101, 200, 300, 301, 400]
    assert workdirs[0] != workdirs[1]


def test_pdf_only_inputs_require_no_libreoffice(tmp_path, monkeypatch):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    make_pdf(first, [111])
    make_pdf(second, [222])
    monkeypatch.setattr(service, "find_libreoffice", lambda: (_ for _ in ()).throw(AssertionError("not needed")))
    output = tmp_path / "merged.pdf"
    assert service.merge_documents([second, first], output) == 2
    assert [int(p.mediabox.width) for p in PdfReader(output).pages] == [222, 111]


def test_empty_and_unsupported_inputs_rejected(tmp_path):
    with pytest.raises(ValueError, match="하나 이상"):
        service.merge_documents([], tmp_path / "output.pdf")
    invalid = tmp_path / "invalid.txt"
    invalid.write_text("not a pdf")
    with pytest.raises(ValueError, match="지원하지 않는"):
        service.merge_documents([invalid], tmp_path / "output.pdf")


def test_duplicate_input_can_be_merged_twice(tmp_path):
    original = tmp_path / "original.pdf"
    make_pdf(original, [100])
    output = tmp_path / "output.pdf"
    assert service.merge_documents([original, original], output) == 2
