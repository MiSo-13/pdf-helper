# PDF Helper 배포 안내

PDF Helper는 Python 코드를 실행하지 않고 운영체제별 파일을 다운로드해 사용할 수 있습니다.

## 다운로드

[최신 버전 다운로드](https://github.com/MiSo-13/pdf-helper/releases/latest)

| 운영체제 | 받을 파일 | 실행 방법 |
| --- | --- | --- |
| Windows 10/11 x64 | `PDF-Helper-windows-x64.exe` | 파일을 다운로드해 더블클릭 |
| macOS Intel | `PDF-Helper-macos-intel.zip` | 압축 해제 후 `PDF-Helper.app` 실행 |
| macOS Apple Silicon (M 시리즈) | `PDF-Helper-macos-arm64.zip` | 압축 해제 후 `PDF-Helper.app` 실행 |
| Linux x64 (Intel/AMD) | `PDF-Helper-linux-x64` | 실행 권한 부여 후 실행 |
| Linux ARM64 | `PDF-Helper-linux-arm64` | 실행 권한 부여 후 실행 |
| ChromeOS Linux 개발 환경(Crostini) | CPU에 맞는 Linux 파일 | Linux 파일 폴더에 넣고 실행 |

압축 파일과 실행 파일에는 Python 런타임과 필수 Python 패키지가 포함되어 있습니다. **별도의 Python이나 pip 설치는 필요하지 않습니다.** Word 문서 변환은 별도 LibreOffice가 필요하지만 PDF 파일끼리는 LibreOffice 없이 병합할 수 있습니다.

### Linux / ChromeOS

다운로드한 파일이 있는 폴더에서 실행 권한을 한 번 설정합니다.

```bash
chmod +x PDF-Helper-linux-x64
./PDF-Helper-linux-x64
```

ARM64 기기에서는 파일명을 `PDF-Helper-linux-arm64`로 바꾸세요.

일부 Linux 배포판에서는 Qt의 시스템 라이브러리가 추가로 필요할 수 있습니다. ChromeOS에서는 설정 → 개발자 → Linux 개발 환경을 먼저 활성화하세요.

### Windows / macOS 보안 경고

현재 배포 파일에는 상용 코드 서명·공증을 적용하지 않습니다. Windows SmartScreen 또는 macOS Gatekeeper가 출처 미확인 앱이라는 경고를 표시할 수 있습니다. GitHub 릴리즈와 출처가 일치하는지 확인한 경우에만 실행하세요.

macOS에서는 파일을 Finder에서 Control-클릭하여 열거나 시스템 설정 → 개인정보 보호 및 보안에서 앱 실행을 허용해야 할 수 있습니다.

### ChromeOS 파일 드래그 앤 드롭

Crostini의 X11(xcb) GUI에서는 ChromeOS 기본 파일 앱의 드래그 앤 드롭 이벤트가 전달되지 않을 수 있습니다. 파일을 복사(Ctrl+C)한 뒤 PDF Helper의 파일 목록에서 Ctrl+V를 사용하거나 **파일 추가** 메뉴를 이용하세요.

설정은 실행 파일 옆 `data/config/settings.json`, 로그는 `logs/`에 저장되므로 쓰기 가능한 폴더에서 실행하는 것을 권장합니다.

## 관리자: 새 버전 릴리즈하는 방법

릴리즈는 **main에 변경 사항을 Merge한 후** 해당 커밋에 버전 태그를 생성해 진행합니다.

### 1. 준비

1. PR을 main에 Merge합니다.
2. GitHub Actions의 테스트가 통과했는지 확인합니다.
3. `main` 브랜치에서 코드 및 버전을 최종 확인합니다.

### 2. 태그 푸시

로컬 저장소에서:

```bash
git switch main
git pull --ff-only origin main
git tag -a v1.0.0 -m "PDF Helper v1.0.0"
git push origin v1.0.0
```

이미 `v1.0.0` 태그가 있다면 새 버전 번호(예: `v1.0.1`)를 사용합니다. 기존 태그를 덮어쓰지 마세요.

### 3. 자동 빌드 및 릴리즈 확인

태그 `v*`가 푸시되면 [다중 운영체제 빌드](https://github.com/MiSo-13/pdf-helper/actions/workflows/build-release.yml)가 자동 실행됩니다.

1. Windows x64, macOS Intel/Apple Silicon, Linux x64/ARM64를 각각 빌드합니다.
2. 운영체제별 실행 파일을 Actions artifact로 업로드합니다.
3. 모든 빌드가 성공하면 GitHub Release에 파일을 첨부합니다.

릴리즈 위치: https://github.com/MiSo-13/pdf-helper/releases

### 4. 태그 없이 사전 빌드 테스트

GitHub → Actions → **다중 운영체제 빌드** → **Run workflow** → 브랜치 선택 → 실행.

`workflow_dispatch`는 빌드 파일을 Actions Artifacts에만 업로드하며 GitHub Release를 생성하지 않습니다. 검증 결과를 확인한 뒤 태그 릴리즈를 진행하세요.

## 배포 주의 사항

- 현재 배포는 설치 프로그램(MSI/DMG/DEB)이 아닌 **바로 실행하는 독립 실행형 패키지**입니다.
- Windows/macOS의 서명 및 공증은 아직 적용되지 않았습니다.
- macOS와 Linux는 실제 기기에서 처음 실행 테스트를 권장합니다.
- 크림 소르시에르 문양은 사용 허가가 확인되지 않았으므로 **공개 GitHub Release에는 포함하지 않습니다**. 개인용 로컬 빌드만 별도 아이콘을 사용하도록 구성되어 있습니다.
- 공개 Release가 생성되지 않았으면 `releases/latest`에서 다운로드할 파일이 보이지 않을 수 있습니다.
