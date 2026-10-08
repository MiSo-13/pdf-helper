# PDF Helper

PyQt6 기반 Word→PDF 변환, PDF 병합 및 비밀번호 설정 도구입니다.

## 기능

- PDF 1개와 Word(.docx/.doc) 1개를 선택
- LibreOffice로 Word를 PDF로 변환한 후 **원본 PDF 뒤에** 병합
- 선택적 AES-256 암호화 (랜덤 16자리 비밀번호 자동 생성 또는 직접 입력)
- 비밀번호 표시/복사, 결과 저장 위치 지정, 덮어쓰기 확인
- 모든 작업을 로컬에서 실행하고 변환/병합 중에는 UI 응답 유지

## 설치 및 실행

Python 3.11 이상과 [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) 설치가 필요합니다.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

LibreOffice는 PATH의 `libreoffice` 또는 `soffice` 명령으로 검색하며, Windows에서는 기본 Program Files 설치 경로도 확인합니다.

## 유의사항

- Word 변환 결과의 레이아웃은 설치된 글꼴과 LibreOffice 버전의 영향을 받습니다.
- 입력 원본 PDF가 암호화된 경우 변환을 지원하지 않습니다.
- 결과 파일은 입력 PDF와 같은 경로로 저장할 수 없습니다.
- 암호는 별도로 저장하지 않으므로 PDF를 열기 전에 반드시 보관하세요.
- 실패 시 기존 결과 파일을 유지하며, 클라우드 업로드는 수행하지 않습니다.

## 테스트

```bash
pip install -r requirements-dev.txt
python -m compileall -q main.py pdf_helper tests
python -m pytest -q
```

설계 문서는 [docs/architecture.md](docs/architecture.md)를 확인하세요.
