"""Seed script — the only fake part of Atlas.

Builds a coherent investment firm at realistic scale — twelve divisions,
~85 people, a 27-process responsibility graph — plus a back catalogue of
requests so that every dashboard, inbox and report is alive on first launch.
The demo conditions at the bottom of this file (who is out of office, which
processes are orphaned, who is a single point of failure) are deliberate:
they are what the pitch walks through.
"""

from __future__ import annotations

import random
from datetime import timedelta

from sqlalchemy.orm import Session

from . import config
from .clock import now
from .db import create_all, drop_all, session_scope, set_setting
from .models import (
    Department,
    Event,
    Message,
    Person,
    Process,
    Request,
    Responsibility,
)

# Each team carries the vocabulary people actually use for its problems, so
# "who do I contact to get my laptop fixed" can reach IT even though no request
# type covers a broken laptop. This is the firm's own words, not a taxonomy: it
# is the thing that has to be edited when a team picks up new ground.
DEPARTMENTS: list[tuple[str, str]] = [
    (
        "Executive Office",
        "board, board meeting, board pack, investment committee agenda, executive, "
        "ceo, chief executive, strategy, town hall, all hands, offsite agenda, "
        "chief of staff, executive assistant",
    ),
    (
        "Private Equity",
        "deal, transaction, data room, diligence, due diligence, target, buyout, "
        "portfolio company, investment, investment committee, pipeline, mandate, "
        "teaser, deal model, fund, co-invest, term sheet, spa, lbo, "
        "nda with a counterparty, exit, add-on acquisition",
    ),
    (
        "Public Markets",
        "equities, public equities, trading, trade, execution, broker, order, "
        "position, rebalance, portfolio rebalance, hedge, bloomberg, market data, "
        "terminal, research note, sell side, earnings, ticker, fixed income, bonds",
    ),
    (
        "Real Assets & Infrastructure",
        "real estate, property, building acquisition, asset management, tenant, "
        "lease, rent review, development, infrastructure, project finance, "
        "site visit to a property, planning permission, capex on a property",
    ),
    (
        "Investor Relations",
        "investor, lp, limited partner, fundraising, capital raise, roadshow, "
        "investor report, quarterly letter, capital account, subscription, "
        "redemption, investor portal, press, media, journalist, communications, "
        "announcement, marketing materials, factsheet",
    ),
    (
        "Finance & Accounting",
        "invoice, payment, pay, supplier, vendor payment, expense, expenses, "
        "reimburse, reimbursement, receipt, budget, cost, spend, purchase order, "
        "accounts, accounts payable, payroll, salary, pay slip, bonus, tax, "
        "audit, nav, valuation, treasury, bank, bank details, wire, transfer, "
        "forecast, month end, ledger, billing, credit card, corporate card, "
        "claim, expense claim, out of pocket, capital call, distribution",
    ),
    (
        "Legal",
        "contract, agreement, nda, non disclosure, legal, lawyer, counsel, review a "
        "contract, terms, clause, dispute, litigation, insurance, power of "
        "attorney, signature, execute a document, company secretary, entity",
    ),
    (
        "Compliance",
        "policy, compliance, regulation, regulatory, fca, sec, kyc, aml, anti "
        "money laundering, sanctions, screening check, gdpr, data protection, "
        "privacy, personal data, breach of policy, conflict of interest, gift "
        "register, personal account dealing, whistleblowing, marketing approval",
    ),
    (
        "Risk",
        "risk, risk assessment, risk register, operational risk, market risk, "
        "credit risk, incident, near miss, limit breach, exposure, stress test, "
        "scenario, business continuity, disaster recovery",
    ),
    (
        "Technology",
        "laptop, computer, macbook, desktop, monitor, screen, keyboard, "
        "mouse, docking station, headset, webcam, hardware, crashed, frozen, "
        "blue screen, won't turn on, wifi, wi-fi, internet, network, vpn, "
        "remote access, printer, printing, "
        "scanner, software, application, install, licence, license, email, "
        "outlook, mailbox, calendar, teams, zoom, phone, mobile, password, "
        "login, log in, locked out, mfa, two factor, permissions, shared "
        "drive, sharepoint, onedrive, backup, virus, phishing, it support, "
        "helpdesk, service desk, tech, technology, data warehouse, snowflake",
    ),
    (
        "People & Culture",
        "holiday, annual leave, time off, sick, sickness, absence, maternity, "
        "paternity, hr, people team, contract of employment, onboarding, joiner, "
        "new starter, leaver, offboarding, benefits, pension, private medical, "
        "recruitment, hiring, hire, new hire, headcount, interview, reference, "
        "training, course, performance review, appraisal, grievance",
    ),
    (
        "Operations & Facilities",
        "office, facilities, building, desk, seating, meeting room, room booking, "
        "parking, security pass, badge, access card, stationery, supplies, "
        "chair, furniture, lighting, heating, air conditioning, "
        "catering, kitchen, cleaning, courier, travel, flight, hotel, taxi, "
        "visa, itinerary, reception, visitor, post, health and safety, "
        "first aid, fire drill",
    ),
]

