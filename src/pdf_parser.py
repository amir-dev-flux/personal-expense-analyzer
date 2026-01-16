from datetime import datetime
import pdfplumber
import re


def parse_hdfc_pdf(pdf_path):
    transactions = []

    # Example line we expect inside text:
    # 31/08/25 POS5129XXXX BLINKIT 323.00 164.32
    # or
    # 03/09/25 UPI-BLINKIT ... 249.00 3869.05

    # Regex pattern:
    pattern = re.compile(
        r"(\d{2}/\d{2}/\d{2,4})\s+(.*?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})"
    )

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                match = pattern.search(line)

                if not match:
                    continue

                date_str, narration, amount_str = match.groups()

                # Parse date (supports both 25 and 2025)
                try:
                    date = datetime.strptime(date_str, "%d/%m/%Y").date()
                except ValueError:
                    date = datetime.strptime(date_str, "%d/%m/%y").date()

                # Clean amount
                amount = float(amount_str.replace(",", ""))

                # HDFC withdrawal amounts appear as spend (assume expense)
                transactions.append({
                    "date": str(date),
                    "description": narration.strip(),
                    "amount": -amount   # treat as expense
                })
    return transactions
