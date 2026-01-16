import csv
from collections import defaultdict
from datetime import datetime

CATEGORIES = {
    "Food & Delivery": [
        "swiggy", "zomato", "blinkit", "domino", "pizza", "restaurant", "cafe", "food"
    ],

    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho"
    ],

    "Subscriptions": [
        "netflix", "spotify", "prime", "hotstar", "youtube"
    ],

    "Transport": [
        "uber", "ola", "rapido", "metro", "irctc"
    ],

    "Bills & Utilities": [
        "electricity", "water", "broadband", "airtel", "jio", "recharge"
    ],

    "Investments": [
        "zerodha", "groww", "coin", "mutual", "sip"
    ],

    "Bank Transfers": [
        "imps", "neft", "rtgs"
    ]
}


def load_transactions_from_csv(csv_file_path):
    import csv

    transactions = []

    with open(csv_file_path, newline="", encoding="utf-8-sig") as file:
        sample = file.read(2048)
        file.seek(0)

        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        reader = csv.DictReader(file, dialect=dialect)

        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        for i, row in enumerate(reader):
            date = (row.get("date") or "").strip()
            description = (row.get("description") or "").strip()
            amount_raw = (row.get("amount") or "").strip()

            if not date or not description or not amount_raw:
                continue

            try:
                amount_clean = (
                    amount_raw
                    .replace("₹", "")
                    .replace(",", "")
                    .replace(" ", "")
                )

                amount = float(amount_clean)

                transactions.append({
                    "date": date,
                    "description": description,
                    "amount": -abs(amount)
                })

            except Exception as e:
                print(f"Skipped row {i}: amount='{amount_raw}' error={e}")

            
    return transactions



from collections import defaultdict
from datetime import datetime


def analyze_expenses(file_path):
    transactions = load_transactions(file_path)
    if not transactions:
        raise ValueError("Could not extract any transactions. Please upload a valid bank statement or properly formatted CSV.")
    total_spent = 0
    transaction_count = 0
    max_expense = 0
    max_expense_desc = ""

    category_totals = defaultdict(float)
    daily_totals = defaultdict(float)

    for txn in transactions:
        try:
            date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
            desc = txn["description"]
            amount = float(txn["amount"])

        # We only analyze expenses (money going out)
            if amount < 0:
                spend = abs(amount)

                total_spent += spend
                transaction_count += 1
                daily_totals[date] += spend

                category = categorize(desc)
                category_totals[category] += spend

                if spend > max_expense:
                    max_expense = spend
                    max_expense_desc = desc

        except Exception:
            continue


    highest_category = max(category_totals, key=category_totals.get, default="N/A")
    top_3_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    highest_spending_day = max(daily_totals, key=daily_totals.get, default=None)
    average_spend = round(total_spent / transaction_count, 2) if transaction_count else 0
    

    return {
        "total_spent": round(total_spent, 2),
        "transaction_count": transaction_count,
        "average_spend": round(average_spend, 2),
        "max_expense": round(max_expense, 2),
        "max_expense_desc": max_expense_desc,
        "highest_category": highest_category,
        "top_3_categories": top_3_categories,
        "highest_spending_day": str(highest_spending_day) if highest_spending_day else "N/A",
        "category_totals": {k: round(v, 2) for k, v in category_totals.items()},
        "generated": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_pdf_report(results, output_path, filename, generated_at):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="Title",
        fontSize=22,
        spaceAfter=20,
        textColor=colors.HexColor("#1f2937")
    )

    header_style = ParagraphStyle(
        name="Header",
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor("#2563eb")
    )

    text_style = ParagraphStyle(
        name="Text",
        fontSize=11,
        spaceAfter=6
    )

    elements = []

    # Title
    elements.append(Paragraph("Personal Expense Report", title_style))
    elements.append(Paragraph(f"File analyzed: {filename}", text_style))
    elements.append(Paragraph(f"Generated on: {generated_at}", text_style))
    elements.append(Spacer(1, 16))


    # Summary section
    elements.append(Paragraph("Summary", header_style))

    summary_data = [
        ["Total Spent", f"₹{results['total_spent']}"],
        ["Transactions", results["transaction_count"]],
        ["Average Spend", f"₹{results['average_spend']}"],
        ["Highest Expense", f"₹{results['max_expense']} ({results['max_expense_desc']})"],
        ["Highest Spending Day", results["highest_spending_day"]],
        ["Top Category", results["highest_category"]],
    ]

    summary_table = Table(summary_data, colWidths=[200, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))

    elements.append(summary_table)

    # Top categories
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Top 3 Categories", header_style))

    top_cat_data = [["Category", "Amount"]]
    for cat, amt in results["top_3_categories"]:
        top_cat_data.append([cat, f"₹{amt}"])

    top_table = Table(top_cat_data, colWidths=[300, 200])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e5edff")),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(top_table)

    # Category breakdown
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Category Breakdown", header_style))

    cat_data = [["Category", "Total"]]
    for cat, amt in results["category_totals"].items():
        cat_data.append([cat, f"₹{amt}"])

    cat_table = Table(cat_data, colWidths=[300, 200])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e5edff")),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(cat_table)

    # Build PDF
    doc.build(elements)

import csv
from src.pdf_parser import parse_hdfc_pdf


def load_transactions(file_path):
    if file_path.endswith(".csv"):
        return load_transactions_from_csv(file_path)
    elif file_path.endswith(".pdf"):
        return parse_hdfc_pdf(file_path)
    else:
        raise ValueError("Unsupported file type")

def categorize(description):
    desc = description.lower()

    for category, keywords in CATEGORIES.items():
        if any(word in desc for word in keywords):
            return category

    if "atm" in desc:
        return "Cash Withdrawal"

    if "upi" in desc:
        return "UPI Transfer"

    return "Other"