# (name, title, department, manager name or None)
PEOPLE: list[tuple[str, str, str | None, str | None]] = [
    # --- Executive Office ---
    ("Khalid Al-Rayes", "Chief Executive Officer", "Executive Office", None),
    ("Victoria Lang", "Chief of Staff", "Executive Office", "Khalid Al-Rayes"),
    ("Priya Nair", "Executive Assistant to the CEO", "Executive Office", "Khalid Al-Rayes"),
    # --- Private Equity ---
    ("Alexander Rothwell", "Chief Investment Officer", "Private Equity", "Khalid Al-Rayes"),
    ("Faisal Al-Otaibi", "Managing Director, Private Equity", "Private Equity", "Alexander Rothwell"),
    ("Sarah Whitfield", "Investment Director", "Private Equity", "Faisal Al-Otaibi"),
    ("Omar Haddad", "Principal", "Private Equity", "Faisal Al-Otaibi"),
    ("Layla Mansour", "Senior Associate", "Private Equity", "Sarah Whitfield"),
    ("James Okonkwo", "Associate", "Private Equity", "Sarah Whitfield"),
    ("Noura Al-Sabah", "Associate", "Private Equity", "Omar Haddad"),
    ("Daniyal Sheikh", "Senior Associate", "Private Equity", "Omar Haddad"),
    ("Lucas Meyer", "Associate", "Private Equity", "Sarah Whitfield"),
    ("Marco Bianchi", "Investment Analyst", "Private Equity", "Omar Haddad"),
    ("Yousef Darwish", "Investment Analyst", "Private Equity", "Layla Mansour"),
    ("Sofia Marchetti", "Investment Analyst", "Private Equity", "Layla Mansour"),
    ("Emily Watts", "Investment Analyst", "Private Equity", "Daniyal Sheikh"),
    # --- Public Markets ---
    ("Helen Zhao", "Head of Public Markets", "Public Markets", "Alexander Rothwell"),
    ("Dmitri Volkov", "Senior Portfolio Manager", "Public Markets", "Helen Zhao"),
    ("Aisha Al-Amin", "Portfolio Manager", "Public Markets", "Helen Zhao"),
    ("Jonathan Pierce", "Head of Trading", "Public Markets", "Helen Zhao"),
    ("Mei-Ling Chen", "Trader", "Public Markets", "Jonathan Pierce"),
    ("Isabelle Fontaine", "Senior Research Analyst", "Public Markets", "Dmitri Volkov"),
    ("Adam Kowalski", "Research Analyst", "Public Markets", "Dmitri Volkov"),
    ("Zara Hussain", "Research Analyst", "Public Markets", "Aisha Al-Amin"),
    # --- Real Assets & Infrastructure ---
    ("Marcus Thorne", "Head of Real Assets", "Real Assets & Infrastructure", "Alexander Rothwell"),
    ("Valentina Cruz", "Director, Real Estate", "Real Assets & Infrastructure", "Marcus Thorne"),
    ("Samir Chatterjee", "Director, Infrastructure", "Real Assets & Infrastructure", "Marcus Thorne"),
    ("Hana Yoshida", "Senior Associate", "Real Assets & Infrastructure", "Valentina Cruz"),
    ("Piotr Nowak", "Associate", "Real Assets & Infrastructure", "Samir Chatterjee"),
    ("Leila Boutros", "Analyst", "Real Assets & Infrastructure", "Valentina Cruz"),
    ("George Kamau", "Analyst", "Real Assets & Infrastructure", "Samir Chatterjee"),
    # --- Investor Relations ---
    ("Charlotte Beaumont", "Head of Investor Relations", "Investor Relations", "Khalid Al-Rayes"),
    ("Ryan O'Sullivan", "Investor Relations Director", "Investor Relations", "Charlotte Beaumont"),
    ("Ingrid Larsen", "Investor Reporting Manager", "Investor Relations", "Charlotte Beaumont"),
    ("Tunde Adebayo", "Investor Relations Associate", "Investor Relations", "Ryan O'Sullivan"),
    ("Camille Laurent", "Communications Manager", "Investor Relations", "Charlotte Beaumont"),
    # --- Finance & Accounting ---
    ("Amira Haddadin", "Chief Financial Officer", "Finance & Accounting", "Khalid Al-Rayes"),
    ("Daniel Reyes", "Finance Director", "Finance & Accounting", "Amira Haddadin"),
    ("Huda Al-Najjar", "Financial Controller", "Finance & Accounting", "Amira Haddadin"),
    ("Lena Fischer", "Head of Treasury", "Finance & Accounting", "Amira Haddadin"),
    ("Peter Lindqvist", "Senior Accountant", "Finance & Accounting", "Huda Al-Najjar"),
    ("Rania Khoury", "Accounts Payable Lead", "Finance & Accounting", "Daniel Reyes"),
    ("Tomas Ferreira", "Treasury Analyst", "Finance & Accounting", "Lena Fischer"),
    ("Mariam Al-Balushi", "Fund Accountant", "Finance & Accounting", "Huda Al-Najjar"),
    ("Jacob Stein", "Fund Accountant", "Finance & Accounting", "Huda Al-Najjar"),
    ("Karim El-Masri", "Payroll Specialist", "Finance & Accounting", "Daniel Reyes"),
    ("Amal Qasimi", "Accounts Assistant", "Finance & Accounting", "Rania Khoury"),
    ("Nathan Brooks", "Financial Analyst", "Finance & Accounting", "Daniel Reyes"),
    # --- Legal ---
    ("Nadia Suleiman", "General Counsel", "Legal", "Khalid Al-Rayes"),
    ("Robert Ashby", "Deputy General Counsel", "Legal", "Nadia Suleiman"),
    ("Eleanor Voss", "Senior Legal Counsel", "Legal", "Robert Ashby"),
    ("Grace Mwangi", "Legal Counsel", "Legal", "Robert Ashby"),
    ("Hassan Al-Farsi", "Paralegal", "Legal", "Eleanor Voss"),
    ("Miriam Goldberg", "Company Secretary", "Legal", "Nadia Suleiman"),
    # --- Compliance ---
    ("Zainab Al-Hashimi", "Head of Compliance", "Compliance", "Nadia Suleiman"),
    ("Tariq Benali", "Compliance Officer, KYC", "Compliance", "Zainab Al-Hashimi"),
    ("Rebecca Ojo", "Senior Compliance Officer", "Compliance", "Zainab Al-Hashimi"),
    ("Stefan Bauer", "Compliance Analyst", "Compliance", "Rebecca Ojo"),
    # --- Risk ---
    ("Margaret Osei", "Chief Risk Officer", "Risk", "Khalid Al-Rayes"),
    ("Viktor Hansen", "Head of Operational Risk", "Risk", "Margaret Osei"),
    ("Anjali Rao", "Risk Analyst", "Risk", "Viktor Hansen"),
    ("Felix Moreau", "Market Risk Analyst", "Risk", "Margaret Osei"),
    # --- Technology ---
    ("Vikram Chandra", "Head of Technology", "Technology", "Khalid Al-Rayes"),
    ("Elena Petrova", "Infrastructure Lead", "Technology", "Vikram Chandra"),
    ("Ahmed Zaki", "Systems Administrator", "Technology", "Elena Petrova"),
    ("Chloe Dubois", "Security Engineer", "Technology", "Vikram Chandra"),
    ("Sam Whitaker", "Cybersecurity Analyst", "Technology", "Chloe Dubois"),
    ("Bilal Rahman", "IT Support Lead", "Technology", "Vikram Chandra"),
    ("Ivan Kovacs", "Application Support Analyst", "Technology", "Bilal Rahman"),
    ("Andre Silva", "IT Support Engineer", "Technology", "Bilal Rahman"),
    ("Fatima Al-Zahrani", "Data Engineer", "Technology", "Elena Petrova"),
    ("Keiko Tanaka", "Data Analyst", "Technology", "Elena Petrova"),
    # --- People & Culture ---
    ("Salma Bouzid", "Head of People & Culture", "People & Culture", "Claire Donovan"),
    ("Dina Al-Kaabi", "HR Business Partner", "People & Culture", "Salma Bouzid"),
    ("Lucia Romano", "Talent Acquisition Lead", "People & Culture", "Salma Bouzid"),
    ("David Mensah", "Learning & Development Manager", "People & Culture", "Salma Bouzid"),
    ("Ffion Davies", "HR Coordinator", "People & Culture", "Dina Al-Kaabi"),
    # --- Operations & Facilities ---
    ("Claire Donovan", "Chief Operating Officer", "Operations & Facilities", "Khalid Al-Rayes"),
    ("Michael Trent", "Operations Manager", "Operations & Facilities", "Claire Donovan"),
    ("Anna Sorenson", "Office Manager", "Operations & Facilities", "Michael Trent"),
    ("Youssef Karim", "Procurement Lead", "Operations & Facilities", "Michael Trent"),
    ("Mona Farid", "Operations Analyst", "Operations & Facilities", "Michael Trent"),
    ("Hamza Al-Dosari", "Travel & Facilities Coordinator", "Operations & Facilities", "Anna Sorenson"),
    ("Beatriz Costa", "Receptionist", "Operations & Facilities", "Anna Sorenson"),
    ("Jack Thompson", "Facilities Technician", "Operations & Facilities", "Anna Sorenson"),
]

