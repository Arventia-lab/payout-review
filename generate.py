"""
Synthetic data generator for the Payout Review demo.

Marketplace wallet model:
  - users top up a wallet (card / bank / crypto)
  - they place orders (merchant, category, amount)
  - some orders are refunded
  - they earn promo credit (with a minimum-spend requirement) and cashback
  - they request payouts

Every planted case maps to exactly one detection rule, so the demo can be
checked: each flagged account should be flagged for the right reason, and the
clean accounts should stay clean.

No real data. Nothing here comes from any real platform or person.
"""

import json, random
from datetime import datetime, timedelta

random.seed(20260923)

TODAY = datetime(2026, 9, 12, 23, 0)

# ---------------------------------------------------------------- catalogue
# Categories that are easy to resell or convert back to cash. These are the
# classic laundering vehicles on a marketplace.
HIGH_LIQUIDITY = ["Gift Cards", "Digital Codes", "Prepaid Top-ups", "Mobile Credit"]
NORMAL_CATEGORY = ["Home & Living", "Apparel", "Books", "Groceries", "Pet Supplies",
                   "Kitchen", "Sports", "Toys", "Beauty"]
ELECTRONICS = ["Electronics", "Phones & Tablets"]

MERCHANTS = ["MRC-101", "MRC-102", "MRC-103", "MRC-104", "MRC-105",
             "MRC-106", "MRC-107", "MRC-108", "MRC-109", "MRC-110"]

METHODS = ["Bank Transfer", "Credit Card", "Debit Card", "Crypto"]


def ts(d):
    return d.strftime("%Y-%m-%d %H:%M")


def gunler(n):
    """A timestamp n days before today, at a plausible hour."""
    return TODAY - timedelta(days=n, hours=random.randint(0, 12),
                             minutes=random.randint(0, 59))


def order(gun, tutar, merchant=None, kategori=None, refunded=False, pending=False):
    return {
        "date": ts(gunler(gun)),
        "amount": round(tutar, 2),
        "merchant": merchant or random.choice(MERCHANTS),
        "category": kategori or random.choice(NORMAL_CATEGORY),
        "refunded": refunded,
        "pending": pending,
    }


def topup(gun, tutar, method="Bank Transfer"):
    return {"date": ts(gunler(gun)), "amount": round(tutar, 2), "method": method}


def payout(gun, tutar, method="Bank Transfer", status="Completed"):
    return {"date": ts(gunler(gun)), "amount": round(tutar, 2),
            "method": method, "status": status}


def promo(gun, tutar, margin, kind="Promo Credit"):
    """A promotion credit.

    `margin` is the INTENDED relationship between what the customer had to spend
    and what they actually spent: 0.01 means they stopped 1% past the line, 0.40
    means they carried on shopping well beyond it.

    The requirement and the completed amount are not written here - they are
    derived from the account's real orders in reconcile(), so the demo can never
    show a customer completing a requirement they did not actually spend.
    """
    return {"date": ts(gunler(gun)), "kind": kind, "amount": round(tutar, 2),
            "_margin": margin,
            "requirement": 0.0, "completed": 0.0, "completed_in_high_liquidity": 0.0}


def normal_orders(n, alt, ust, gun_alt=1, gun_ust=90, refund_rate=0.04):
    """Ordinary shopping behaviour."""
    o = []
    for _ in range(n):
        o.append(order(random.randint(gun_alt, gun_ust),
                       random.choice([alt, (alt + ust) / 2, ust]) * random.uniform(0.7, 1.3),
                       refunded=random.random() < refund_rate))
    return o


USERS = []
PAYOUTS = []


def add(uid, name, tag, **kw):
    u = {
        "id": uid,
        "username": name,
        "tag": tag,
        "registered": kw.get("registered", ts(gunler(kw.get("age_days", 200)))),
        "kyc": kw.get("kyc", "Verified"),
        "ip": kw.get("ip", "88.230.%d.%d" % (random.randint(1, 250), random.randint(1, 250))),
        "device_fp": kw.get("device_fp", "dev-%04x" % random.randint(0, 0xFFFF)),
        "payment_fp": kw.get("payment_fp", "pay-%04x" % random.randint(0, 0xFFFF)),
        "crypto_wallet": kw.get("crypto_wallet"),
        "referrer": kw.get("referrer", "REF-%d" % random.randint(10, 60)),
        "cashback_earned": kw.get("cashback_earned", 0),
        "chargebacks": kw.get("chargebacks", 0),
        "seller_accounts_linked": kw.get("seller_accounts_linked", []),
        "payout_method_added": kw.get("payout_method_added"),
        "rejection_history": kw.get("rejection_history", []),
        "topups": kw.get("topups", []),
        "orders": kw.get("orders", []),
        "promos": kw.get("promos", []),
        "past_payouts": kw.get("past_payouts", []),
    }
    USERS.append(u)
    return u


