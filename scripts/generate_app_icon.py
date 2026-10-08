"""사용자가 선택한 크림 소르시에르 문양으로 로컬 앱 아이콘 생성.

원본 이미지는 Personal Use 표시가 있으므로 저장소에는 원본/변환본을 포함하지 않습니다.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

SOURCE_URL = (
    "https://www.clipartmax.com/png/middle/"
    "80-804083_fairy-tail-crime-sorciere-guild-logo-by-elsid37-fairy-tail-crime-sorciere.png"
)
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"


def generate() -> None:
    with urlopen(Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as response:
        original = Image.open(BytesIO(response.read())).convert("RGBA")
    if original.width < 256 or original.height < 256:
        raise ValueError("아이콘 원본 해상도가 너무 낮습니다.")

    # 투명도를 유지하면서 정사각형 내에 문양을 중앙 정렬한다.
    original.thumbnail((880, 880), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    canvas.alpha_composite(original, ((1024 - original.width) // 2, (1024 - original.height) // 2))
    OUT.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT / "app-icon.png")
    canvas.save(OUT / "app-icon.ico", format="ICO",
                sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    canvas.save(OUT / "app-icon.icns", format="ICNS")
    print("아이콘 생성:", OUT)
    print("참고: 원본 출처와 사용 허가 범위를 확인한 뒤 배포하세요.")


if __name__ == "__main__":
    generate()