# (name, category, description, keywords)
PROCESSES: list[tuple[str, str, str, str]] = [
    (
        "Data Room Access",
        "Deal Support",
        "Grant a colleague or counterparty access to a project virtual data room, "
        "including folder-level permissions and NDA verification.",
        "data room, dataroom, virtual data room, vdr, deal documents, project access, "
        "folder access, diligence documents, deal folder, project falcon, "
        "data, data access, access to the data, data permissions, deal data",
    ),
    (
        "Invoice Approval",
        "Finance",
        "Approve a supplier invoice for payment once goods or services are confirmed received.",
        "invoice, approve invoice, supplier payment, pay invoice, billing, accounts payable, "
        "invoice sign off, payment run",
    ),
    (
        "IT Access Provisioning",
        "IT",
        "Provision system access, licences or shared drive permissions for a colleague, "
        "including password resets and locked accounts.",
        "access, permissions, system access, provisioning, licence, license, vpn access, "
        "shared drive, new account, joiner setup, password, reset password, locked out, "
        "mfa, login issue, cannot log in, account locked",
    ),
    (
        "Travel Approval",
        "Operations",
        "Approve business travel and book flights, hotels and ground transport.",
        "travel, flight, flights, trip, hotel, business travel, travel request, itinerary, "
        "travel booking, visa",
    ),
    (
        "Expense Reimbursement",
        "Finance",
        "Reimburse out-of-pocket business expenses against submitted receipts.",
        "expense, expenses, reimbursement, reimburse, claim, receipts, out of pocket, "
        "expense report, mileage",
    ),
    (
        "Valuation Sign-off",
        "Finance",
        "Quarterly fair-value sign-off for portfolio holdings feeding the NAV.",
        "valuation, nav, fair value, portfolio valuation, sign off, mark, quarterly valuation, "
        "pricing, net asset value",
    ),
    (
        "Purchase Order Approval",
        "Procurement",
        "Raise and approve a purchase order before committing firm spend.",
        "purchase order, po, raise po, procurement request, spend approval, commit spend, "
        "buy, order form",
    ),
    (
        "Policy Exception Approval",
        "Compliance",
        "Approve a documented deviation from an internal policy, with rationale and expiry.",
        "policy exception, waiver, exemption, deviation, override, policy breach, "
        "one off approval, dispensation",
    ),
    (
        "IT Hardware Support",
        "IT",
        "Fix or replace a broken laptop, monitor, phone or other device, "
        "including slow machines, battery and charger problems.",
        "laptop, computer, hardware, broken laptop, fix laptop, laptop fixed, repair, "
        "device, screen, monitor, keyboard, mouse, printer, phone, headset, docking, "
        "battery, charger, slow computer, not working, blue screen, "
        "replacement device, new laptop, it support",
    ),
    (
        "NDA Execution",
        "Legal",
        "Prepare, negotiate and execute a non-disclosure agreement with a "
        "counterparty, adviser or vendor.",
        "nda, non disclosure, confidentiality agreement, execute nda, sign nda, "
        "counterparty nda, mutual nda, confidentiality undertaking",
    ),
    (
        "Contract Review",
        "Legal",
        "Legal review of a contract, engagement letter or side letter before "
        "signature, with redlines back to the counterparty.",
        "contract review, review a contract, agreement review, redline, markup, "
        "engagement letter, side letter, supplier contract, terms and conditions, "
        "legal review, contract sign off",
    ),
    (
        "KYC / AML Screening",
        "Compliance",
        "Know-your-customer and anti-money-laundering screening for a new "
        "investor, counterparty or vendor, including sanctions checks.",
        "kyc, know your customer, aml, anti money laundering, sanctions check, "
        "screening, investor onboarding check, counterparty screening, kyc refresh, "
        "pep check, source of funds",
    ),
    (
        "Personal Account Dealing Approval",
        "Compliance",
        "Pre-clearance for a personal trade in a listed security, as the PA "
        "dealing policy requires.",
        "personal account dealing, pa dealing, personal trade, pre clearance, "
        "preclearance, personal investment, share dealing, trade approval for "
        "my own account",
    ),
    (
        "Gifts & Entertainment Approval",
        "Compliance",
        "Declare and approve a gift or hospitality given or received, and record "
        "it on the gift register.",
        "gift, gifts, entertainment, hospitality, declare a gift, gift register, "
        "client entertainment, tickets from a broker, corporate hospitality",
    ),
    (
        "Capital Call Processing",
        "Fund Operations",
        "Issue a capital call notice to limited partners and reconcile the "
        "drawdown against commitments.",
        "capital call, drawdown, call notice, lp funding, commitment drawdown, "
        "call capital, fund the deal",
    ),
    (
        "Distribution Processing",
        "Fund Operations",
        "Process a distribution of proceeds to limited partners through the "
        "waterfall, including carry calculations.",
        "distribution, distribute proceeds, lp distribution, waterfall, carry, "
        "return capital, proceeds to investors",
    ),
    (
        "Payment Release",
        "Treasury",
        "Release a wire from a firm or fund bank account once the payment has "
        "been verified and dual-authorised.",
        "wire, wire transfer, payment release, release payment, release a wire, "
        "bank transfer, remittance, settle payment, transfer funds, urgent payment",
    ),
    (
        "Vendor Onboarding",
        "Procurement",
        "Set up a new supplier: due diligence, bank detail verification and "
        "entry in the vendor master.",
        "vendor onboarding, new vendor, new supplier, supplier onboarding, vendor "
        "setup, supplier setup, vendor due diligence, add a supplier, vendor master",
    ),
    (
        "New Joiner Onboarding",
        "People",
        "Everything a new starter needs for day one: contract, equipment order, "
        "system access bundle and induction plan.",
        "onboarding, new joiner, new starter, joiner, first day, induction, "
        "starter setup, welcome pack, joiner bundle",
    ),
    (
        "Leaver Offboarding",
        "People",
        "Off-board a leaver: revoke access, recover equipment, settle final pay "
        "and run the exit interview.",
        "leaver, offboarding, resignation, exit, departure, revoke access for a "
        "leaver, final pay, exit interview, return equipment",
    ),
    (
        "Annual Leave Approval",
        "People",
        "Approve a request for annual leave and record it on the absence calendar.",
        "annual leave, holiday, holiday request, time off, vacation, leave "
        "request, book leave, pto, days off",
    ),
    (
        "Recruitment Requisition",
        "People",
        "Open a role: approve the headcount, the level and the budget, then "
        "brief the talent team.",
        "recruitment, requisition, open a role, hire, hiring, new hire, headcount "
        "approval, job posting, vacancy, backfill",
    ),
    (
        "Software Purchase Request",
        "IT",
        "Buy or renew a software product or SaaS subscription, including the "
        "security review and licence assignment.",
        "software purchase, buy software, new tool, saas, subscription renewal, "
        "software licence request, app request, purchase a licence, renew software",
    ),
    (
        "Building Access Pass",
        "Operations",
        "Issue, replace or extend a building security pass for staff, "
        "contractors and visitors.",
        "security pass, badge, access card, building access, door pass, key fob, "
        "office pass, visitor pass, replacement badge, lost pass",
    ),
    (
        "Investor Report Request",
        "Investor Relations",
        "Produce or resend an investor report, capital account statement or "
        "factsheet for a limited partner.",
        "investor report, quarterly letter, lp report, capital account statement, "
        "investor statement, factsheet, investor portal access, resend a report",
    ),
    (
        "Risk Incident Report",
        "Risk",
        "Log an operational incident, error or near miss on the risk register "
        "and track remediation.",
        "risk incident, incident report, operational incident, error report, "
        "near miss, limit breach, breach of limit, log an incident, remediation",
    ),
    (
        "Market Data Access",
        "Public Markets",
        "Grant or amend a market data entitlement — a Bloomberg terminal, "
        "Refinitiv or FactSet seat, or an index licence.",
        "bloomberg, market data, terminal, refinitiv, factset, data terminal, "
        "market data licence, index licence, terminal seat, quote access",
    ),
]

