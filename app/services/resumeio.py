import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone

import pytesseract
import requests
from fastapi import HTTPException
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pytesseract.pytesseract import TesseractError, TesseractNotFoundError

from app.schemas.resumeio import Extension


@dataclass
class ResumeioDownloader:
    """
    Class to download a resume from resume.io and convert it to a PDF.

    Parameters
    ----------
    rendering_token : str
        Rendering Token of the resume to download.
    extension : Extension, optional
        Image extension to download, by default "jpeg".
    image_size : int, optional
        Size of the images to download, by default 3000.
    """

    rendering_token: str
    extension: Extension = Extension.jpeg
    image_size: int = 3000
    METADATA_URL: str = "https://ssr.resume.tools/meta/{rendering_token}?cache={cache_date}"
    IMAGES_URL: str = (
        "https://ssr.resume.tools/to-image/{rendering_token}-{page_id}.{extension}?cache={cache_date}&size={image_size}"
    )

    def __post_init__(self) -> None:
        """Set the cache date to the current time."""
        self.cache_date = datetime.now(timezone.utc).isoformat()[:-10] + "Z"

    def generate_pdf(self) -> bytes:
        """
        Generate a PDF from the resume.io resume.

        Returns
        -------
        bytes
            PDF representation of the resume.
        """
        self.__get_resume_metadata()
        images = self.__download_images()
        pdf = PdfWriter()
        viewport = (self.metadata[0].get("viewport") or {}) if self.metadata else {}
        metadata_w = viewport.get("width")
        metadata_h = viewport.get("height")
        if not metadata_w or not metadata_h:
            raise HTTPException(status_code=502, detail="Resume metadata is missing viewport dimensions.")

        ocr_available = True
        for i, image in enumerate(images):
            image.seek(0)
            image_instance = Image.open(image)
            if ocr_available:
                try:
                    page_pdf = pytesseract.image_to_pdf_or_hocr(image_instance, extension="pdf", config="--dpi 300")
                except (TesseractNotFoundError, TesseractError):
                    ocr_available = False
                    page_pdf = self.__image_to_pdf(image_instance)
            else:
                page_pdf = self.__image_to_pdf(image_instance)

            page = PdfReader(io.BytesIO(page_pdf)).pages[0]
            page_scale = max(page.mediabox.height / metadata_h, page.mediabox.width / metadata_w)
            pdf.add_page(page)

            links = self.metadata[i].get("links") or []
            for link in links:
                link_url = link.pop("url", None)
                if not link_url:
                    continue
                link.update((k, v * page_scale) for k, v in link.items())
                x, y, w, h = link.values()

                link_annotation = Link(rect=(x, y, x + w, y + h), url=link_url)
                pdf.add_annotation(page_number=i, annotation=link_annotation)

        with io.BytesIO() as file:
            pdf.write(file)
            return file.getvalue()

    def __image_to_pdf(self, image: Image.Image) -> bytes:
        """Convert a PIL Image to a PDF without OCR."""
        if image.mode != "RGB":
            image = image.convert("RGB")
        with io.BytesIO() as output:
            image.save(output, format="PDF", resolution=300.0)
            return output.getvalue()

    def __get_resume_metadata(self) -> None:
        """Download the metadata for the resume."""
        response = self.__get(
            self.METADATA_URL.format(rendering_token=self.rendering_token, cache_date=self.cache_date),
        )
        content: dict[str, list] = json.loads(response.text)
        pages = content.get("pages") or []
        if not pages:
            raise HTTPException(status_code=502, detail="Resume metadata is missing pages.")
        self.metadata = pages

    def __download_images(self) -> list[io.BytesIO]:
        """Download the images for the resume.

        Returns
        -------
        list[io.BytesIO]
            List of image files.
        """
        images = []
        for page_id in range(1, 1 + len(self.metadata)):
            image_url = self.IMAGES_URL.format(
                rendering_token=self.rendering_token,
                page_id=page_id,
                extension=self.extension.value,
                cache_date=self.cache_date,
                image_size=self.image_size,
            )
            response = self.__get(image_url)
            images.append(io.BytesIO(response.content))

        return images

    def __get(self, url: str) -> requests.Response:
        """Get a response from a URL.

        Parameters
        ----------
        url : str
            URL to get.

        Returns
        -------
        requests.Response
            Response object.

        Raises
        ------
        HTTPException
            If the response status code is not 200.
        """
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/136.0.0.0 Safari/537.36"
                    ),
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail="Unable to reach resume.io services.") from exc
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Unable to download resume (rendering token: {self.rendering_token})",
            )
        return response
