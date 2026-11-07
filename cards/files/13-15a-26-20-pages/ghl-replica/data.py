# Data for the GoHighLevel Opportunities replica (Adi, 2026-11-07).
# Every contact, business, funnel, deal value, date and column total here is illustrative.
# Nothing is copied from the account the design was taken from.
import random

random.seed(20261107)

NAMES = [
    'Daniel Whitford', 'Priya Natarajan', 'Marcus Ellery', 'Hannah Kowalski', 'Omar Haddad', 'Lucia Ferreira',
    'Grant Holloway', 'Mei Lin Tan', 'Jonas Albrecht', 'Rachel Okafor', 'Victor Lindqvist', 'Aisha Rahman',
    'Patrick Doyle', 'Sofia Marchetti', 'Ethan Brooks', 'Nadia Petrova', 'Caleb Morrison', 'Ingrid Solberg',
    'Rohan Mehta', 'Claire Dubois', 'Tobias Wren', 'Leila Haddadi', 'Simon Archer', 'Yuki Tanaka',
    'Felix Andersson', 'Brianna Cole', 'Kwame Mensah', 'Elena Vasquez', 'Owen Gallagher', 'Fatima Zahra',
    'Henry Lancaster', 'Chloe Bennett', 'Arjun Kapoor', 'Megan Sullivan', 'Lars Eriksen', 'Tessa Monroe',
    'Gabriel Santos', 'Naomi Fischer', 'Declan Murphy', 'Sana Qureshi', 'Isaac Thornton', 'Julia Novak',
    'Adrian Cho', 'Ruth Abernathy', 'Mateo Rinaldi', 'Zoe Harrington', 'Kieran Walsh', 'Anika Bose',
]
BUSINESSES = [
    'Northbridge Advisory', 'Clearpath Consulting', 'Lumen Growth Partners', 'Brightwave Media', 'Harbor & Pine Capital',
    'Summit Ridge Coaching', 'Vantage Point Labs', 'Elevate Health Group', 'Ironclad Logistics', 'Bluefin Analytics',
    'Keystone Legal Group', 'Atlas Learning Co', 'Redwood Wealth Partners', 'Pinnacle Talent', 'Meridian SaaS',
    'Copperline Agency', 'Silverleaf Dental Group', 'Oakmont Real Estate', 'Nimbus Cloud Services', 'Trueline Insurance',
    'Crescent Fitness Studios', 'Granite Peak Builders', 'Sparrow Creative', 'Westbrook Accounting', 'Helix Biotech Advisors',
    'Orbit Ecommerce', 'Foundry Leadership', 'Tidewater Marine', 'Riverstone Finance', 'Evergreen Coaching Co',
    'Halcyon Wellness', 'Beacon Recruitment', 'Quarry Street Studios', 'Lighthouse Edtech', 'Stonebridge Partners',
    'Cobalt Security', 'Juniper Home Services', 'Frontier Freight', 'Mosaic Marketing', 'Ashford Private Clinic',
    'Larkspur Interiors', 'Ridgeway Solar', 'Kestrel Ventures', 'Parkside Physio', 'Arcadia Travel', 'Sterling Payroll',
    'Fernwood Academy', 'Highline Fintech',
]
FUNNELS = ['Webinar 7', 'Webinar 8', 'Webinar 9', 'Webinar 10', 'Webinar 11', 'Webinar 12', 'VSL 2', 'VSL 3', 'VSL 4', 'VSL 5']
ASSIGNEES = ['KR', 'SM', 'DL', 'NB']

# Column header totals: (opportunities, total deal value). Values are whole dollars, rounded to $100.
STAGES = {
    'Duplicates': (38, 142600),
    'Application, No Booking': (126, 468300),
    'Upcoming 1st Call Booked': (184, 812700),
    '1st Call Done': (352, 1694200),
    '2nd Call Done (In Prog)': (147, 1128900),
    'Warm List (1st or 2nd Call done)': (61, 497300),
    'Hot List (Verbal Commit)': (34, 318600),
    'Deal Won': (72, 1246800),
    'Long Term Nurture': (0, 0),
}
TOTAL = sum(c for c, _ in STAGES.values())


def ordinal(d):
    return f"{d}{'th' if 11 <= d % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')}"


def money(v):
    # GoHighLevel's format in this account: no grouping under 10,000, a narrow space group above, comma decimals.
    s = f'{v:,}'.replace(',', '\u00a0') if v >= 10000 else str(v)
    return f'${s},00'


def deal_value(stage):
    lo, hi = (6000, 24000) if stage in ('Hot List (Verbal Commit)', 'Deal Won', '2nd Call Done (In Prog)') else (2500, 15000)
    v = random.uniform(lo, hi)
    return int(-(-v // 100) * 100)  # round up to the next $100


def when():
    d = random.randint(6, 31)
    h = random.choice([9, 10, 11, 12, 1, 2, 3, 4, 5])
    m = random.choice(['00', '30'])
    ap = 'am' if h in (9, 10, 11) else 'pm'
    return f'Oct {ordinal(d)}, {h}:{m} {ap}'


def build(cards_per_stage=5):
    names, biz = NAMES[:], BUSINESSES[:]
    random.shuffle(names)
    random.shuffle(biz)
    stages = []
    for st, (count, total) in STAGES.items():
        cards = []
        if count:
            for _ in range(cards_per_stage):
                cards.append({
                    'name': names.pop(), 'business': biz.pop(), 'funnel': random.choice(FUNNELS),
                    'value': money(deal_value(st)), 'when': when(), 'assignee': random.choice(ASSIGNEES),
                })
        stages.append({'stage': st, 'count': f'{count} opportunities', 'total': money(total), 'cards': cards})
    return {
        'location_name': 'Tantra Enterprise', 'location_city': 'Bengaluru, Karnataka', 'user_initials': 'AM',
        'total': f'{TOTAL} opportunities',
        # Saved views (smart list tabs), left to right.
        'views': ['Open opportunities', 'Webinar Leads', 'VSL Leads', 'Enterprise - 2026 Opps'],
        'stages': stages,
    }