def pending_payout(pid, uid, amount, method="Bank Transfer", days=0):
    PAYOUTS.append({"id": pid, "user": uid, "amount": round(amount, 2),
                    "date": ts(gunler(days)), "method": method})


# =====================================================================
#  U1001  clean shopper - should come out LOW
# =====================================================================
add("U1001", "user_1001", "clean",
    age_days=190, kyc="Verified",
    topups=[topup(95, 3000), topup(70, 4000), topup(45, 2500), topup(20, 2500)],
    orders=normal_orders(60, 80, 400),
    promos=[promo(94, 1500, 0.41)],
    past_payouts=[payout(44, 3000)],
    cashback_earned=420)
pending_payout("P-5001", "U1001", 15000)

# =====================================================================
#  U1002  promo abuser - clears the requirement by a hair, then cashes out
# =====================================================================
add("U1002", "user_1002", "promo abuser",
    age_days=26, kyc="Verified", ip="185.44.12.9",
    topups=[topup(25, 2000), topup(18, 2000)],
    orders=normal_orders(40, 300, 900),
    promos=[promo(25, 2000, 0.01)],
    cashback_earned=90)
pending_payout("P-5002", "U1002", 21000)

# =====================================================================
#  U1003  gift-card launderer - spends almost everything on resellable codes
# =====================================================================
gc = [order(random.randint(1, 40), random.uniform(1500, 4000),
            kategori=random.choice(HIGH_LIQUIDITY)) for _ in range(34)]
add("U1003", "user_1003", "high-liquidity concentration",
    age_days=38, kyc="Verified", ip="185.44.12.9",
    topups=[topup(39, 30000, "Credit Card"), topup(20, 25000, "Credit Card")],
    orders=gc + normal_orders(6, 100, 300),
    promos=[promo(38, 3000, 0.016)])
pending_payout("P-5003", "U1003", 48000)

# =====================================================================
#  U1004  wash trading - buys from a seller account that is linked to them
# =====================================================================
wash = [order(random.randint(1, 45), random.uniform(2000, 5000),
              merchant="MRC-777") for _ in range(26)]
add("U1004", "user_1004", "self-dealing",
    age_days=64, kyc="Verified",
    device_fp="dev-w41", payment_fp="pay-w41",
    seller_accounts_linked=["MRC-777"],
    topups=[topup(60, 40000, "Credit Card"), topup(30, 35000, "Credit Card")],
    orders=wash + normal_orders(8, 150, 500),
    promos=[promo(60, 4000, 0.05)])
pending_payout("P-5004", "U1004", 66000)

# =====================================================================
#  U1005  single-merchant concentration - collusion with one seller
# =====================================================================
one = [order(random.randint(1, 50), random.uniform(900, 2400),
             merchant="MRC-104") for _ in range(31)]
add("U1005", "user_1005", "merchant collusion",
    age_days=75, kyc="Verified",
    topups=[topup(70, 25000), topup(35, 20000)],
    orders=one + normal_orders(5, 120, 400))
pending_payout("P-5005", "U1005", 37000)

# =====================================================================
#  U1006-08  referral cluster on one device and card
# =====================================================================
for i, uid in enumerate(["U1006", "U1007", "U1008"]):
    add(uid, "user_10%02d" % (6 + i), "referral cluster",
        age_days=13, kyc="Verified",
        ip="91.93.7.%d" % (40 + i),
        device_fp="dev-c77", payment_fp="pay-c77",
        referrer="REF-99",
        topups=[topup(12, 1500), topup(6, 1500)],
        orders=normal_orders(18, 200, 600),
        promos=[promo(12, 1500, 0.01)])
    pending_payout("P-50%02d" % (6 + i), uid, 12500)

# =====================================================================
#  U1009  pending orders while requesting a payout
# =====================================================================
add("U1009", "user_1009", "open orders",
    age_days=120, kyc="Verified",
    topups=[topup(110, 12000), topup(50, 8000)],
    orders=normal_orders(34, 200, 700) + [
        order(3, 6500, pending=True), order(2, 4200, pending=True),
        order(1, 5100, pending=True)],
    promos=[promo(110, 1200, 0.30)])
pending_payout("P-5009", "U1009", 19000)

# =====================================================================
#  U1010  cashback-driven account
# =====================================================================
add("U1010", "user_1010", "cashback heavy",
    age_days=160, kyc="Verified",
    topups=[topup(150, 9000), topup(80, 9000), topup(30, 6000)],
    orders=normal_orders(72, 150, 500),
    cashback_earned=9200)
pending_payout("P-5010", "U1010", 14000)

