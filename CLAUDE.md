# Bullet Journal PDF Generator for reMarkable Paper Pro Move

This project generates a Bullet Journal PDF optimized for reMarkable Paper Pro Move (rPPM).

## Project Structure

- `generate_rppm_pdf_v2.py` - Main script to generate the PDF
- `original/Bullet Journal.pdf` - Original reference PDF
- `output/BulletJournal_rPPM_v2.pdf` - Generated output

## Usage

```bash
python3 generate_rppm_pdf_v2.py
```

## Requirements

- Python 3
- PyMuPDF (`fitz`)
- EB Garamond font installed at `/Library/Fonts/EBGaramond-Regular.ttf`

## Output Specifications

- Page size: 954 x 1696 pixels
- Optimized for rPPM screen with top toolbar safe zone (130px)
- 546 pages total
