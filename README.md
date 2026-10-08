# PDF Helper

PyQt6 기반 PDF·Word 다중 파일 병합 및 AES-256 암호화 도구입니다.

## 사용 방법

1. **파일 추가 ▾**에서 PDF / Word / 혼합 파일 여러 개를 선택하거나 목록에 끌어다 놓습니다.
2. 목록 내부 드래그 또는 ▲/▼ 버튼으로 순서를 변경합니다. 위에서 아래 순서대로 병합합니다.
3. 저장할 PDF 경로를 지정합니다.
4. 비밀번호를 자동 생성하거나 직접 입력합니다. 비밀번호 없이 저장할 수도 있습니다.
5. **순서대로 PDF 병합 및 저장**을 누릅니다.

Word(DOC, DOCX)는 LibreOffice를 사용해 PDF로 변환합니다. PDF 파일만 병합하면 LibreOffice가 필요하지 않습니다.

## 설치 및 실행

Python 3.11 이상 및 Word 변환 시 LibreOffice가 필요합니다.

```bash
python -m venv .venv
pip install -r requirements.txt
python main.py
```

Windows에서는 가상환경 활성화 시 `.venv\\Scripts\\activate`, Linux/macOS에서는 `source .venv/bin/activate`를 사용합니다.

## 운영체제 지원

GitHub Actions의 **다중 운영체제 빌드** 워크플로를 통해 Windows x64, macOS Intel/Apple Silicon, Linux x64/ARM64 빌드를 구성했습니다. ChromeOS에서는 Linux 개발 환경(Crostini)을 활성화한 후 Linux 실행 파일을 사용합니다. 실제 기기 호환성은 추가 확인이 필요합니다. Word 변환에는 각 기기의 LibreOffice 설치가 필요합니다.

## 주의사항

- 암호화된 입력 PDF는 현재 지원하지 않습니다.
- 결과 파일은 입력 파일과 동일한 경로로 지정할 수 없습니다.
- Word 문서의 레이아웃은 LibreOffice 및 설치 글꼴에 영향을 받습니다.
- 암호는 자동 저장하지 않습니다. 생성된 암호는 사용자가 보관해야 합니다.
- 병합 중 실패하면 기존 결과 파일은 보존합니다.

## 테스트

```bash
pip install -r requirements-dev.txt
python -m compileall -q main.py pdf_helper tests
python -m pytest -q
```

자세한 구현 구조는 [docs/architecture.md](docs/architecture.md)에서 확인할 수 있습니다.
