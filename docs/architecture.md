# PDF Helper 아키텍처

## 구성

- `main.py`: PyQt6 QApplication 시작
- `pdf_helper/window.py`: 파일 선택 / 암호 옵션 / 비동기 작업 / 오류 메시지
- `pdf_helper/service.py`: LibreOffice 변환, pypdf 병합, AES-256 암호화
- `tests/test_service.py`: 서비스 로직 회귀 테스트

## 처리 순서

1. 원본 PDF / Word / 저장 위치를 검증한다.
2. 임시 디렉터리에서 LibreOffice를 별도 UserInstallation 프로필로 실행한다.
3. 변환된 PDF를 확인한다.
4. pypdf로 원본 PDF와 변환된 PDF를 **이 순서대로** 추가한다.
5. 비밀번호가 지정된 경우 AES-256 암호화를 적용한다.
6. 출력 폴더에 임시 PDF 파일을 생성한다.
7. 최종 쓰기가 끝났을 때만 `os.replace`로 결과를 교체한다.

GUI는 `QThread`의 작업 객체를 이용해 변환 중에도 이벤트 루프가 블로킹되지 않도록 한다.
입력 문서 및 생성 PDF는 원격 서버에 전송하지 않는다.
비밀번호는 디스크의 앱 설정에 저장하지 않는다.

## 제한 및 추후 개선

- DOC/DOCX 변환은 LibreOffice 설치가 필수다.
- 원본 PDF의 비밀번호를 입력하는 기능은 현재 제공하지 않는다.
- 단일 PDF + 단일 Word만 처리한다.
- GUI 자체의 자동화 테스트 및 실제 LibreOffice 문서 렌더링 테스트는 후속 과제다.