# process name -> {role: [person names]}
RESPONSIBILITIES: dict[str, dict[str, list[str]]] = {
    "Data Room Access": {
        "owner": ["Layla Mansour"],
        "approver": ["Faisal Al-Otaibi"],
        "delegate": ["James Okonkwo"],
        "backup": ["Omar Haddad"],
    },
    "Invoice Approval": {
        "owner": ["Rania Khoury"],
        "approver": ["Huda Al-Najjar"],
        "delegate": ["Karim El-Masri"],
        "backup": ["Tomas Ferreira"],
    },
    "IT Hardware Support": {
        "owner": ["Bilal Rahman"],
        "approver": ["Vikram Chandra"],
        "delegate": ["Ivan Kovacs"],
        "backup": ["Ahmed Zaki"],
    },
    "IT Access Provisioning": {
        "owner": ["Bilal Rahman"],
        "approver": ["Vikram Chandra"],
        "delegate": ["Ivan Kovacs"],
        "backup": ["Ahmed Zaki"],
    },
    "Travel Approval": {
        "owner": ["Hamza Al-Dosari"],
        "approver": ["Michael Trent", "Huda Al-Najjar"],
        "delegate": ["Anna Sorenson"],
    },
    "Expense Reimbursement": {
        "owner": ["Peter Lindqvist"],
        "approver": ["Huda Al-Najjar"],
        "delegate": ["Mariam Al-Balushi"],
    },
    # Deliberate single point of failure: owner is Huda, no delegate, no backup.
    "Valuation Sign-off": {
        "owner": ["Huda Al-Najjar"],
        "approver": ["Amira Haddadin"],
    },
    "NDA Execution": {
        "owner": ["Grace Mwangi"],
        "approver": ["Robert Ashby"],
        "delegate": ["Hassan Al-Farsi"],
    },
    # Owner Eleanor Voss is on leave at seed time — a second live reroute.
    "Contract Review": {
        "owner": ["Eleanor Voss"],
        "approver": ["Robert Ashby"],
        "delegate": ["Grace Mwangi"],
        "backup": ["Nadia Suleiman"],
    },
    "KYC / AML Screening": {
        "owner": ["Tariq Benali"],
        "approver": ["Zainab Al-Hashimi"],
        "delegate": ["Rebecca Ojo"],
        "backup": ["Stefan Bauer"],
    },
    "Personal Account Dealing Approval": {
        "owner": ["Rebecca Ojo"],
        "approver": ["Zainab Al-Hashimi"],
        "delegate": ["Stefan Bauer"],
    },
    "Gifts & Entertainment Approval": {
        "owner": ["Stefan Bauer"],
        "approver": ["Zainab Al-Hashimi"],
    },
    "Capital Call Processing": {
        "owner": ["Mariam Al-Balushi"],
        "approver": ["Huda Al-Najjar"],
        "delegate": ["Jacob Stein"],
    },
    "Distribution Processing": {
        "owner": ["Jacob Stein"],
        "approver": ["Huda Al-Najjar"],
        "delegate": ["Mariam Al-Balushi"],
    },
    "Payment Release": {
        "owner": ["Tomas Ferreira"],
        "approver": ["Lena Fischer"],
        "backup": ["Daniel Reyes"],
    },
    "Vendor Onboarding": {
        "owner": ["Youssef Karim"],
        "approver": ["Michael Trent"],
        "delegate": ["Anna Sorenson"],
    },
    "New Joiner Onboarding": {
        "owner": ["Dina Al-Kaabi"],
        "approver": ["Salma Bouzid"],
        "delegate": ["Ffion Davies"],
    },
    "Leaver Offboarding": {
        "owner": ["Ffion Davies"],
        "approver": ["Salma Bouzid"],
        "delegate": ["Dina Al-Kaabi"],
    },
    "Annual Leave Approval": {
        "owner": ["Ffion Davies"],
        "approver": ["Salma Bouzid"],
        "delegate": ["Dina Al-Kaabi"],
    },
    "Recruitment Requisition": {
        "owner": ["Lucia Romano"],
        "approver": ["Salma Bouzid"],
        "backup": ["Claire Donovan"],
    },
    "Software Purchase Request": {
        "owner": ["Ivan Kovacs"],
        "approver": ["Vikram Chandra"],
        "delegate": ["Bilal Rahman"],
    },
    "Building Access Pass": {
        "owner": ["Beatriz Costa"],
        "approver": ["Anna Sorenson"],
        "delegate": ["Jack Thompson"],
    },
    "Investor Report Request": {
        "owner": ["Ingrid Larsen"],
        "approver": ["Charlotte Beaumont"],
        "delegate": ["Tunde Adebayo"],
    },
    "Risk Incident Report": {
        "owner": ["Viktor Hansen"],
        "approver": ["Margaret Osei"],
        "delegate": ["Anjali Rao"],
    },
    "Market Data Access": {
        "owner": ["Jonathan Pierce"],
        "approver": ["Helen Zhao"],
        "delegate": ["Mei-Ling Chen"],
    },
    # Orphans — deliberately nobody owns these.
    "Purchase Order Approval": {},
    "Policy Exception Approval": {},
}