# =====================================================================
#  U1011-13  ordinary customers - should come out LOW
# =====================================================================
for i, uid in enumerate(["U1011", "U1012", "U1013"]):
    add(uid, "user_10%02d" % (11 + i), "normal",
        age_days=random.randint(150, 320), kyc="Verified",
        topups=[topup(random.randint(120, 200), random.uniform(2000, 5000)),
                topup(random.randint(40, 100), random.uniform(2000, 5000))],
        orders=normal_orders(random.randint(45, 70), 90, 450),
        cashback_earned=random.randint(150, 600))
    pending_payout("P-50%02d" % (11 + i), uid, random.uniform(2500, 6000))

# =====================================================================
#  U1014  money mover - card top-ups, barely shops, cashes out to bank
# =====================================================================
add("U1014", "user_1014", "money movement",
    age_days=17, kyc="Verified",
    topups=[topup(16, 30000, "Credit Card"), topup(11, 30000, "Credit Card"),
            topup(5, 25000, "Credit Card")],
    orders=normal_orders(7, 400, 900))
pending_payout("P-5014", "U1014", 72000)

# =====================================================================
#  U1015  refund abuser - buys, complains, gets compensated, repeats
# =====================================================================
ref = [order(random.randint(1, 60), random.uniform(700, 1800), refunded=True)
       for _ in range(21)]
add("U1015", "user_1015", "refund abuse",
    age_days=140, kyc="Verified",
    topups=[topup(130, 8000), topup(60, 7000)],
    orders=ref + normal_orders(16, 200, 600),
    promos=[promo(55, 3500, 0.05, kind="Goodwill Credit"),
            promo(25, 4000, 0.04, kind="Goodwill Credit")])
pending_payout("P-5015", "U1015", 17500)

# =====================================================================
#  U1016  payment crossing - tops up one way, cashes out another
# =====================================================================
add("U1016", "user_1016", "payment crossing",
    age_days=90, kyc="Verified",
    topups=[topup(80, 20000, "Credit Card"), topup(40, 18000, "Credit Card"),
            topup(12, 6000, "Bank Transfer")],
    orders=normal_orders(29, 250, 800))
pending_payout("P-5016", "U1016", 31000, method="Crypto")

# =====================================================================
#  U1017 / U1018  shared crypto wallet and IP
# =====================================================================
for i, uid in enumerate(["U1017", "U1018"]):
    add(uid, "user_10%02d" % (17 + i), "shared wallet",
        age_days=random.randint(45, 80), kyc="Verified",
        ip="45.12.30.77",
        crypto_wallet="wlt-3f9a21",
        topups=[topup(40, 15000, "Crypto"), topup(18, 12000, "Crypto")],
        orders=normal_orders(22, 300, 900))
    pending_payout("P-50%02d" % (17 + i), uid, 24000, method="Crypto")

# =====================================================================
#  U1019  chargeback history
# =====================================================================
add("U1019", "user_1019", "chargebacks",
    age_days=19, kyc="Verified",
    chargebacks=3,
    topups=[topup(18, 22000, "Credit Card"), topup(9, 18000, "Credit Card")],
    orders=normal_orders(14, 500, 1500))
pending_payout("P-5019", "U1019", 33000)

# =====================================================================
#  U1020  very high refund rate
# =====================================================================
hr = [order(random.randint(1, 70), random.uniform(400, 1200),
            refunded=(k % 5 != 0)) for k in range(45)]
add("U1020", "user_1020", "high refund rate",
    age_days=110, kyc="Verified",
    topups=[topup(100, 14000), topup(45, 10000)],
    orders=hr)
pending_payout("P-5020", "U1020", 16000)

# =====================================================================
#  U1021  payout velocity - many cashouts in a short window
# =====================================================================
add("U1021", "user_1021", "payout velocity",
    age_days=85, kyc="Verified",
    topups=[topup(80, 26000), topup(40, 22000)],
    orders=normal_orders(26, 350, 1000),
    past_payouts=[payout(6, 9000), payout(4, 8500), payout(3, 9500),
                  payout(2, 8000), payout(1, 9200)])
pending_payout("P-5021", "U1021", 11000)

# =====================================================================
#  U1022  payout method added days ago, large amount
# =====================================================================
add("U1022", "user_1022", "new payout method",
    age_days=210, kyc="Verified",
    payout_method_added=ts(gunler(2)),
    topups=[topup(200, 18000), topup(120, 15000), topup(50, 12000)],
    orders=normal_orders(58, 200, 700))
pending_payout("P-5022", "U1022", 40000, method="Crypto")

# =====================================================================
#  U1023  KYC not completed
# =====================================================================
add("U1023", "user_1023", "kyc pending",
    age_days=34, kyc="Pending",
    topups=[topup(30, 9000), topup(14, 7000)],
    orders=normal_orders(20, 250, 700))
