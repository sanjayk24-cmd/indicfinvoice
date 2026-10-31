#!/usr/bin/env python3
"""
scripts/generate_rich_mock_db.py

Generates an expanded, highly realistic MockBank database (mockbank/db.json)
featuring 24 diverse Indian banking personas covering:
  - Account edge cases: Standard salary, zero-balance (C014), negative overdraft (C015),
    ultra-HNW multi-crore (C016), dormant (C005), frozen/lien hold (C017), joint account (C019).
  - Loan edge cases: Active crop loan, home loan, personal loan, overdue loan with penal interest (C010),
    fully paid closed loan (C011), education loan with moratorium (C007).
  - Transaction edge cases: Over 850+ realistic transactions with:
    - Micro amounts (0.50, 1.00, 2.50)
    - Fractional decimals (49.99, 1250.75, 87.30, 999.50)
    - Round & high amounts (500, 1000, 1,00,000, 25,00,000)
    - Varied statuses: completed, pending, failed, reversed
    - Varied types: debit, credit
    - Rich Indian merchants: UPI (Swiggy, Zomato, Blinkit), Salary, PM-KISAN,
      Electricity, Indane Gas, FASTag, Mutual Fund SIP, ATM cash dispensing failed,
      duplicate debits for dispute testing.
  - Zero transaction customer (C009) for testing empty-state UI and test assertions.
  - Strictly preserves baseline requirements for C001 (PIN 1234, TXN-9001, CLM-771, savings 45000, kcc 25000).
"""

import json
import os
import random
from datetime import date, timedelta

# Output path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DB_PATH = os.path.join(PROJECT_DIR, "mockbank", "db.json")

# Fixed anchor date for reproducibility
ANCHOR_DATE = date(2026, 10, 31)

def get_date_str(days_ago: int) -> str:
    return (ANCHOR_DATE - timedelta(days=days_ago)).isoformat()

def add_historical_transactions(txns_dict, cid_num, persona_type, count=25):
    """
    Adds persona-specific historical transactions spread over the past 90 days.
    """
    templates = {
        "salaried": [
            (349.0, "debit", "completed", "UPI · Swiggy Gourmet Lunch"),
            (120.0, "debit", "completed", "UPI · Zepto Quick Grocery"),
            (2500.0, "debit", "completed", "Fuel · Indian Oil Corporation"),
            (1450.75, "debit", "completed", "Utility · Electricity Bill Payment"),
            (299.0, "debit", "completed", "Telecom · Prepaid Mobile Recharge"),
            (4500.0, "debit", "completed", "Retail · DMart Supermarket Basket"),
            (5000.0, "debit", "completed", "Investment · Monthly Mutual Fund SIP"),
            (1500.0, "debit", "completed", "ATM · Cash Withdrawal Branch ATM"),
            (450.0, "debit", "completed", "Dining · Cafe Coffee Day"),
            (85.0, "debit", "completed", "UPI · Chai & Snacks Tapri"),
            (1800.0, "debit", "completed", "Medical · Apollo Pharmacy Refill"),
            (750.0, "debit", "completed", "FASTag · NHAI Highway Toll"),
            (45000.0, "credit", "completed", "Salary · Monthly Corporate Salary Credit"),
            (12000.0, "debit", "completed", "Loan · Monthly Loan Auto-Debit"),
            (99.0, "debit", "completed", "Entertainment · Music Streaming Subscription"),
            (2100.0, "debit", "completed", "Shopping · Amazon India Essentials"),
            (350.0, "debit", "completed", "UPI · Fresh Bakery & Bread"),
            (650.0, "debit", "completed", "Transport · Uber City Commute"),
            (850.0, "debit", "completed", "Utility · Piped Natural Gas Bill")
        ],
        "rural": [
            (2000.0, "credit", "completed", "DBT · PM-KISAN Subsidy Installment"),
            (850.0, "debit", "completed", "Agri · IFFCO Organic Bio-Fertilizer"),
            (1200.0, "debit", "completed", "Agri · Certified Hybrid Vegetable Seeds"),
            (3000.0, "debit", "completed", "Fuel · Tractor High-Speed Diesel"),
            (500.0, "debit", "completed", "Micro-ATM · Cash Withdrawal Rural CSP"),
            (14500.0, "credit", "completed", "Mandi · Crop Produce Harvest Sale"),
            (1200.0, "debit", "completed", "Utility · Agriculture Power Feeder"),
            (450.0, "debit", "completed", "Veterinary · Dairy Cow Mineral Tonic"),
            (250.0, "debit", "completed", "Household · Village Haat Kirana Store"),
            (199.0, "debit", "completed", "Telecom · BSNL Rural Mobile Recharge"),
            (4500.0, "debit", "completed", "Loan · KCC Agriculture Crop Loan Instalment"),
            (8500.0, "credit", "completed", "Produce · Sugarcane Cooperative Mill Credit"),
            (1500.0, "debit", "completed", "Machinery · Water Pump Motor Repair"),
            (350.0, "debit", "completed", "UPI · Rural Hardware Store Spares"),
            (2000.0, "debit", "completed", "Wages · Farm Daily Laborer Wages")
        ],
        "hni": [
            (25000.0, "credit", "completed", "Dividend · Bluechip Corporate Equity Dividend"),
            (18500.0, "debit", "completed", "Dining · Luxury Five-Star Hotel Dining"),
            (45000.0, "debit", "completed", "Travel · Premium Airline Flight Booking"),
            (12500.0, "debit", "completed", "Club · Golf & Country Club Monthly Dues"),
            (50000.0, "debit", "completed", "Investment · Portfolio Wealth Management"),
            (3500.0, "debit", "completed", "Fuel · Premium Synthetic Engine Fuel"),
            (8500.0, "debit", "completed", "Retail · Designer Luxury Apparel"),
            (250000.0, "credit", "completed", "Treasury · Fixed Yield Instrument Maturity"),
            (75000.0, "debit", "completed", "Property · Penthouse Maintenance Association"),
            (1200.0, "debit", "completed", "Subscription · Financial Times International")
        ],
        "merchant": [
            (150.0, "credit", "completed", "QR Soundbox · Customer UPI Daily Purchase"),
            (280.0, "credit", "completed", "QR Soundbox · Customer UPI Cooking Oil & Salt"),
            (85.0, "credit", "completed", "QR Soundbox · Customer UPI Soap & Detergent"),
            (520.0, "credit", "completed", "QR Soundbox · Customer UPI Basmati Rice"),
            (12000.0, "debit", "completed", "Wholesale · FMCG Supplier Invoice Settlement"),
            (1850.0, "debit", "completed", "Utility · Commercial High-Load Electricity"),
            (3500.0, "debit", "completed", "Tax · GST Composition Scheme Tax"),
            (125.0, "debit", "completed", "Fee · QR Soundbox Monthly Connectivity Fee"),
            (8500.0, "debit", "completed", "Loan · Business Equipment Loan Installment"),
            (450.0, "credit", "completed", "QR Soundbox · Customer UPI Dry Fruits")
        ]
    }

    pool = templates.get(persona_type, templates["salaried"])
    for i in range(count):
        tmpl = pool[i % len(pool)]
        days = 15 + (i * 3)
        if days > 110:
            days = 110
        ref_id = f"TXN-{cid_num}{100+i:03d}"
        if ref_id not in txns_dict:
            txns_dict[ref_id] = {
                "amount": tmpl[0],
                "date": get_date_str(days),
                "description": tmpl[3],
                "type": tmpl[1],
                "status": tmpl[2],
                "currency": "INR"
            }

