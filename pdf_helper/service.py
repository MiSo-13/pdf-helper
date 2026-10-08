"""파일 변환, PDF 병합, 선택적 암호화의 순수 서비스 계층."""
from __future__ import annotations

import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile

from pypdf import PdfReader, PdfWriter

PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"


def generate_password(length: int = 16) -> str:
    """혼동하기 쉬운 문자를 제외한 암호학적 난수 비밀번호를 생성한다."""
    if length < 12:
        raise ValueError("비밀번호 길이는 12자 이상이어야 합니다.")
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


def find_libreoffice() -> str:
    """PATH와 알려진 Windows 설치 경로에서 LibreOffice를 찾는다."""
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
    raise RuntimeError("Word 변환에는 LibreOffice가 필요합니다. 설치 후 다시 실행하세요.")


def convert_word_to_pdf(word_path: Path, work_dir: Path) -> Path:
    """격리된 임시 프로필로 DOCX/DOC를 PDF로 변환한다."""
    word_path = Path(word_path).resolve()
    if word_path.suffix.lower() not in (".docx", ".doc"):
        raise ValueError("Word 파일은 .docx 또는 .doc 형식이어야 합니다.")
    if not word_path.is_file():
        raise FileNotFoundError(f"Word 파일이 없습니다: {word_path}")
    work_dir = Path(work_dir).resolve()
    profile_dir = work_dir / "lo-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    # 입력 파일 이름이 충돌하지 않도록 변환 결과는 전용 임시 폴더에 둔다.
    output_dir = work_dir / "converted"
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        find_libreoffice(),
        f"-env:UserInstallation={profile_dir.as_uri()}",
        "--headless", "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", str(output_dir), str(word_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Word → PDF 변환 시간이 초과되었습니다(120초).") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Word → PDF 변환 실패: {detail[:500]}")
    converted = output_dir / f"{word_path.stem}.pdf"
    if not converted.is_file() or converted.stat().st_size == 0:
        raise RuntimeError("Word 변환 결과 PDF가 생성되지 않았습니다.")
    return converted


def create_merged_pdf(
    pdf_path: str | Path,
    word_path: str | Path,
    output_path: str | Path,
    password: str | None = None,
) -> int:
    """기존 PDF 다음에 Word 변환 PDF를 붙여 안전하게 저장하고 총 페이지 수를 반환한다.

    오류 시 결과 파일을 덮어쓰지 않는다. 암호화는 AES-256을 사용한다.
    """
    pdf_path, word_path, output_path = map(lambda p: Path(p).expanduser().resolve(), (pdf_path, word_path, output_path))
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("원본 파일은 PDF 형식이어야 합니다.")
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF 파일이 없습니다: {pdf_path}")
    if output_path in (pdf_path, word_path):
        raise ValueError("결과 파일은 입력 파일과 다른 경로여야 합니다.")
    if password is not None and not password:
        raise ValueError("비밀번호가 비어 있습니다.")
    if not output_path.parent.is_dir():
        raise FileNotFoundError("결과 파일을 저장할 폴더가 없습니다.")

    with tempfile.TemporaryDirectory(prefix="pdf-helper-") as tmp:
        converted = convert_word_to_pdf(word_path, Path(tmp))
        writer = PdfWriter()
        for source in (pdf_path, converted):
            reader = PdfReader(str(source), strict=True)
            if reader.is_encrypted:
                raise ValueError(f"암호화된 입력 PDF는 지원하지 않습니다: {source.name}")
            writer.append(reader)
        page_count = len(writer.pages)
        if page_count == 0:
            raise ValueError("병합할 PDF 페이지가 없습니다.")
        if password is not None:
            writer.encrypt(user_password=password, algorithm="AES-256")
        # 동일한 출력 폴더에 임시 파일 생성 후 완료 시에만 원자적으로 교체한다.
        fd, staged_name = tempfile.mkstemp(prefix=".pdf-helper-", suffix=".pdf", dir=output_path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                writer.write(stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(staged_name, output_path)
        finally:
            if os.path.exists(staged_name):
                os.unlink(staged_name)
        return page_count