# name -> days out of office from the simulated "now"
OOO_PEOPLE = {
    "Layla Mansour": 6,   # owner of Data Room Access — the headline demo
    "Eleanor Voss": 3,    # owner of Contract Review — reroutes to Grace Mwangi
    "Ahmed Zaki": 2,
    "Huda Al-Najjar": 4,  # single point of failure, no delegate configured
    "Dmitri Volkov": 3,
    "Ffion Davies": 5,    # leave/offboarding owner — reroutes to Dina Al-Kaabi
    "Jack Thompson": 1,
    "Tunde Adebayo": 2,
}


def _email(name: str) -> str:
    parts = [p for p in name.replace("-", " ").split() if p]
    first = parts[0].lower()
    last = parts[-1].lower()
    return f"{first}.{last}@atlas-capital.example"


def _add_event(
    session: Session,
    request: Request,
    type_: str,
    detail: str,
    created_at,
    actor: str = "system",
) -> None:
    session.add(
        Event(
            request_id=request.id,
            type=type_,
            detail=detail,
            actor=actor,
            created_at=created_at,
        )
    )


def _seed_request(
    session: Session,
    *,
    requester: Person,
    process: Process,
    assignee: Person,
    title: str,
    body: str,
    status: str,
    created_at,
    ack_after_hours: float | None = None,
    complete_after_hours: float | None = None,
    chase_count: int = 0,
    last_action_offset_hours: float | None = None,
) -> Request:
    request = Request(
        requester_id=requester.id,
        process_id=process.id,
        assignee_id=assignee.id,
        original_assignee_id=assignee.id,
        title=title,
        body=body,
        status=status,
        created_at=created_at,
        updated_at=created_at,
        last_action_at=created_at,
        chase_count=chase_count,
    )
    session.add(request)
    session.flush()

    _add_event(
        session,
        request,
        "created",
        f"{requester.name} raised a request under '{process.name}'.",
        created_at,
        actor=requester.name,
    )
    _add_event(
        session,
        request,
        "dispatch",
        f"Dispatched to {assignee.name} ({assignee.title}) as accountable owner.",
        created_at,
    )
    session.add(
        Message(
            request_id=request.id,
            sender_id=requester.id,
            recipient_id=assignee.id,
            type="dispatch",
            body=body,
            created_at=created_at,
            read=status != "pending",
        )
    )

    last_action = created_at
    if ack_after_hours is not None:
        acked = created_at + timedelta(hours=ack_after_hours)
        request.acknowledged_at = acked
        last_action = acked
        _add_event(
            session,
            request,
            "acknowledged",
            f"{assignee.name} acknowledged the request.",
            acked,
            actor=assignee.name,
        )
    if status == "in_progress":
        started = last_action + timedelta(hours=1.5)
        last_action = started
        _add_event(
            session,
            request,
            "status_update",
            f"{assignee.name} moved the request to In progress.",
            started,
            actor=assignee.name,
        )
    if complete_after_hours is not None:
        done = created_at + timedelta(hours=complete_after_hours)
        request.completed_at = done
        last_action = done
        _add_event(
            session,
            request,
            "completed",
            f"{assignee.name} completed the request.",
            done,
            actor=assignee.name,
        )
        session.add(
            Message(
                request_id=request.id,
                sender_id=assignee.id,
                recipient_id=requester.id,
                type="status_update",
                body=f"Your request '{title}' has been completed.",
                created_at=done,
                read=False,
            )
        )

    if last_action_offset_hours is not None:
        last_action = created_at + timedelta(hours=last_action_offset_hours)

    request.last_action_at = last_action
    request.updated_at = last_action
    return request


