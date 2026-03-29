"""Tests for PDF generator — clipping, auto-scaling, zone layout (Bug 1)."""

from app.pdf_generator import LabelPDFGenerator


class TestLabelPDFGenerator:
    """Bug 1: draw_label improvements."""

    def test_fit_text_width_no_shrink(self) -> None:
        """Text that already fits should keep original size."""
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas

        buf = BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=A4)
        gen = LabelPDFGenerator()

        result = gen._fit_text_width(c, "Short", "Helvetica", 14, 200)
        assert result == 14

    def test_fit_text_width_shrinks_long_text(self) -> None:
        """Very long text should be shrunk to fit within width."""
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas

        buf = BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=A4)
        gen = LabelPDFGenerator()

        long_text = "A" * 100
        result = gen._fit_text_width(c, long_text, "Helvetica", 20, 50)
        assert result < 20
        assert result >= gen._MIN_FONT_SIZE

    def test_fit_text_width_respects_minimum(self) -> None:
        """Font size should never go below _MIN_FONT_SIZE."""
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas

        buf = BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=A4)
        gen = LabelPDFGenerator()

        impossibly_long = "X" * 1000
        result = gen._fit_text_width(c, impossibly_long, "Helvetica", 20, 10)
        assert result >= gen._MIN_FONT_SIZE

    def test_draw_label_does_not_crash(self) -> None:
        """draw_label should complete without error for normal data."""
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas

        buf = BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=A4)
        gen = LabelPDFGenerator()

        label_data = {
            "product_name": "Paralen 500mg",
            "form": "tbl",
            "amount": 24,
            "price": 89.50,
            "unit_price": 3.73,
            "unit": "ks",
            "price_font_size": 32,
            "text_font_size": 14,
        }
        gen.draw_label(c, 10, 10, label_data)
        c.save()
        assert buf.tell() > 0

    def test_draw_label_with_long_name(self) -> None:
        """draw_label should handle long product names without error."""
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas

        buf = BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=A4)
        gen = LabelPDFGenerator()

        label_data = {
            "product_name": "Very Long Product Name That Exceeds Twenty Five Characters Easily",
            "form": "cps",
            "amount": 100,
            "price": 299.99,
            "unit_price": 3.0,
            "unit": "ks",
            "price_font_size": 48,
            "text_font_size": 24,
        }
        gen.draw_label(c, 10, 10, label_data)
        c.save()
        assert buf.tell() > 0

    def test_generate_pdf_returns_buffer(self) -> None:
        """generate_pdf should return a BytesIO for valid labels."""
        gen = LabelPDFGenerator()
        labels = [
            {
                "product_name": "Test",
                "form": "tbl",
                "amount": 10,
                "price": 50,
                "unit_price": 5.0,
                "unit": "ks",
            }
        ]
        result = gen.generate_pdf(labels)
        assert result is not None
        assert result.read(4) == b"%PDF"

    def test_generate_pdf_empty_returns_none(self) -> None:
        gen = LabelPDFGenerator()
        assert gen.generate_pdf([]) is None