def build_database():
    db = {}

    # ==========================================
    # C001: Aarav Sharma - Primary Retail Benchmark
    # ==========================================
    c001_txns = {
        "TXN-9001": {
            "amount": 1500,
            "date": "2026-10-24",
            "description": "UPI · Fresh Vegetables & Groceries",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-9002": {
            "amount": 75000,
            "date": "2026-10-20",
            "description": "IMPS · House Rent Transfer to Landlord",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001000": {
            "amount": 1.0,
            "date": get_date_str(3),
            "description": "UPI · Chai Tapri Micro Payment",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001001": {
            "amount": 49.99,
            "date": get_date_str(4),
            "description": "NEFT · Reimbursement Pending",
            "type": "credit",
            "status": "pending",
            "currency": "INR"
        },
        "TXN-001002": {
            "amount": 2500.0,
            "date": get_date_str(5),
            "description": "ATM · Cash Withdrawal HDFC ATM",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001003": {
            "amount": 45000.0,
            "date": get_date_str(7),
            "description": "NEFT · Monthly Salary Credit TechCorp",
            "type": "credit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001004": {
            "amount": 1250.75,
            "date": get_date_str(8),
            "description": "Utility · BESCOM Electricity Bill",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001005": {
            "amount": 0.50,
            "date": get_date_str(9),
            "description": "Refund · Penny Verification Pending",
            "type": "credit",
            "status": "pending",
            "currency": "INR"
        },
        "TXN-001006": {
            "amount": 349.0,
            "date": get_date_str(10),
            "description": "UPI · Swiggy Food Delivery",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001007": {
            "amount": 2499.0,
            "date": get_date_str(11),
            "description": "E-Commerce · Amazon India Diwal Shopping",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001008": {
            "amount": 500.0,
            "date": get_date_str(12),
            "description": "FASTag · NHAI Electronic Toll Debit",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001009": {
            "amount": 120.0,
            "date": get_date_str(14),
            "description": "UPI · Zepto 10-Min Grocery Delivery",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001010": {
            "amount": 5000.0,
            "date": get_date_str(15),
            "description": "Investment · Nippon India MF Monthly SIP",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001011": {
            "amount": 950.0,
            "date": get_date_str(16),
            "description": "Utility · Indane LPG Cylinder Booking",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001012": {
            "amount": 3200.0,
            "date": get_date_str(18),
            "description": "Fuel · Indian Oil Petrol Pump",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001013": {
            "amount": 799.0,
            "date": get_date_str(19),
            "description": "Telecom · Airtel Xstream Fiber Broadband",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001014": {
            "amount": 12000.0,
            "date": get_date_str(21),
            "description": "EMI · Personal Loan Auto Debit",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001015": {
            "amount": 250.0,
            "date": get_date_str(22),
            "description": "UPI · Barber Haircut Salon",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001016": {
            "amount": 15000.0,
            "date": get_date_str(25),
            "description": "Transfer · Sent to Parents via IMPS",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001017": {
            "amount": 650.0,
            "date": get_date_str(28),
            "description": "Entertainment · PVR Cinema Movie Tickets",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001018": {
            "amount": 45000.0,
            "date": get_date_str(37),
            "description": "NEFT · Monthly Salary Credit TechCorp",
            "type": "credit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001019": {
            "amount": 299.0,
            "date": get_date_str(38),
            "description": "Telecom · Jio Mobile 84-Day Recharge",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001020": {
            "amount": 1850.50,
            "date": get_date_str(40),
            "description": "Health · Apollo Pharmacy Prescription",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001021": {
            "amount": 149.0,
            "date": get_date_str(42),
            "description": "Entertainment · Disney+ Hotstar Subscription",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001022": {
            "amount": 4500.0,
            "date": get_date_str(45),
            "description": "Shopping · Myntra Festive Apparel",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001023": {
            "amount": 850.0,
            "date": get_date_str(48),
            "description": "Dining · Starbucks Coffee MG Road",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001024": {
            "amount": 3500.0,
            "date": get_date_str(52),
            "description": "ATM · Cash Withdrawal SBI ATM",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001025": {
            "amount": 25000.0,
            "date": get_date_str(55),
            "description": "Bonus · TechCorp Quarterly Performance Bonus",
            "type": "credit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001026": {
            "amount": 180.0,
            "date": get_date_str(58),
            "description": "UPI · Uber Auto Ride Koramangala",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001027": {
            "amount": 45000.0,
            "date": get_date_str(67),
            "description": "NEFT · Monthly Salary Credit TechCorp",
            "type": "credit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001028": {
            "amount": 12000.0,
            "date": get_date_str(68),
            "description": "EMI · Personal Loan Auto Debit",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001029": {
            "amount": 1150.0,
            "date": get_date_str(70),
            "description": "Utility · BESCOM Electricity Bill",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001030": {
            "amount": 5000.0,
            "date": get_date_str(75),
            "description": "Investment · Nippon India MF Monthly SIP",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001031": {
            "amount": 2800.0,
            "date": get_date_str(80),
            "description": "Retail · DMart Supermarket Monthly Groceries",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001032": {
            "amount": 420.0,
            "date": get_date_str(82),
            "description": "Travel · Metro Card Smart Card Recharge",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001033": {
            "amount": 45000.0,
            "date": get_date_str(97),
            "description": "NEFT · Monthly Salary Credit TechCorp",
            "type": "credit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001034": {
            "amount": 250.0,
            "date": get_date_str(100),
            "description": "Fee · Annual Debit Card Maintenance Fee",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001035": {
            "amount": 45.0,
            "date": get_date_str(100),
            "description": "Tax · 18% GST on Annual Card Fee",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001036": {
            "amount": 1000.0,
            "date": get_date_str(1),
            "description": "UPI · Blinkit Urgent Milk & Bread",
            "type": "debit",
            "status": "pending",
            "currency": "INR"
        },
        "TXN-001037": {
            "amount": 2000.0,
            "date": get_date_str(2),
            "description": "ATM · Cash Withdrawal Attempt Kotak ATM",
            "type": "debit",
            "status": "failed",
            "currency": "INR"
        },
        "TXN-001038": {
            "amount": 550.0,
            "date": get_date_str(6),
            "description": "UPI · Zomato Dinner Order",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001039": {
            "amount": 75.0,
            "date": get_date_str(13),
            "description": "UPI · Tender Coconut Stall",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-001040": {
            "amount": 3400.0,
            "date": get_date_str(26),
            "description": "Fuel · Shell Petrol Pump Varthur",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        }
    }

    db["C001"] = {
        "pin": "1234",
        "profile": {
            "name": "Aarav Sharma",
            "scenario": "salary account (standard retail)",
            "bank_name": "Indic State Bank",
            "branch": "Indiranagar, Bengaluru",
            "account_number": "XXXX 1001",
            "kyc_status": "verified",
            "customer_segment": "Retail Salaried",
            "phone": "+91 98450 12345",
            "email": "aarav.sharma@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 45000,
                "masked_account": "XXXX 1001",
                "currency": "INR",
                "status": "active"
            },
            "kcc": {
                "balance": 25000,
                "masked_account": "XXXX 1001",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "crop": {
                "due_date": "2026-11-30",
                "outstanding": 125000
            },
            "personal": {
                "due_date": "2026-12-15",
                "outstanding": 50000
            }
        },
        "claims": {
            "CLM-771": {
                "status": "in_process",
                "amount": 22000
            },
            "CLM-402": {
                "status": "approved",
                "amount": 15000
            }
        },
        "transactions": c001_txns
    }

    # ==========================================
    # C002: Rajesh Patel - Farmer / Rural KCC
    # ==========================================
    c002_txns = {}
    c002_raw = [
        (get_date_str(1), 2000.0, "credit", "completed", "DBT · PM-KISAN Samman Nidhi 18th Installment"),
        (get_date_str(2), 450.0, "debit", "completed", "Agri · IFFCO Urea & DAP Fertilizer Purchase"),
        (get_date_str(4), 1800.0, "debit", "completed", "Agri · Hybrid Cotton Seeds Krishi Kendra"),
        (get_date_str(6), 2500.0, "debit", "completed", "Fuel · Tractor Diesel Bharat Petroleum"),
        (get_date_str(8), 500.0, "debit", "completed", "Micro-ATM · Cash Withdrawal Rural CSP"),
        (get_date_str(10), 18500.0, "credit", "completed", "Mandi · Onion Harvest Sale APMC Nashik"),
        (get_date_str(12), 1200.0, "debit", "completed", "Utility · MSEDCL Agriculture Feeder Power"),
        (get_date_str(15), 3200.0, "debit", "completed", "Agri · Drip Irrigation Pipe Fittings"),
        (get_date_str(18), 850.0, "debit", "completed", "Agri · Pesticide Spray Bayer CropScience"),
        (get_date_str(20), 4000.0, "debit", "completed", "ATM · Cash Withdrawal Gramin Bank ATM"),
        (get_date_str(22), 12000.0, "credit", "completed", "Mandi · Soybean Produce Procurement Credit"),
        (get_date_str(25), 1500.0, "debit", "completed", "Household · Village Kirana Store Groceries"),
        (get_date_str(28), 299.0, "debit", "completed", "Telecom · Airtel 84-Day Prepaid Plan"),
        (get_date_str(32), 8500.0, "debit", "completed", "Loan · Tractor Loan Monthly EMI Auto-Debit"),
        (get_date_str(35), 650.0, "debit", "completed", "Health · Primary Health Center Medicals"),
        (get_date_str(40), 2500.0, "debit", "completed", "Agri · Farm Labor Wages Payout via UPI"),
        (get_date_str(45), 18000.0, "credit", "completed", "Claim · PMFBY Crop Insurance Claim Settled"),
        (get_date_str(50), 3000.0, "debit", "completed", "Fuel · Diesel Can for Water Pump"),
        (get_date_str(55), 1000.0, "debit", "completed", "Micro-ATM · Cash Withdrawal for Weekly Haat"),
        (get_date_str(60), 2000.0, "credit", "completed", "DBT · PM-KISAN Samman Nidhi 17th Installment"),
        (get_date_str(3), 1500.0, "debit", "pending", "Agri · Organic Pesticide Spray (Clearing)"),
        (get_date_str(7), 5000.0, "debit", "failed", "ATM · Cash Withdrawal Technical Failure")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c002_raw, start=2001):
        c002_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c002_txns, 2, "rural", count=20)

    db["C002"] = {
        "pin": "2345",
        "profile": {
            "name": "Rajesh Patel",
            "scenario": "farmer / rural KCC borrower",
            "bank_name": "Indic Gramin Bank",
            "branch": "Dindori Rural, Nashik",
            "account_number": "XXXX 2002",
            "kyc_status": "verified",
            "customer_segment": "Kisan Agriculturist",
            "phone": "+91 97654 32101",
            "email": "rajesh.patel.kisan@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 12400,
                "masked_account": "XXXX 2002",
                "currency": "INR",
                "status": "active"
            },
            "kcc": {
                "balance": 18500,
                "masked_account": "XXXX 2002",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "crop": {
                "due_date": "2026-12-31",
                "outstanding": 85000
            },
            "home": {
                "due_date": "2026-11-20",
                "outstanding": 450000
            }
        },
        "claims": {
            "CLM-930": {
                "status": "in_process",
                "amount": 35000
            },
            "CLM-931": {
                "status": "approved",
                "amount": 18000
            }
        },
        "transactions": c002_txns
    }

    # ==========================================
    # C003: Vikram Malhotra - Corporate Trader / Overdraft User
    # ==========================================
    c003_txns = {}
    c003_raw = [
        (get_date_str(1), 125000.0, "credit", "completed", "Salary · Executive Monthly Director Remuneration"),
        (get_date_str(2), 15000.0, "debit", "completed", "Dining · Wasabi by Morimoto Taj Mahal Palace"),
        (get_date_str(3), 42000.0, "debit", "completed", "Travel · Business Class Mumbai-Delhi Air India"),
        (get_date_str(5), 8500.0, "debit", "completed", "Retail · Brooks Brothers Palladium Mall"),
        (get_date_str(7), 50000.0, "debit", "completed", "Investment · HDFC Top 100 Large Cap Fund"),
        (get_date_str(9), 250000.0, "credit", "completed", "Dividend · Reliance Industries Annual Dividend"),
        (get_date_str(11), 180000.0, "debit", "completed", "Loan · Luxury Villa Home Loan Monthly EMI"),
        (get_date_str(13), 6500.0, "debit", "completed", "Utility · Tata Power South Mumbai Electricity"),
        (get_date_str(16), 12500.0, "debit", "completed", "Club · Bombay Gymkhana Quarterly Membership"),
        (get_date_str(18), 3500.0, "debit", "completed", "Fuel · Shell V-Power Petrol Bandra"),
        (get_date_str(21), 95000.0, "debit", "completed", "Credit Card · American Express Platinum Auto Pay"),
        (get_date_str(24), 45000.0, "credit", "completed", "Consulting · Strategic Advisory Honorarium"),
        (get_date_str(27), 1850.0, "debit", "completed", "FASTag · Bandra-Worli Sea Link Monthly Pass"),
        (get_date_str(2), 25000.0, "debit", "pending", "Transfer · Vendor Invoice Payment Processing"),
        (get_date_str(4), 100000.0, "debit", "failed", "RTGS · Overseas Wire Transfer Limit Exceeded")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c003_raw, start=3001):
        c003_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c003_txns, 3, "hni", count=25)

    db["C003"] = {
        "pin": "3456",
        "profile": {
            "name": "Vikram Malhotra",
            "scenario": "overdraft account / corporate executive",
            "bank_name": "Indic Apex Bank",
            "branch": "Nariman Point, Mumbai",
            "account_number": "XXXX 3003",
            "kyc_status": "verified",
            "customer_segment": "Corporate Elite",
            "phone": "+91 98200 98765",
            "email": "vikram.malhotra@corp.example.com"
        },
        "accounts": {
            "savings": {
                "balance": -15000,
                "masked_account": "XXXX 3003",
                "currency": "INR",
                "status": "active"
            },
            "kcc": {
                "balance": 0,
                "masked_account": "XXXX 3003",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "crop": {
                "due_date": "2026-11-15",
                "outstanding": 75000
            },
            "personal": {
                "due_date": "2026-12-01",
                "outstanding": 250000
            }
        },
        "claims": {
            "CLM-301": {
                "status": "settled",
                "amount": 50000
            }
        },
        "transactions": c003_txns
    }

    # ==========================================
    # C004: Sneha Sen - Tech Lead / Duplicate Debit Dispute
    # ==========================================
    c004_txns = {
        "TXN-4001": {
            "amount": 4299.0,
            "date": "2026-10-23",
            "description": "POS · Electronics Store Duplicate Charge",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        },
        "TXN-4002": {
            "amount": 4299.0,
            "date": "2026-10-23",
            "description": "POS · Electronics Store Original Charge",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        }
    }
    c004_raw = [
        (get_date_str(1), 185000.0, "credit", "completed", "Salary · Google India Monthly Salary"),
        (get_date_str(2), 650.0, "debit", "completed", "UPI · Third Wave Coffee Gachibowli"),
        (get_date_str(3), 1200.0, "debit", "completed", "UPI · Blinkit Organic Vegetables & Milk"),
        (get_date_str(5), 4500.0, "debit", "completed", "Wellness · Cult.fit Annual Gym Pass"),
        (get_date_str(7), 899.0, "debit", "completed", "Telecom · ACT Fibernet High-Speed Fiber"),
        (get_date_str(9), 18500.0, "debit", "completed", "Loan · Personal Loan Auto Debit"),
        (get_date_str(12), 3400.0, "debit", "completed", "Retail · Nykaa Cosmetics Online Order"),
        (get_date_str(14), 2800.0, "debit", "completed", "Fuel · Bharat Petroleum Madhapur"),
        (get_date_str(17), 50000.0, "debit", "completed", "Investment · Parag Parikh Flexi Cap SIP"),
        (get_date_str(4), 1500.0, "debit", "pending", "E-Commerce · Amazon India Prime Day Order"),
        (get_date_str(6), 3000.0, "debit", "failed", "ATM · Cash Dispenser Gate Jammed")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c004_raw, start=4003):
        c004_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c004_txns, 4, "salaried", count=25)

    db["C004"] = {
        "pin": "4567",
        "profile": {
            "name": "Sneha Sen",
            "scenario": "high balance tech professional (duplicate debit)",
            "bank_name": "Indic Cyber Bank",
            "branch": "HITEC City, Hyderabad",
            "account_number": "XXXX 4004",
            "kyc_status": "verified",
            "customer_segment": "Tech Professional",
            "phone": "+91 99887 65432",
            "email": "sneha.sen@tech.example.com"
        },
        "accounts": {
            "savings": {
                "balance": 284500.75,
                "masked_account": "XXXX 4004",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-10",
                "outstanding": 120000
            }
        },
        "claims": {
            "CLM-1004": {
                "status": "in_process",
                "amount": 4299
            }
        },
        "transactions": c004_txns
    }

    # ==========================================
    # C005: Manoj Kumar Verma - Dormant / Inactive Account
    # ==========================================
    c005_txns = {}
    c005_raw = [
        (get_date_str(210), 150.0, "debit", "completed", "Fee · Annual Debit Card Maintenance Fee"),
        (get_date_str(210), 27.0, "debit", "completed", "Tax · GST on Annual Maintenance Charge"),
        (get_date_str(240), 18.50, "credit", "completed", "Interest · Savings Bank Quarterly Interest Credit"),
        (get_date_str(300), 500.0, "debit", "completed", "ATM · Cash Withdrawal Patna City Branch"),
        (get_date_str(330), 19.20, "credit", "completed", "Interest · Savings Bank Quarterly Interest Credit"),
        (get_date_str(420), 1000.0, "credit", "completed", "Deposit · Branch Cash Deposit Counter"),
        (get_date_str(450), 150.0, "debit", "completed", "Fee · SMS Alert Quarterly Service Charge"),
        (get_date_str(500), 17.80, "credit", "completed", "Interest · Savings Bank Quarterly Interest Credit")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c005_raw, start=5001):
        c005_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }

    db["C005"] = {
        "pin": "5678",
        "profile": {
            "name": "Manoj Kumar Verma",
            "scenario": "dormant account (inactive > 6 months)",
            "bank_name": "Indic Rashtriya Bank",
            "branch": "Kankarbagh, Patna",
            "account_number": "XXXX 5005",
            "kyc_status": "re_kyc_due",
            "customer_segment": "Retail Inactive",
            "phone": "+91 94310 11223",
            "email": "manoj.verma.patna@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 1250.00,
                "masked_account": "XXXX 5005",
                "currency": "INR",
                "status": "dormant"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-15",
                "outstanding": 15000
            }
        },
        "claims": {
            "CLM-1005": {
                "status": "rejected",
                "amount": 5000
            }
        },
        "transactions": c005_txns
    }

    # ==========================================
    # C006: Anita Deshmukh - Senior Citizen Pensioner
    # ==========================================
    c006_txns = {}
    c006_raw = [
        (get_date_str(1), 34500.0, "credit", "completed", "Pension · Central Govt Defence Pension Credit"),
        (get_date_str(2), 2450.0, "debit", "completed", "Health · Sanjeevani Medicals Chronic Medicines"),
        (get_date_str(4), 850.0, "debit", "completed", "Utility · Pune Mahanagar Gas Cylinder Refill"),
        (get_date_str(7), 1450.0, "debit", "completed", "Utility · MSEDCL Pune Residential Power"),
        (get_date_str(10), 5000.0, "debit", "completed", "ATM · Senior Citizen Counter Cash Withdrawal"),
        (get_date_str(15), 4500.0, "credit", "completed", "Interest · Senior Citizen Special FD Interest"),
        (get_date_str(18), 350.0, "debit", "completed", "UPI · Morning Milk & Dairy Products"),
        (get_date_str(22), 1200.0, "debit", "completed", "Health · Blood Diagnostic Pathology Tests"),
        (get_date_str(25), 650.0, "debit", "completed", "Telecom · BSNL Landline & Broadband Bill"),
        (get_date_str(3), 1500.0, "debit", "pending", "Utility · Water Supply Board Annual Cess"),
        (get_date_str(8), 2000.0, "debit", "failed", "ATM · Timeout Bank of India ATM")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c006_raw, start=6001):
        c006_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c006_txns, 6, "salaried", count=25)

    db["C006"] = {
        "pin": "6789",
        "profile": {
            "name": "Anita Deshmukh",
            "scenario": "senior citizen pensioner (FD interest / Form 15H)",
            "bank_name": "Indic Pensioners Bank",
            "branch": "Deccan Gymkhana, Pune",
            "account_number": "XXXX 6006",
            "kyc_status": "verified",
            "customer_segment": "Senior Citizen",
            "phone": "+91 98220 54321",
            "email": "anita.deshmukh.pension@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 68450.00,
                "masked_account": "XXXX 6006",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-10-01",
                "outstanding": 0
            }
        },
        "claims": {
            "CLM-1006": {
                "status": "approved",
                "amount": 12000
            }
        },
        "transactions": c006_txns
    }

    # ==========================================
    # C007: Rohan Iyer - Overseas Student / Education Loan
    # ==========================================
    c007_txns = {}
    c007_raw = [
        (get_date_str(1), 85.0, "debit", "completed", "UPI · College Canteen Dosa & Filter Coffee"),
        (get_date_str(2), 350.0, "debit", "completed", "Study · Photocopy & Engineering Project Print"),
        (get_date_str(3), 1500.0, "credit", "completed", "Transfer · Pocket Money from Parents UPI"),
        (get_date_str(5), 499.0, "debit", "completed", "Books · Amazon Academic Textbook Pearson"),
        (get_date_str(7), 180.0, "debit", "completed", "Travel · Chennai Metro Smart Card Top-up"),
        (get_date_str(10), 125000.0, "debit", "completed", "Tuition · Semester Examination & Lab Fees"),
        (get_date_str(12), 299.0, "debit", "completed", "Telecom · Jio Student Unlimited 5G Plan"),
        (get_date_str(15), 1800.0, "debit", "completed", "Test · GRE Practice Test Portal Voucher"),
        (get_date_str(4), 250.0, "debit", "pending", "Books · Scientific Calculator Order (Processing)"),
        (get_date_str(9), 1000.0, "debit", "failed", "UPI · Hosteller Night Delivery UPI Timeout")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c007_raw, start=7001):
        c007_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c007_txns, 7, "salaried", count=25)

    db["C007"] = {
        "pin": "7890",
        "profile": {
            "name": "Rohan Iyer",
            "scenario": "student account / education loan (moratorium)",
            "bank_name": "Indic Scholars Bank",
            "branch": "Mylapore, Chennai",
            "account_number": "XXXX 7007",
            "kyc_status": "verified",
            "customer_segment": "Student",
            "phone": "+91 98401 23456",
            "email": "rohan.iyer.edu@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 5420.50,
                "masked_account": "XXXX 7007",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2027-03-31",
                "outstanding": 1450000
            }
        },
        "claims": {
            "CLM-1007": {
                "status": "in_process",
                "amount": 10000
            }
        },
        "transactions": c007_txns
    }

    # ==========================================
    # C008: Sunita Choudhary - Kirana Merchant / QR Soundbox
    # ==========================================
    c008_txns = {}
    c008_raw = [
        (get_date_str(1), 120.0, "credit", "completed", "QR Soundbox · Customer UPI Rice & Dal"),
        (get_date_str(1), 45.0, "credit", "completed", "QR Soundbox · Customer UPI Spices & Sugar"),
        (get_date_str(1), 250.0, "credit", "completed", "QR Soundbox · Customer UPI Fortune Oil Pouch"),
        (get_date_str(2), 15000.0, "debit", "completed", "Wholesale · FMCG Distributor Grain Delivery"),
        (get_date_str(2), 350.0, "credit", "completed", "QR Soundbox · Customer UPI Daily Provisions"),
        (get_date_str(3), 85.0, "credit", "completed", "QR Soundbox · Customer UPI Soap & Shampoo"),
        (get_date_str(4), 1850.0, "debit", "completed", "Utility · JVVNL Commercial Electricity Bill"),
        (get_date_str(5), 4500.0, "debit", "completed", "Tax · GST Quarter 2 Composition Tax Payment"),
        (get_date_str(1), 500.0, "credit", "pending", "QR Soundbox · Batch Settlement In-Flight"),
        (get_date_str(3), 1000.0, "debit", "failed", "UPI · Distributor Payment Server Timeout")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c008_raw, start=8001):
        c008_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c008_txns, 8, "merchant", count=25)

    db["C008"] = {
        "pin": "8901",
        "profile": {
            "name": "Sunita Choudhary",
            "scenario": "merchant / QR soundbox daily settlements",
            "bank_name": "Indic Vyapar Bank",
            "branch": "Johari Bazaar, Jaipur",
            "account_number": "XXXX 8008",
            "kyc_status": "verified",
            "customer_segment": "Merchant SME",
            "phone": "+91 94140 98765",
            "email": "sunita.kirana.jaipur@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 92150.00,
                "masked_account": "XXXX 8008",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-10",
                "outstanding": 180000
            }
        },
        "claims": {
            "CLM-1008": {
                "status": "approved",
                "amount": 8500
            }
        },
        "transactions": c008_txns
    }

    # ==========================================
    # C009: Kavya Raman - Zero-Transaction Fresh Account
    # ==========================================
    db["C009"] = {
        "pin": "9012",
        "profile": {
            "name": "Kavya Raman",
            "scenario": "zero-transaction / freshly opened account",
            "bank_name": "Indic Digital Bank",
            "branch": "Koramangala, Bengaluru",
            "account_number": "XXXX 9009",
            "kyc_status": "verified",
            "customer_segment": "Digital Onboarding",
            "phone": "+91 99001 12345",
            "email": "kavya.raman.new@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 1000.00,
                "masked_account": "XXXX 9009",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-31",
                "outstanding": 0
            }
        },
        "claims": {},
        "transactions": {}
    }

    # ==========================================
    # C010: Harpreet Singh - Transport Fleet / Overdue Loan
    # ==========================================
    c010_txns = {}
    c010_raw = [
        (get_date_str(1), 18500.0, "debit", "completed", "Fuel · Indian Oil Fleet Diesel GT Road"),
        (get_date_str(2), 2450.0, "debit", "completed", "FASTag · Panipat Toll Plaza Multi-Axle"),
        (get_date_str(3), 45000.0, "credit", "completed", "Freight · Delhi-Ludhiana Logistics Invoice Paid"),
        (get_date_str(5), 14850.0, "debit", "failed", "Loan · Commercial Vehicle Loan Auto Debit Failed"),
        (get_date_str(5), 590.0, "debit", "completed", "Penalty · ECS Return Inward Mandate Reject Fee"),
        (get_date_str(6), 106.20, "debit", "completed", "Tax · 18% GST on Mandate Reject Penalty"),
        (get_date_str(8), 12500.0, "debit", "completed", "Repair · Truck Tyre Replacement MRF Dealer"),
        (get_date_str(11), 3200.0, "debit", "completed", "FASTag · Shambhu Toll Plaza Punjab Border"),
        (get_date_str(2), 5000.0, "debit", "pending", "FASTag · Monthly Tag Wallet Auto-Topup"),
        (get_date_str(7), 15000.0, "debit", "failed", "ATM · Cash Withdrawal Daily Limit Exceeded")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c010_raw, start=10101):
        c010_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c010_txns, 10, "salaried", count=25)

    db["C010"] = {
        "pin": "1010",
        "profile": {
            "name": "Harpreet Singh",
            "scenario": "overdue loan / commercial fleet owner",
            "bank_name": "Indic Commercial Bank",
            "branch": "GT Road, Ludhiana",
            "account_number": "XXXX 1010",
            "kyc_status": "verified",
            "customer_segment": "Commercial Fleet",
            "phone": "+91 98140 12345",
            "email": "harpreet.trucking@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 14200.00,
                "masked_account": "XXXX 1010",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-10-05",  # Overdue!
                "outstanding": 148500
            }
        },
        "claims": {
            "CLM-1010": {
                "status": "under_review",
                "amount": 45000
            }
        },
        "transactions": c010_txns
    }

    # ==========================================
    # C011: Farhan Akhtar - Fully Paid Off Loan Customer
    # ==========================================
    c011_txns = {}
    c011_raw = [
        (get_date_str(31), 45000.0, "debit", "completed", "Loan · Final Loan Preclosure Settlement Lump Sum"),
        (get_date_str(30), 250.0, "debit", "completed", "Fee · Loan NOC & Deed Release Processing Fee"),
        (get_date_str(1), 58000.0, "credit", "completed", "Salary · Architecture Studio Senior Designer"),
        (get_date_str(3), 1250.0, "debit", "completed", "UPI · Hazratganj Tunday Kababi Dinner"),
        (get_date_str(5), 2400.0, "debit", "completed", "Retail · Fabindia Lucknow Chikan Kurta"),
        (get_date_str(8), 1800.0, "debit", "completed", "Utility · UPPCL Lucknow Electricity Bill"),
        (get_date_str(2), 1200.0, "debit", "pending", "Retail · Online Art Supplies Palette Order")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c011_raw, start=1101):
        c011_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c011_txns, 11, "salaried", count=25)

    db["C011"] = {
        "pin": "1111",
        "profile": {
            "name": "Farhan Akhtar",
            "scenario": "closed loan (zero outstanding / NOC issued)",
            "bank_name": "Indic Heritage Bank",
            "branch": "Hazratganj, Lucknow",
            "account_number": "XXXX 1111",
            "kyc_status": "verified",
            "customer_segment": "Retail Debt-Free",
            "phone": "+91 94150 54321",
            "email": "farhan.akhtar.lko@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 78900.00,
                "masked_account": "XXXX 1111",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-09-30",
                "outstanding": 0  # Fully closed!
            }
        },
        "claims": {
            "CLM-1011": {
                "status": "settled",
                "amount": 15000
            }
        },
        "transactions": c011_txns
    }

    # ==========================================
    # C012: Deepak Joshi - High Dispute / Failed Transactions
    # ==========================================
    c012_txns = {
        "TXN-1201": {
            "amount": 5000.0,
            "date": get_date_str(2),
            "description": "ATM · Cash Dispenser Failed - Money Debited",
            "type": "debit",
            "status": "failed",
            "currency": "INR"
        },
        "TXN-1202": {
            "amount": 2400.0,
            "date": get_date_str(3),
            "description": "UPI · Merchant QR Timed Out - Money Deducted",
            "type": "debit",
            "status": "failed",
            "currency": "INR"
        },
        "TXN-1203": {
            "amount": 14999.0,
            "date": get_date_str(5),
            "description": "POS · Unauthorized Card Swipe Unknown Terminal",
            "type": "debit",
            "status": "completed",
            "currency": "INR"
        }
    }
    c012_raw = [
        (get_date_str(1), 52000.0, "credit", "completed", "Salary · Tourism Dept State Govt Salary"),
        (get_date_str(4), 1800.0, "debit", "completed", "Fuel · Bharat Petroleum Rajpur Road"),
        (get_date_str(6), 499.0, "debit", "failed", "Telecom · DTH Recharge Transaction Failed"),
        (get_date_str(7), 1250.0, "debit", "completed", "Utility · Uttarakhand Jal Sansthan Water Bill"),
        (get_date_str(1), 1000.0, "credit", "reversed", "Auto-Reversal · Failed ATM Transaction Reversal")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c012_raw, start=1204):
        c012_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c012_txns, 12, "salaried", count=25)

    db["C012"] = {
        "pin": "1212",
        "profile": {
            "name": "Deepak Joshi",
            "scenario": "failed transactions & dispute tracking",
            "bank_name": "Indic Valley Bank",
            "branch": "Rajpur Road, Dehradun",
            "account_number": "XXXX 1212",
            "kyc_status": "verified",
            "customer_segment": "Retail Disputed",
            "phone": "+91 97600 12345",
            "email": "deepak.joshi.dun@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 33400.00,
                "masked_account": "XXXX 1212",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-25",
                "outstanding": 60000
            }
        },
        "claims": {
            "CLM-1012": {
                "status": "escalated",
                "amount": 14999
            }
        },
        "transactions": c012_txns
    }

    # ==========================================
    # C013: Abhishek Banerjee - Metro Salaried Executive
    # ==========================================
    c013_txns = {}
    c013_raw = [
        (get_date_str(1), 115000.0, "credit", "completed", "Salary · ITC Limited Senior Consultant"),
        (get_date_str(2), 4500.0, "debit", "completed", "Dining · Peter Cat Park Street Chelo Kebab"),
        (get_date_str(4), 1800.0, "debit", "completed", "Utility · CESC Kolkata Electricity Bill"),
        (get_date_str(6), 25000.0, "debit", "completed", "Rent · South Kolkata Apartment Rent Transfer"),
        (get_date_str(2), 2200.0, "debit", "pending", "Retail · Amazon India Book Order")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c013_raw, start=1301):
        c013_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c013_txns, 13, "salaried", count=25)

    db["C013"] = {
        "pin": "1313",
        "profile": {
            "name": "Abhishek Banerjee",
            "scenario": "salary account (metro corporate)",
            "bank_name": "Indic City Bank",
            "branch": "Park Street, Kolkata",
            "account_number": "XXXX 1313",
            "kyc_status": "verified",
            "customer_segment": "Corporate Salaried",
            "phone": "+91 98300 98765",
            "email": "abhishek.banerjee.kol@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 165000.00,
                "masked_account": "XXXX 1313",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-28",
                "outstanding": 95000
            }
        },
        "claims": {
            "CLM-1013": {
                "status": "approved",
                "amount": 6500
            }
        },
        "transactions": c013_txns
    }

    # ==========================================
    # C014: Meera Iyer - Zero Balance Account Edge Case
    # ==========================================
    c014_txns = {}
    c014_raw = [
        (get_date_str(3), 5000.0, "debit", "completed", "Withdrawal · Branch Cash Withdrawal - Depleted Balance"),
        (get_date_str(1), 500.0, "debit", "failed", "UPI · Payment Declined - Insufficient Balance (Zero Balance)"),
        (get_date_str(2), 1000.0, "debit", "failed", "ATM · Cash Withdrawal Declined Insufficient Balance"),
        (get_date_str(10), 5000.0, "credit", "completed", "Credit · Transfer from Relative for Medical"),
        (get_date_str(15), 450.0, "debit", "completed", "Utility · KSEB Electricity Bill Ernakulam")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c014_raw, start=1401):
        c014_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c014_txns, 14, "rural", count=20)

    db["C014"] = {
        "pin": "1414",
        "profile": {
            "name": "Meera Iyer",
            "scenario": "zero balance edge case",
            "bank_name": "Indic Malabar Bank",
            "branch": "MG Road, Ernakulam",
            "account_number": "XXXX 1414",
            "kyc_status": "verified",
            "customer_segment": "Zero Balance",
            "phone": "+91 98470 12345",
            "email": "meera.iyer.zero@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 0.0,  # Strict zero for test assertion!
                "masked_account": "XXXX 1414",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-10",
                "outstanding": 30000
            }
        },
        "claims": {
            "CLM-1014": {
                "status": "closed",
                "amount": 0
            }
        },
        "transactions": c014_txns
    }

    # ==========================================
    # C015: Arjun Patel - Negative Overdraft Edge Case
    # ==========================================
    c015_txns = {}
    c015_raw = [
        (get_date_str(1), 12500.0, "debit", "completed", "Cheque · Clearing Cheque Debit Exceeding Balance"),
        (get_date_str(2), 250.0, "debit", "completed", "Interest · Overdraft Limit Utilization Interest"),
        (get_date_str(3), 45.0, "debit", "completed", "Fee · Over-Limit Urgent SMS Notification Charge"),
        (get_date_str(8), 5000.0, "credit", "completed", "Deposit · UPI Repayment into Overdraft Account"),
        (get_date_str(2), 1500.0, "debit", "failed", "ATM · Cash Withdrawal Blocked - Overdraft Limit Reached")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c015_raw, start=1501):
        c015_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c015_txns, 15, "salaried", count=25)

    db["C015"] = {
        "pin": "1515",
        "profile": {
            "name": "Arjun Patel",
            "scenario": "overdraft / negative balance edge case",
            "bank_name": "Indic Mercantile Bank",
            "branch": "Ashram Road, Ahmedabad",
            "account_number": "XXXX 1515",
            "kyc_status": "verified",
            "customer_segment": "Overdraft Facility",
            "phone": "+91 98250 54321",
            "email": "arjun.patel.od@example.com"
        },
        "accounts": {
            "savings": {
                "balance": -4850.75,  # Strict negative for test assertion!
                "masked_account": "XXXX 1515",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-18",
                "outstanding": 110000
            }
        },
        "claims": {
            "CLM-1015": {
                "status": "pending",
                "amount": 10000
            }
        },
        "transactions": c015_txns
    }

    # ==========================================
    # C016: Cyrus Poonawalla - Multi-Crore HNW Edge Case
    # ==========================================
    c016_txns = {}
    c016_raw = [
        (get_date_str(1), 850000.0, "credit", "completed", "Dividend · TCS Quarterly Dividend Direct Credit"),
        (get_date_str(2), 1250000.0, "debit", "completed", "RTGS · Private Equity Fund Capital Call Tranche 4"),
        (get_date_str(4), 45000.0, "debit", "completed", "Dining · Zodiac Grill Taj Mahal Palace Private Dining"),
        (get_date_str(6), 250000.0, "debit", "completed", "Aviation · Private Aircraft Fuel & Ground Handling"),
        (get_date_str(10), 5000000.0, "credit", "completed", "Treasury · Commercial Paper Maturity Repayment"),
        (get_date_str(1), 500000.0, "debit", "pending", "RTGS · Heritage Property Restoration Advance")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c016_raw, start=1601):
        c016_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c016_txns, 16, "hni", count=25)

    db["C016"] = {
        "pin": "1616",
        "profile": {
            "name": "Cyrus Poonawalla",
            "scenario": "high balance / multi-crore private wealth",
            "bank_name": "Indic Imperial Wealth Bank",
            "branch": "Altamount Road, Mumbai",
            "account_number": "XXXX 1616",
            "kyc_status": "verified",
            "customer_segment": "Ultra HNI Private Wealth",
            "phone": "+91 98201 00001",
            "email": "cyrus.poonawalla@private.example.com"
        },
        "accounts": {
            "savings": {
                "balance": 24500000.0,  # 2.45 Crores (> 1 Crore)!
                "masked_account": "XXXX 1616",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-31",
                "outstanding": 0
            }
        },
        "claims": {},
        "transactions": c016_txns
    }

    # ==========================================
    # C017: Priya Nair - Frozen Account / Cybercrime Lien Hold
    # ==========================================
    c017_txns = {}
    c017_raw = [
        (get_date_str(1), 2500.0, "debit", "failed", "Debit Blocked · Account Frozen by Cyber Crime Cell Lien"),
        (get_date_str(2), 1200.0, "debit", "failed", "UPI Declined · Lien Hold of Rs 50,000 on Account"),
        (get_date_str(5), 18500.0, "credit", "completed", "Credit · Inward Pension Credit Allowed by Bank"),
        (get_date_str(15), 450.0, "debit", "completed", "Utility · KSEB Electricity Payment Prior to Freeze"),
        (get_date_str(3), 500.0, "debit", "failed", "ATM · Transaction Denied - Account Under Lien")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c017_raw, start=1701):
        c017_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c017_txns, 17, "salaried", count=20)

    db["C017"] = {
        "pin": "1717",
        "profile": {
            "name": "Priya Nair",
            "scenario": "frozen account (cybercrime lien hold)",
            "bank_name": "Indic Coastal Bank",
            "branch": "Statue Junction, Thiruvananthapuram",
            "account_number": "XXXX 1717",
            "kyc_status": "under_investigation",
            "customer_segment": "Legal Lien Marked",
            "phone": "+91 94470 54321",
            "email": "priya.nair.tvm@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 54200.00,
                "masked_account": "XXXX 1717",
                "currency": "INR",
                "status": "frozen"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-05",
                "outstanding": 40000
            }
        },
        "claims": {
            "CLM-1017": {
                "status": "under_investigation",
                "amount": 25000
            }
        },
        "transactions": c017_txns
    }

    # ==========================================
    # C018: Ravi Kumar - Multiple In-Flight Pending Payments
    # ==========================================
    c018_txns = {}
    c018_raw = [
        (get_date_str(1), 12500.0, "debit", "pending", "NEFT · Vendor Material Supply (Awaiting Batch Clear)"),
        (get_date_str(1), 2450.0, "debit", "pending", "Utility · BSES Rajdhani Electricity (Processing)"),
        (get_date_str(2), 4999.0, "credit", "pending", "E-Commerce · Amazon India Return Refund in Clearing"),
        (get_date_str(2), 1500.0, "debit", "pending", "IMPS · Peer-to-Peer Transfer (NPCI In-Flight)"),
        (get_date_str(3), 45000.0, "credit", "completed", "Salary · Delhi Govt Education Directorate Salary"),
        (get_date_str(5), 1800.0, "debit", "completed", "Fuel · Indian Oil CP Connaught Place"),
        (get_date_str(8), 8500.0, "debit", "completed", "Loan · Personal Loan Auto Debit")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c018_raw, start=1801):
        c018_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c018_txns, 18, "salaried", count=25)

    db["C018"] = {
        "pin": "1818",
        "profile": {
            "name": "Ravi Kumar",
            "scenario": "pending payments & in-flight clearing",
            "bank_name": "Indic Capital Bank",
            "branch": "Connaught Place, New Delhi",
            "account_number": "XXXX 1818",
            "kyc_status": "verified",
            "customer_segment": "Retail Salaried",
            "phone": "+91 98110 98765",
            "email": "ravi.kumar.delhi@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 48150.00,
                "masked_account": "XXXX 1818",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-22",
                "outstanding": 80000
            }
        },
        "claims": {
            "CLM-1018": {
                "status": "in_review",
                "amount": 12000
            }
        },
        "transactions": c018_txns
    }

    # ==========================================
    # C019: Lakshmi Narayanan - Joint Account / Family Household
    # ==========================================
    c019_txns = {}
    c019_raw = [
        (get_date_str(1), 18500.0, "debit", "completed", "School · Kendriya Vidyalaya Term Tuition Fee"),
        (get_date_str(2), 3450.0, "debit", "completed", "Debit Card 2 (Spouse) · Nilgiris Supermarket Trichy"),
        (get_date_str(3), 850.0, "debit", "completed", "Utility · Indane LPG Gas Cylinder Booking"),
        (get_date_str(5), 1200.0, "debit", "completed", "Utility · TANGEDCO Residential Power Trichy"),
        (get_date_str(8), 65000.0, "credit", "completed", "Salary · BHEL Senior Engineer Monthly Salary"),
        (get_date_str(2), 1500.0, "debit", "pending", "Utility · Municipal Corporation Water Supply Cess")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c019_raw, start=1901):
        c019_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c019_txns, 19, "salaried", count=25)

    db["C019"] = {
        "pin": "1919",
        "profile": {
            "name": "Lakshmi Narayanan",
            "scenario": "joint account / household family budget",
            "bank_name": "Indic Family Bank",
            "branch": "Thillai Nagar, Tiruchirappalli",
            "account_number": "XXXX 1919",
            "kyc_status": "verified",
            "customer_segment": "Joint Account",
            "phone": "+91 94431 12345",
            "email": "lakshmi.narayanan.trichy@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 72300.00,
                "masked_account": "XXXX 1919",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-15",
                "outstanding": 55000
            }
        },
        "claims": {
            "CLM-1019": {
                "status": "approved",
                "amount": 4500
            }
        },
        "transactions": c019_txns
    }

    # ==========================================
    # C020: Tariq Mansoor - NRI / Foreign Inward Remittance
    # ==========================================
    c020_txns = {}
    c020_raw = [
        (get_date_str(1), 250000.0, "credit", "completed", "Remittance · Swift Inward TT from UAE Exchange Dubai"),
        (get_date_str(2), 1450.0, "debit", "completed", "Forex · Foreign Exchange Markup Fee on Overseas POS"),
        (get_date_str(4), 1850.0, "debit", "completed", "Dining · Grand Hyatt Bolgatty Kochi"),
        (get_date_str(7), 45000.0, "debit", "completed", "Transfer · Sent to Parents Savings Account Kerala"),
        (get_date_str(10), 12000.0, "credit", "completed", "Interest · NRE Tax-Free Term Deposit Interest"),
        (get_date_str(2), 25000.0, "debit", "pending", "Transfer · Outward Wire Transfer Processing")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c020_raw, start=2001):
        c020_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c020_txns, 20, "hni", count=25)

    db["C020"] = {
        "pin": "2020",
        "profile": {
            "name": "Tariq Mansoor",
            "scenario": "NRI account / foreign inward remittances",
            "bank_name": "Indic NRI Overseas Bank",
            "branch": "Marine Drive, Ernakulam",
            "account_number": "XXXX 2020",
            "kyc_status": "verified",
            "customer_segment": "Non-Resident Indian (NRE)",
            "phone": "+971 50 1234567",
            "email": "tariq.mansoor.dxb@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 380000.00,
                "masked_account": "XXXX 2020",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-20",
                "outstanding": 200000
            }
        },
        "claims": {
            "CLM-1020": {
                "status": "cleared",
                "amount": 18000
            }
        },
        "transactions": c020_txns
    }

    # ==========================================
    # C021: Bhavna Shah - Fixed Deposit & RD Specialist
    # ==========================================
    c021_txns = {}
    c021_raw = [
        (get_date_str(1), 10000.0, "debit", "completed", "Deposit · Recurring Deposit (RD) Monthly Standing Instruction"),
        (get_date_str(3), 6750.0, "credit", "completed", "Interest · Cumulative 3-Year Fixed Deposit Quarterly Interest"),
        (get_date_str(5), 18500.0, "debit", "completed", "Gold · Tanishq Jewellers Dhanteras Token Gold Coin"),
        (get_date_str(8), 2400.0, "debit", "completed", "Utility · Torrent Power Surat Commercial Power"),
        (get_date_str(2), 10000.0, "debit", "pending", "Deposit · New Term Deposit Certificate Issuance")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c021_raw, start=2101):
        c021_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c021_txns, 21, "salaried", count=25)

    db["C021"] = {
        "pin": "2121",
        "profile": {
            "name": "Bhavna Shah",
            "scenario": "fixed deposits & recurring deposit (RD)",
            "bank_name": "Indic Samruddhi Bank",
            "branch": "Ring Road, Surat",
            "account_number": "XXXX 2121",
            "kyc_status": "verified",
            "customer_segment": "Term Deposit Investor",
            "phone": "+91 98251 12345",
            "email": "bhavna.shah.surat@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 95600.00,
                "masked_account": "XXXX 2121",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-12",
                "outstanding": 35000
            }
        },
        "claims": {
            "CLM-1021": {
                "status": "closed",
                "amount": 7200
            }
        },
        "transactions": c021_txns
    }

    # ==========================================
    # C022: Arvind Swamy - Credit Card Heavy Spender / Traveler
    # ==========================================
    c022_txns = {}
    c022_raw = [
        (get_date_str(1), 38500.0, "debit", "completed", "Credit Card · Infinite Metal Card Auto-Debit Bill Settlement"),
        (get_date_str(2), 14500.0, "debit", "completed", "Travel · Vistara Premium Economy Delhi-Bengaluru"),
        (get_date_str(3), 850.0, "debit", "completed", "Lounge · Encalm Lounge Terminal 3 Access Fee"),
        (get_date_str(5), 18500.0, "debit", "completed", "Hotel · JW Marriott Bengaluru Weekend Stay"),
        (get_date_str(2), 2400.0, "debit", "pending", "Dining · Olive Beach Gourmet Dinner (Pending Clear)")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c022_raw, start=2201):
        c022_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c022_txns, 22, "hni", count=25)

    db["C022"] = {
        "pin": "2222",
        "profile": {
            "name": "Arvind Swamy",
            "scenario": "credit card heavy spender & frequent traveler",
            "bank_name": "Indic Platinum Bank",
            "branch": "MG Road, Bengaluru",
            "account_number": "XXXX 2222",
            "kyc_status": "verified",
            "customer_segment": "Platinum Cardholder",
            "phone": "+91 98451 98765",
            "email": "arvind.swamy.blr@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 142800.00,
                "masked_account": "XXXX 2222",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-11-25",
                "outstanding": 70000
            }
        },
        "claims": {
            "CLM-1022": {
                "status": "approved",
                "amount": 15000
            }
        },
        "transactions": c022_txns
    }

    # ==========================================
    # C023: Swati Mishra - Freshly Onboarded Customer
    # ==========================================
    c023_txns = {}
    c023_raw = [
        (get_date_str(4), 10000.0, "credit", "completed", "Deposit · Initial Account Funding Initial Deposit"),
        (get_date_str(3), 100.0, "credit", "completed", "Promotion · Digital Account Opening Welcome Cashback"),
        (get_date_str(2), 50.0, "debit", "completed", "UPI · Test Penny Payment to Friend Mobile"),
        (get_date_str(1), 299.0, "debit", "completed", "Telecom · Jio Prepaid Monthly Mobile Recharge"),
        (get_date_str(1), 250.0, "debit", "pending", "E-Commerce · First Welcome Kit Dispatch Processing")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c023_raw, start=2301):
        c023_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }

    db["C023"] = {
        "pin": "2323",
        "profile": {
            "name": "Swati Mishra",
            "scenario": "freshly onboarded (welcome kit in transit)",
            "bank_name": "Indic Pratham Bank",
            "branch": "MP Nagar, Bhopal",
            "account_number": "XXXX 2323",
            "kyc_status": "verified",
            "customer_segment": "New Customer",
            "phone": "+91 94250 12345",
            "email": "swati.mishra.bhopal@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 10500.00,
                "masked_account": "XXXX 2323",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "personal": {
                "due_date": "2026-12-31",
                "outstanding": 0
            }
        },
        "claims": {},
        "transactions": c023_txns
    }

    # ==========================================
    # C024: Suresh Chandran - Dairy Farmer / Milk Procurement
    # ==========================================
    c024_txns = {}
    c024_raw = [
        (get_date_str(1), 480.0, "credit", "completed", "Cooperative · Morning Milk Procurement Aavin Society"),
        (get_date_str(1), 420.0, "credit", "completed", "Cooperative · Evening Milk Procurement Aavin Society"),
        (get_date_str(2), 490.0, "credit", "completed", "Cooperative · Morning Milk Procurement Aavin Society"),
        (get_date_str(3), 1850.0, "debit", "completed", "Agri · Cattle Fodder & Mineral Feed Supplement"),
        (get_date_str(4), 450.0, "credit", "completed", "Cooperative · Morning Milk Procurement Aavin Society"),
        (get_date_str(5), 2500.0, "debit", "completed", "Fuel · Rural Milk Transport Vehicle Diesel"),
        (get_date_str(7), 850.0, "debit", "completed", "Veterinary · Dairy Cow Health Tonic & Vaccination"),
        (get_date_str(10), 4500.0, "debit", "completed", "Loan · Animal Husbandry Allied KCC Loan Instalment"),
        (get_date_str(1), 500.0, "credit", "pending", "Cooperative · Bi-Weekly Fat Incentive Settlement")
    ]
    for idx, (dt, amt, kind, st, desc) in enumerate(c024_raw, start=2401):
        c024_txns[f"TXN-{idx}"] = {
            "amount": amt, "date": dt, "description": desc,
            "type": kind, "status": st, "currency": "INR"
        }
    add_historical_transactions(c024_txns, 24, "rural", count=25)

    db["C024"] = {
        "pin": "2424",
        "profile": {
            "name": "Suresh Chandran",
            "scenario": "dairy farmer / animal husbandry allied KCC",
            "bank_name": "Indic Kisan Pragati Bank",
            "branch": "Attur, Salem",
            "account_number": "XXXX 2424",
            "kyc_status": "verified",
            "customer_segment": "Dairy Agriculturist",
            "phone": "+91 94432 98765",
            "email": "suresh.dairy.salem@example.com"
        },
        "accounts": {
            "savings": {
                "balance": 28750.00,
                "masked_account": "XXXX 2424",
                "currency": "INR",
                "status": "active"
            },
            "kcc": {
                "balance": 22000.00,
                "masked_account": "XXXX 2424",
                "currency": "INR",
                "status": "active"
            }
        },
        "loans": {
            "crop": {
                "due_date": "2026-12-20",
                "outstanding": 65000
            }
        },
        "claims": {
            "CLM-1024": {
                "status": "in_process",
                "amount": 20000
            }
        },
        "transactions": c024_txns
    }

    # Save to disk
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated expanded database at {DB_PATH}")
    print(f"Total customers: {len(db)}")
    total_txns = sum(len(c["transactions"]) for c in db.values())
    print(f"Total transactions across all personas: {total_txns}")

if __name__ == "__main__":
    build_database()
