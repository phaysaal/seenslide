"""PDF generation for slide presentations."""

import logging
import io
import uuid
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

from modules.cloud.models import CloudSlide

logger = logging.getLogger(__name__)


class SlidePDFGenerator:
    """Generates PDF documents from slide images."""

    def __init__(
        self,
        storage_path: str = "/tmp/seenslide_pdfs"
    ):
        """Initialize PDF generator.

        Args:
            storage_path: Directory to store generated PDFs
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"PDF generator initialized at {self.storage_path}")

    def generate_pdf(
        self,
        slides: List[CloudSlide],
        session_info: Optional[Dict[str, Any]] = None,
        page_size: tuple = A4,
        add_watermark: bool = False,
        watermark_text: str = "SeenSlide"
    ) -> tuple[str, bytes]:
        """Generate PDF from multiple slides.

        Args:
            slides: List of CloudSlide objects to include
            session_info: Optional session metadata (presenter name, etc.)
            page_size: PDF page size (default: A4)
            add_watermark: Whether to add watermark
            watermark_text: Text to use for watermark

        Returns:
            Tuple of (pdf_id, pdf_bytes)

        Raises:
            ValueError: If slides list is empty or slides don't exist
        """
        if not slides:
            raise ValueError("No slides provided for PDF generation")

        # Generate unique PDF ID
        pdf_id = str(uuid.uuid4())

        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=page_size)
            page_width, page_height = page_size

            # Add metadata
            if session_info:
                c.setAuthor(session_info.get("presenter_name", "SeenSlide User"))
                c.setTitle(f"Presentation - {session_info.get('session_id', 'Unknown')}")
            c.setCreator("SeenSlide")
            c.setSubject("Presentation Slides")

            # Process each slide
            for idx, slide in enumerate(slides, 1):
                logger.info(f"Adding slide {idx}/{len(slides)} to PDF")

                # Check if slide file exists
                slide_path = Path(slide.file_path)
                if not slide_path.exists():
                    logger.warning(f"Slide file not found: {slide.file_path}")
                    continue

                # Open and process image
                try:
                    img = Image.open(slide_path)

                    # Calculate dimensions to fit page while maintaining aspect ratio
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height

                    # Leave margins (0.5 inch on each side)
                    max_width = page_width - (1 * inch)
                    max_height = page_height - (1 * inch)

                    if aspect_ratio > (max_width / max_height):
                        # Width is the limiting factor
                        draw_width = max_width
                        draw_height = max_width / aspect_ratio
                    else:
                        # Height is the limiting factor
                        draw_height = max_height
                        draw_width = max_height * aspect_ratio

                    # Center the image on the page
                    x = (page_width - draw_width) / 2
                    y = (page_height - draw_height) / 2

                    # Draw the image
                    c.drawImage(
                        ImageReader(img),
                        x, y,
                        width=draw_width,
                        height=draw_height,
                        preserveAspectRatio=True
                    )

                    # Add watermark if requested
                    if add_watermark:
                        self._add_watermark(c, watermark_text, page_width, page_height)

                    # Add slide number footer
                    c.setFont("Helvetica", 8)
                    c.setFillColorRGB(0.5, 0.5, 0.5)
                    footer_text = f"Slide {slide.slide_number}"
                    if session_info:
                        footer_text += f" | {session_info.get('presenter_name', '')}"
                    c.drawString(0.5 * inch, 0.3 * inch, footer_text)

                    # Add page
                    c.showPage()

                except Exception as e:
                    logger.error(f"Failed to process slide {slide.slide_number}: {e}")
                    continue

            # Finalize PDF
            c.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()

            # Save PDF to disk
            pdf_path = self.storage_path / f"{pdf_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)

            logger.info(
                f"Generated PDF {pdf_id} with {len(slides)} slides "
                f"({len(pdf_bytes)} bytes)"
            )

            return pdf_id, pdf_bytes

        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise ValueError(f"PDF generation failed: {e}")

    def generate_single_slide_pdf(
        self,
        slide: CloudSlide,
        session_info: Optional[Dict[str, Any]] = None,
        add_watermark: bool = False
    ) -> bytes:
        """Generate PDF from a single slide.

        Args:
            slide: CloudSlide object
            session_info: Optional session metadata
            add_watermark: Whether to add watermark

        Returns:
            PDF bytes

        Raises:
            ValueError: If slide doesn't exist
        """
        _, pdf_bytes = self.generate_pdf(
            slides=[slide],
            session_info=session_info,
            add_watermark=add_watermark
        )
        return pdf_bytes

    def _add_watermark(
        self,
        c: canvas.Canvas,
        text: str,
        page_width: float,
        page_height: float
    ):
        """Add diagonal watermark to PDF page.

        Args:
            c: ReportLab canvas
            text: Watermark text
            page_width: Page width
            page_height: Page height
        """
        c.saveState()

        # Set watermark properties
        c.setFont("Helvetica-Bold", 60)
        c.setFillColorRGB(0.9, 0.9, 0.9, alpha=0.3)

        # Calculate rotation and position
        c.translate(page_width / 2, page_height / 2)
        c.rotate(45)

        # Draw watermark
        text_width = c.stringWidth(text, "Helvetica-Bold", 60)
        c.drawString(-text_width / 2, 0, text)

        c.restoreState()

    def get_pdf_file(self, pdf_id: str) -> Optional[bytes]:
        """Retrieve generated PDF file.

        Args:
            pdf_id: PDF identifier

        Returns:
            PDF bytes if found, None otherwise
        """
        pdf_path = self.storage_path / f"{pdf_id}.pdf"

        if not pdf_path.exists():
            return None

        try:
            with open(pdf_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read PDF file: {e}")
            return None

    def delete_pdf(self, pdf_id: str) -> bool:
        """Delete a generated PDF.

        Args:
            pdf_id: PDF identifier

        Returns:
            True if deleted, False if not found
        """
        pdf_path = self.storage_path / f"{pdf_id}.pdf"

        if not pdf_path.exists():
            return False

        try:
            pdf_path.unlink()
            logger.info(f"Deleted PDF {pdf_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete PDF: {e}")
            return False

    def cleanup_old_pdfs(self, max_age_hours: int = 24):
        """Clean up old PDF files.

        Args:
            max_age_hours: Maximum age in hours before deleting
        """
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)

        deleted_count = 0
        for pdf_file in self.storage_path.glob("*.pdf"):
            try:
                if pdf_file.stat().st_mtime < cutoff_time:
                    pdf_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete old PDF {pdf_file}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old PDF files")
