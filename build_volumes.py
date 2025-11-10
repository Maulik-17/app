import os
import requests
from PIL import Image
from io import BytesIO

from drive_upload import upload_to_drive

# === SETTINGS ===

FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")  # store in Render env
max_pages_per_chapter = 100

# Which chapters belong to which volume
volumes = {
    1: range(1, 8),
    2: range(8, 16),
    3: range(16, 24),
    # … add remaining if needed
}

base_url = "https://hot.planeptune.us/manga/One-Piece/{chapter:04d}-{page:03d}.png"


def build_volumes():
    for volume, chapter_range in volumes.items():
        print(f"\n=== Building Volume {volume} ===")

        volume_images = []

        for chapter in chapter_range:
            for page in range(1, max_pages_per_chapter + 1):

                url = base_url.format(chapter=chapter, page=page)
                response = requests.get(url)

                if response.status_code != 200:
                    break

                try:
                    img = Image.open(BytesIO(response.content)).convert("RGB")
                    volume_images.append(img)
                except:
                    break

        if len(volume_images):
            tmp_pdf = f"/tmp/Volume-{volume:02d}.pdf"
            first = volume_images[0]
            first.save(tmp_pdf, save_all=True, append_images=volume_images[1:])
            print(f"✅ Volume {volume} PDF saved temp → {tmp_pdf}")

            upload_to_drive(tmp_pdf)
            os.remove(tmp_pdf)

        else:
            print(f"⚠ No pages found for volume {volume}")