pending_payout("P-5023", "U1023", 13500)

# =====================================================================
#  U1024  prior rejections on file
# =====================================================================
add("U1024", "user_1024", "prior rejections",
    age_days=230, kyc="Verified",
    rejection_history=[
        {"date": "2026-05-04", "reason": "Linked account under review"},
        {"date": "2026-07-19", "reason": "Promotion terms breach"}],
    topups=[topup(200, 11000), topup(90, 9000)],
    orders=normal_orders(38, 180, 600))
pending_payout("P-5024", "U1024", 12000)


# =====================================================================
#  reconcile - make every wallet add up
#
#  A wallet cannot spend money it never received. Writing top-ups and spending
#  independently produces accounts that bought more than they funded, which is
#  the first thing anyone who reviews payouts for a living would notice.
#
#  So the orders are the truth, and everything else is derived from them:
#    - the promotion requirement comes from what was actually spent
#    - the top-ups are sized to cover spending, pending orders and the payout
#  The INTENT of each planted case is preserved, because what makes a case is
#  the RATIO between these numbers, not their absolute size.
# =====================================================================
def reconcile():
    for u in USERS:
        orders  = u["orders"]
        kept    = [o for o in orders if not o["pending"] and not o["refunded"]]
        spend   = sum(o["amount"] for o in kept)
        refunds = sum(o["amount"] for o in orders if o["refunded"])
        pendingv= sum(o["amount"] for o in orders if o["pending"])
        liq     = sum(o["amount"] for o in kept if o["category"] in HIGH_LIQUIDITY)
        liq_share = liq / spend if spend else 0.0

        # ---- promotions: requirement derived from real spend ----
        promos = u["promos"]
        if promos:
            share = spend / len(promos)          # split the spend across credits
            for b in promos:
                margin = b.pop("_margin", 0.2)
                b["completed"] = round(share, 2)
                b["requirement"] = round(share / (1 + margin), 2)
                b["completed_in_high_liquidity"] = round(share * liq_share, 2)

        promo_total = sum(b["amount"] for b in promos)
        cashback    = u.get("cashback_earned", 0)
        past        = sum(x["amount"] for x in u.get("past_payouts", []))
        pend        = next((p["amount"] for p in PAYOUTS if p["user"] == u["id"]), 0)

        # ---- top-ups: sized so the wallet can actually cover everything ----
        needed = spend + pendingv + past + pend - promo_total - refunds - cashback
        needed = max(needed * 1.03, 0)           # small buffer, as a real balance has
        current = sum(t["amount"] for t in u["topups"])
        if current > 0 and needed > 0:
            k = needed / current
            for t in u["topups"]:
                t["amount"] = round(t["amount"] * k, 2)


def verify():
    """Refuse to ship data that does not add up."""
    problems = []
    for u in USERS:
        orders  = u["orders"]
        kept    = [o for o in orders if not o["pending"] and not o["refunded"]]
        spend   = sum(o["amount"] for o in kept)
        refunds = sum(o["amount"] for o in orders if o["refunded"])
        pendingv= sum(o["amount"] for o in orders if o["pending"])
        topups  = sum(t["amount"] for t in u["topups"])
        promo_t = sum(b["amount"] for b in u["promos"])
        cashback= u.get("cashback_earned", 0)
        past    = sum(x["amount"] for x in u.get("past_payouts", []))
        pend    = next((p["amount"] for p in PAYOUTS if p["user"] == u["id"]), 0)

        available = topups + promo_t + refunds + cashback
        used      = spend + pendingv + past + pend
        if used - available > 1:
            problems.append("%s (%s): short by %.0f" % (u["id"], u["tag"], used - available))

        for b in u["promos"]:
            if b["completed"] > spend + 1:
                problems.append("%s: promo completed %.0f exceeds spend %.0f"
                                % (u["id"], b["completed"], spend))
    return problems


reconcile()
issues = verify()
if issues:
    print("DATA IS INCONSISTENT:")
    for i in issues:
        print("  -", i)
    raise SystemExit(1)

# =====================================================================
#  write out
# =====================================================================
DATA = {
    "generated": ts(TODAY),
    "today": ts(TODAY),
    "high_liquidity_categories": HIGH_LIQUIDITY,
    "users": USERS,
    "pending_payouts": PAYOUTS,
}

with open("demo-data.js", "w", encoding="utf-8") as f:
    # `let`, not `const`: the page replaces this whole object when the user
    # loads their own CSV files.
    f.write("let DEMO = ")
    json.dump(DATA, f, ensure_ascii=False, indent=1)
    f.write(";\n")

orders_total = sum(len(u["orders"]) for u in USERS)
print("users            :", len(USERS))
print("pending payouts  :", len(PAYOUTS))
print("orders           :", orders_total)
print("written          : demo-data.js")