def seed(reset: bool = True) -> None:
    """Build a fresh database. Destroys any existing one when ``reset`` is set."""
    if reset:
        drop_all()
    create_all()

    rng = random.Random(20240517)

    with session_scope() as session:
        for key, value in config.DEFAULT_SETTINGS.items():
            set_setting(session, key, value)
        session.flush()

        base = now(session)

        departments: dict[str, Department] = {}
        for name, topics in DEPARTMENTS:
            dept = Department(name=name, topics=topics)
            session.add(dept)
            departments[name] = dept
        session.flush()

        people: dict[str, Person] = {}
        for name, title, dept_name, _manager in PEOPLE:
            person = Person(
                name=name,
                title=title,
                department_id=departments[dept_name].id if dept_name else None,
                email=_email(name),
                is_ooo=False,
            )
            session.add(person)
            people[name] = person
        session.flush()

        for name, _title, _dept, manager_name in PEOPLE:
            if manager_name:
                people[name].manager_id = people[manager_name].id

        for name, days in OOO_PEOPLE.items():
            people[name].is_ooo = True
            people[name].ooo_until = base + timedelta(days=days)

        processes: dict[str, Process] = {}
        for name, category, description, keywords in PROCESSES:
            proc = Process(
                name=name, category=category, description=description, keywords=keywords
            )
            session.add(proc)
            processes[name] = proc
        session.flush()

        for process_name, roles in RESPONSIBILITIES.items():
            for role, holders in roles.items():
                for holder in holders:
                    session.add(
                        Responsibility(
                            process_id=processes[process_name].id,
                            person_id=people[holder].id,
                            role=role,
                        )
                    )
        session.flush()

        _seed_history(session, rng, base, people, processes)

        session.add(
            Event(
                request_id=None,
                type="seed",
                detail=(
                    f"Database seeded: {len(people)} people, {len(departments)} departments, "
                    f"{len(processes)} processes."
                ),
                actor="system",
                created_at=base,
            )
        )
        set_setting(session, "seeded_at", base.isoformat())


