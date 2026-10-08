"""순서가 지정된 PDF/Word 문서 병합 및 선택적 AES-256 암호화."""
from __future__ import annotations

import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
from collections.abc import Sequence

from pypdf import PdfReader, PdfWriter

SUPPORTED_SUFFIXES = frozenset({".pdf", ".doc", ".docx"})
PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"


def generate_password(length: int = 16) -> str:
    if length < 12:
        raise ValueError("비밀번호 길이는 12자 이상이어야 합니다.")
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


def find_libreoffice() -> str:
    for name in ("libreoffice", "soffice"):
        found = shutil.which(name)
        if found:
            return found
    if os.name == "nt":
        for root in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")):
            if root:
                candidate = Path(root) / "LibreOffice" / "program" / "soffice.exe"
                if candidate.is_file():
                    return str(candidate)
    if os.name == "posix":
        mac_path = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        if mac_path.is_file():
            return str(mac_path)
    raise RuntimeError("Word 변환을 위해 LibreOffice 설치가 필요합니다.")


def convert_word_to_pdf(word_path: Path, work_dir: Path) -> Path:
    word_path = Path(word_path).resolve()
    if word_path.suffix.lower() not in (".docx", ".doc"):
        raise ValueError("Word 파일은 .docx 또는 .doc 형식이어야 합니다.")
    if not word_path.is_file():
        raise FileNotFoundError(f"Word 파일이 없습니다: {word_path}")
    work_dir = Path(work_dir).resolve()
    profile = work_dir / "lo-profile"
    profile.mkdir(parents=True, exist_ok=True)
    output = work_dir / "converted"
    output.mkdir(parents=True, exist_ok=True)
    command = [
        find_libreoffice(), f"-env:UserInstallation={profile.as_uri()}",
        "--headless", "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", str(output), str(word_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Word 변환 시간 초과: {word_path.name}") from exc
    if result.returncode != 0:
        raise RuntimeError(f"Word 변환 실패 ({word_path.name}): {(result.stderr or result.stdout).strip()[:500]}")
    converted = output / (word_path.stem + ".pdf")
    if not converted.is_file() or converted.stat().st_size == 0:
        raise RuntimeError(f"Word 변환 결과가 없습니다: {word_path.name}")
    return converted


def merge_documents(
    inputs: Sequence[str | Path],
    output_path: str | Path,
    password: str | None = None,
) -> int:
    """지정한 순서대로 PDF 및 Word를 병합한다. 실패 시 기존 결과는 보존한다."""
    if not inputs:
        raise ValueError("병합할 파일을 하나 이상 추가하세요.")
    sources = [Path(value).expanduser().resolve() for value in inputs]
    destination = Path(output_path).expanduser().resolve()
    if password is not None and not password:
        raise ValueError("비밀번호가 비어 있습니다.")
    if not destination.parent.is_dir():
        raise FileNotFoundError("결과 파일을 저장할 폴더가 없습니다.")
    if destination in sources:
        raise ValueError("결과 파일은 입력 파일과 다른 경로여야 합니다.")
    for source in sources:
        if source.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise ValueError(f"지원하지 않는 파일 형식: {source.name}")
        if not source.is_file():
            raise FileNotFoundError(f"파일이 없습니다: {source}")

    writer = PdfWriter()
    try:
        with tempfile.TemporaryDirectory(prefix="pdf-helper-") as tmp:
            # Word별 작업 폴더를 분리해 같은 파일명도 결과가 충돌하지 않도록 한다.
            for index, source in enumerate(sources):
                if source.suffix.lower() == ".pdf":
                    target = source
                else:
                    target = convert_word_to_pdf(source, Path(tmp) / str(index))
                reader = PdfReader(str(target), strict=True)
                if reader.is_encrypted:
                    raise ValueError(f"암호화된 입력 PDF는 지원하지 않습니다: {source.name}")
                writer.append(reader)
            page_count = len(writer.pages)
            if not page_count:
                raise ValueError("병합할 PDF 페이지가 없습니다.")
            if password is not None:
                writer.encrypt(user_password=password, algorithm="AES-256")
            fd, staged = tempfile.mkstemp(prefix=".pdf-helper-", suffix=".pdf", dir=destination.parent)
            try:
                with os.fdopen(fd, "wb") as stream:
                    writer.write(stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(staged, destination)
            finally:
                if os.path.exists(staged):
                    os.unlink(staged)
            return page_count
    finally:
        writer.close()


def create_merged_pdf(
    pdf_path: str | Path, word_path: str | Path,
    output_path: str | Path, password: str | None = None,
) -> int:
    """기존 두 파일 호출부 호환성 유지."""
    return merge_documents([pdf_path, word_path], output_path, password)
