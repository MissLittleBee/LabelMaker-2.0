import logging
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas

logger = logging.getLogger(__name__)


def get_font_path(font_name: str) -> str:
    """Find path to font."""
    if getattr(sys, "frozen", False):
        # Path in EXE (v _internal/static/fonts)
        base_path = Path(sys._MEIPASS) / "static" / "fonts"
    else:
        # Dev path
        base_path = Path(__file__).parent.parent / "static" / "fonts"

    return str(base_path / font_name)


try:
    regular_path = get_font_path("DejaVuSans.ttf")
    bold_path = get_font_path("DejaVuSans-Bold.ttf")

    pdfmetrics.registerFont(TTFont("DejaVuSans", regular_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))

    FONT_REGULAR = "DejaVuSans"
    FONT_BOLD = "DejaVuSans-Bold"
    logger.info(f"✓ Fonts registered from: {regular_path}")
except Exception as e:
    logger.warning(f"Could not register fonts: {e}. Fallback to Helvetica.")
    FONT_REGULAR = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"


class LabelPDFGenerator:
    """Generate PDF with pharmacy price labels.

    Based on the original label-maker template:
    - 32 labels per A4 page (4 columns x 8 rows)
    - Matches the docx template format
    """

    # Label dimensions (calculated for 32 labels on A4)
    # A4 is 210mm x 297mm
    LABEL_WIDTH = 48 * mm  # ~48mm wide (4 per row with margins)
    LABEL_HEIGHT = 35 * mm  # ~35mm tall (8 per column with margins)

    # Page margins
    MARGIN_LEFT = 6 * mm
    MARGIN_TOP = 6 * mm
    MARGIN_BETWEEN = 0 * mm  # No space between labels - they share borders

    def __init__(self) -> None:
        """Initialize PDF generator."""
        self.page_width: float
        self.page_height: float
        self.page_width, self.page_height = A4
        logger.debug(
            f"PDF Generator initialized (Page: {self.page_width}x{self.page_height})"
        )

    def calculate_label_positions(self) -> List[Tuple[float, float]]:
        """Calculate how many labels fit on an A4 page and their positions."""
        # Calculate labels per row and column
        usable_width = self.page_width - (2 * self.MARGIN_LEFT)
        usable_height = self.page_height - (2 * self.MARGIN_TOP)

        labels_per_row = int(usable_width / (self.LABEL_WIDTH + self.MARGIN_BETWEEN))
        labels_per_column = int(
            usable_height / (self.LABEL_HEIGHT + self.MARGIN_BETWEEN)
        )

        positions = []
        for row in range(labels_per_column):
            for col in range(labels_per_row):
                x = self.MARGIN_LEFT + col * (self.LABEL_WIDTH + self.MARGIN_BETWEEN)
                # Start from top of page (PDF coordinates start at bottom)
                y = (
                    self.page_height
                    - self.MARGIN_TOP
                    - (row + 1) * (self.LABEL_HEIGHT + self.MARGIN_BETWEEN)
                )
                positions.append((x, y))

        logger.debug(
            f"Calculated {len(positions)} label positions per page ({labels_per_row}x{labels_per_column})"
        )
        return positions

    def draw_label(
        self,
        pdf_canvas: pdf_canvas.Canvas,
        x: float,
        y: float,
        label_data: Dict[str, Any],
    ) -> None:
        """
        Draw a single pharmacy price label.

        - Product name at top
        - Large price in center
        - Unit price at bottom (e.g., "1ml = 1,94Kč")
        """
        logger.debug(f"Drawing label at ({x}, {y}): {label_data['product_name']}")

        # Save canvas state
        pdf_canvas.saveState()

        # Draw border (light gray for cutting guide)
        pdf_canvas.setLineWidth(0.3)
        pdf_canvas.setStrokeColorRGB(0.7, 0.7, 0.7)  # Light gray
        pdf_canvas.rect(x, y, self.LABEL_WIDTH, self.LABEL_HEIGHT, stroke=1, fill=0)

        # Center X position for all text
        text_x = x + self.LABEL_WIDTH / 2

        # Prepare data
        product_name = label_data["product_name"]
        unit = label_data.get("unit", "ml")
        amount = label_data["amount"]
        form = label_data["form"]
        price_font_size = int(label_data.get("price_font_size", 34))
        text_font_size = int(label_data.get("text_font_size", 10))

        # First row: Product name (split if needed), second row: rest of name + form + amount + unit
        pdf_canvas.setFillColorRGB(0, 0, 0)  # Black
        pdf_canvas.setFont(FONT_BOLD, text_font_size)

        form_info = f"{form} {amount:.0f} {unit}"
        MAX_CHARS_PER_LINE = 25

        # Try to fit product name on one or two lines, always keep form_info together on line 2
        if len(product_name) <= MAX_CHARS_PER_LINE:
            # All fits on one line
            text_y = y + self.LABEL_HEIGHT - (text_font_size + 2) * mm / 2
            pdf_canvas.drawCentredString(text_x, text_y, f"{product_name}")
            # Second line: form info (same font size)
            pdf_canvas.setFont(FONT_BOLD, text_font_size)
            text_y = y + self.LABEL_HEIGHT - (text_font_size + 8) * mm / 2
            pdf_canvas.drawCentredString(text_x, text_y, form_info)
        else:
            # Split product name at nearest space before limit
            split_idx = product_name.rfind(" ", 0, MAX_CHARS_PER_LINE)
            if split_idx == -1:
                # No space found, hard split
                line1 = product_name[:MAX_CHARS_PER_LINE]
                line2 = product_name[MAX_CHARS_PER_LINE:]
            else:
                line1 = product_name[:split_idx]
                line2 = product_name[split_idx + 1 :]
            # Draw first line (part of product name)
            text_y = y + self.LABEL_HEIGHT - (text_font_size + 2) * mm / 2
            pdf_canvas.drawCentredString(text_x, text_y, line1)
            # Draw second line: rest of name + form info (same font size)
            pdf_canvas.setFont(FONT_BOLD, text_font_size)
            text_y = y + self.LABEL_HEIGHT - (text_font_size + 8) * mm / 2
            second_line = line2.strip() + ("  " if line2.strip() else "") + form_info
            pdf_canvas.drawCentredString(text_x, text_y, second_line.strip())

        # Second row: Large price (main focus)
        pdf_canvas.setFont(FONT_BOLD, price_font_size)
        price_text = f"{label_data['price']:.0f},-"
        text_y = y + self.LABEL_HEIGHT / 2 - 4 * mm
        pdf_canvas.drawCentredString(text_x, text_y, price_text)

        # Third row: Unit price at bottom (e.g., "1tbl = 14,95 Kč")
        pdf_canvas.setFont(FONT_REGULAR, text_font_size)
        unit_price = label_data["unit_price"]
        # Format: "1tbl = 14,95 Kč" (without space after number, with space before Kč)
        unit_price_text = f"1 {unit} = {unit_price:.2f} Kč".replace(".", ",")
        text_y = y + 7 * mm
        pdf_canvas.drawCentredString(text_x, text_y, unit_price_text)

        # Restore canvas state
        pdf_canvas.restoreState()

    def generate_pdf(self, labels: List[Dict[str, Any]]) -> Optional[BytesIO]:
        """
        Generate PDF with all labels marked for printing.

        Args:
            labels: List of label dictionaries with keys:
                   - product_name
                   - form
                   - amount
                   - price
                   - unit_price
                   - unit (optional, defaults to 'ml')

        Returns:
            BytesIO: PDF file in memory
        """
        logger.info(f"Generating PDF with {len(labels)} labels")

        if not labels:
            logger.warning("No labels provided for PDF generation")
            return None

        # Create PDF in memory
        pdf_buffer = BytesIO()
        pdf = pdf_canvas.Canvas(pdf_buffer, pagesize=A4)
        pdf.setTitle("Pharmacy Price Labels")
        pdf.setAuthor("LabelMaker 2.0")

        # Calculate label positions on page
        positions = self.calculate_label_positions()
        labels_per_page = len(positions)

        logger.debug(f"Labels per page: {labels_per_page}")

        # Draw labels
        label_count = 0
        for i, label_data in enumerate(labels):
            position_index = i % labels_per_page

            # Start new page if needed
            if i > 0 and position_index == 0:
                pdf.showPage()
                logger.debug(f"Started new page for label {i + 1}")

            # Get position for this label
            x, y = positions[position_index]

            # Draw the label
            self.draw_label(pdf, x, y, label_data)
            label_count += 1

        # Save PDF
        pdf.save()
        pdf_buffer.seek(0)

        logger.info(
            f"PDF generated successfully with {label_count} labels on {(label_count + labels_per_page - 1) // labels_per_page} page(s)"
        )
        return pdf_buffer


def generate_labels_pdf(labels: List[Any]) -> Optional[BytesIO]:
    """
    Convenience function to generate PDF from label list.

    Args:
        labels: List of Label model instances or dictionaries

    Returns:
        BytesIO: PDF file in memory
    """
    generator = LabelPDFGenerator()

    # Convert Label models to dictionaries if needed
    label_data: List[Dict[str, Any]] = []
    for label in labels:
        if hasattr(label, "to_dict"):
            data = label.to_dict()
        else:
            data = label

        # Add unit field (get from form if available)
        if "unit" not in data:
            data["unit"] = "ml"  # Default unit

        label_data.append(data)

    return generator.generate_pdf(label_data)