def _seed_history(session, rng, base, people, processes) -> None:
    """Historical requests in mixed states, including overdue ones."""

    def hours_ago(h: float):
        return base - timedelta(hours=h)

    completed = [
        (
            "Expense Reimbursement", "Marco Bianchi", "Peter Lindqvist",
            "Reimbursement for Riyadh site visit",
            "Three nights and taxis for the Riyadh management meeting. Receipts attached.",
            410.0, 3.5, 29.0,
        ),
        (
            "IT Access Provisioning", "Sofia Marchetti", "Bilal Rahman",
            "Access to the portfolio monitoring drive",
            "I need read access to the portfolio monitoring shared drive for the quarterly pack.",
            330.0, 1.5, 8.0,
        ),
        (
            "IT Access Provisioning", "Anna Sorenson", "Bilal Rahman",
            "Locked out of the expenses portal",
            "MFA re-enrolment failed after my phone was replaced.",
            220.0, 0.5, 2.0,
        ),
        (
            "Invoice Approval", "Youssef Karim", "Rania Khoury",
            "Invoice 88412 — Meridian Advisory",
            "Q1 advisory retainer, goods receipted. Please approve for the Friday payment run.",
            190.0, 4.0, 26.0,
        ),
        (
            "Travel Approval", "Noura Al-Sabah", "Hamza Al-Dosari",
            "Travel to Manama for portfolio review",
            "Two nights, flying out Tuesday morning, returning Thursday evening.",
            150.0, 2.0, 12.0,
        ),
        (
            "Data Room Access", "Omar Haddad", "Layla Mansour",
            "Data room access for the Northgate diligence team",
            "Three analysts need read access to the Northgate folder before Monday.",
            120.0, 5.0, 41.0,
        ),
        (
            "KYC / AML Screening", "Ingrid Larsen", "Tariq Benali",
            "KYC for the new LP — Meridian Pension Trust",
            "Subscription docs are in; screening needed before we countersign.",
            96.0, 2.0, 30.0,
        ),
        (
            "NDA Execution", "Daniyal Sheikh", "Grace Mwangi",
            "NDA with Cobalt Ridge advisers",
            "Standard mutual NDA ahead of the first management meeting.",
            84.0, 1.0, 20.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h, ack_h, done_h in completed:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="completed",
            created_at=hours_ago(created_h),
            ack_after_hours=ack_h,
            complete_after_hours=done_h,
        )

    in_progress = [
        (
            "Travel Approval", "Michael Trent", "Hamza Al-Dosari",
            "Flights for the Halcyon site visit",
            "Two of us, out Wednesday back Friday. Fares are moving so worth booking early.",
            70.0, 5.0,
        ),
        (
            "Expense Reimbursement", "Anna Sorenson", "Peter Lindqvist",
            "Office supplies bought on a personal card",
            "The card on file was declined, so I paid for the print cartridges myself.",
            58.0, 9.0,
        ),
        (
            "IT Access Provisioning", "Khalid Al-Rayes", "Bilal Rahman",
            "Board portal access for the new committee member",
            "Please set up an account before the next investment committee.",
            44.0, 2.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h, ack_h in in_progress:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="in_progress",
            created_at=hours_ago(created_h),
            ack_after_hours=ack_h,
        )

    acknowledged = [
        (
            "Valuation Sign-off", "Amira Haddadin", "Huda Al-Najjar",
            "Q1 valuation sign-off — Falcon and Cedar holdings",
            "Both marks need controller sign-off before the NAV is struck on the 15th.",
            36.0, 4.0,
        ),
        (
            "Expense Reimbursement", "Yousef Darwish", "Peter Lindqvist",
            "Client dinner — Cedarline management",
            "Dinner with the Cedarline management team after the site visit.",
            30.0, 3.0,
        ),
        (
            "IT Access Provisioning", "Dina Al-Kaabi", "Bilal Rahman",
            "HR system access for new joiner",
            "New HR business partner starts Monday and needs the usual joiner bundle.",
            26.0, 1.0,
        ),
        (
            "Market Data Access", "Adam Kowalski", "Jonathan Pierce",
            "FactSet seat for the research desk",
            "Sharing a login is against the licence — we need a second seat.",
            22.0, 2.5,
        ),
    ]
    for proc, requester, assignee, title, body, created_h, ack_h in acknowledged:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="acknowledged",
            created_at=hours_ago(created_h),
            ack_after_hours=ack_h,
        )

    fresh_pending = [
        (
            "Invoice Approval", "Anna Sorenson", "Rania Khoury",
            "Invoice 88596 — Halcyon Facilities",
            "First invoice from the new facilities contractor. Please approve.",
            9.0,
        ),
        (
            "Travel Approval", "Marco Bianchi", "Hamza Al-Dosari",
            "Travel to London for the Cedarline signing",
            "One night, needs to be booked this week while fares hold.",
            5.0,
        ),
        (
            "Expense Reimbursement", "Sarah Whitfield", "Peter Lindqvist",
            "Taxis during the Sandpiper roadshow",
            "Four days of client meetings across the city. Receipts are in the folder.",
            3.0,
        ),
        (
            "Payment Release", "Mariam Al-Balushi", "Tomas Ferreira",
            "Wire for the Cedarline completion payment",
            "Funds flow is agreed; the wire needs releasing before the 2pm cut-off.",
            2.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h in fresh_pending:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="pending",
            created_at=hours_ago(created_h),
        )

    # Deliberately overdue: the agent picks these up on its first tick, so the
    # Agent Log is never empty when the demo starts.
    overdue = [
        (
            "Invoice Approval", "Tomas Ferreira", "Rania Khoury",
            "Invoice 88604 — custodian quarterly fee",
            "The custodian fee is due at the end of the week.",
            53.0,
        ),
        (
            "Travel Approval", "Claire Donovan", "Hamza Al-Dosari",
            "Ops offsite — flights and hotel",
            "Six of us, two nights, the week after next.",
            51.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h in overdue:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="pending",
            created_at=hours_ago(created_h),
        )

    # A historical escalation so the dashboard's escalation rate is non-zero.
    escalated = _seed_request(
        session,
        requester=people["Fatima Al-Zahrani"],
        process=processes["Valuation Sign-off"],
        assignee=people["Huda Al-Najjar"],
        title="Valuation inputs for the data warehouse feed",
        body="I need the signed-off marks to backfill the warehouse before quarter end.",
        status="pending",
        created_at=hours_ago(146.0),
    )
    t0 = escalated.created_at
    escalated.chase_count = 2
    _add_event(session, escalated, "chase", "No acknowledgement after 48h — chase 1 of 2 sent to Huda Al-Najjar.", t0 + timedelta(hours=48))
    _add_event(session, escalated, "chase", "Still unacknowledged — chase 2 of 2 sent to Huda Al-Najjar.", t0 + timedelta(hours=72))
    _add_event(
        session,
        escalated,
        "escalation",
        "Two chases went unanswered and no delegate is configured for 'Valuation Sign-off'. "
        "Escalated to Amira Haddadin (Chief Financial Officer).",
        t0 + timedelta(hours=96),
    )
    escalated.status = "escalated"
    escalated.assignee_id = people["Amira Haddadin"].id
    escalated.last_action_at = t0 + timedelta(hours=96)
    escalated.updated_at = t0 + timedelta(hours=96)
    session.add(
        Message(
            request_id=escalated.id,
            sender_id=None,
            recipient_id=people["Amira Haddadin"].id,
            type="escalation",
            body=(
                "Escalated: 'Valuation inputs for the data warehouse feed' was not picked up by "
                "Huda Al-Najjar after two chases."
            ),
            created_at=t0 + timedelta(hours=96),
            read=False,
        )
    )
    # rng is used to jitter read flags so inboxes look lived-in rather than uniform.
    for message in session.query(Message).all():
        if message.type == "dispatch" and rng.random() < 0.35:
            message.read = True


if __name__ == "__main__":  # pragma: no cover
    seed()
    print(f"Seeded {config.DB_PATH}")
