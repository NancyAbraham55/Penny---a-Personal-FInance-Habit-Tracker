import json
import os
import time
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Tuple

import streamlit as st

st.set_page_config(page_title="Penny", page_icon="🌳", layout="centered")

DATA_FILE = "penny_data.json"
MAX_LEVEL_PER_TREE = 10
MAX_TREES = 100
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "EUR ",
    "GBP": "GBP ",
    "SAR": "SAR ",
    "AED": "AED ",
    "INR": "INR ",
}
CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "SAR": "Saudi Riyal",
    "AED": "UAE Dirham",
    "INR": "Indian Rupee",
}
CURRENCY_PPP_PER_USD = {
    # Estimated local purchasing-power units per 1 USD-equivalent.
    "USD": 1.0,
    "EUR": 0.9,
    "GBP": 0.8,
    "SAR": 2.7,
    "AED": 2.9,
    "INR": 23.0,
}

ACTIONS = [
    {"label": "Skip coffee", "emoji": "☕", "default_amount_usd": 5.0},
    {"label": "Skip takeout", "emoji": "🍔", "default_amount_usd": 14.0},
    {"label": "Cook at home", "emoji": "🍳", "default_amount_usd": 10.0},
    {"label": "Added to investment", "emoji": "📈", "default_amount_usd": 25.0},
    {"label": "No impulse buy", "emoji": "🛍️", "default_amount_usd": 12.0},
]

TREE_STAGES = [
    (1, "Seed", "🌰"),
    (2, "Sprout", "🌱"),
    (3, "Sapling", "🌿"),
    (4, "Young Plant", "🪴"),
    (6, "Young Tree", "🌳"),
    (8, "Money Tree", "🌲"),
    (10, "Ancient Tree", "🌴"),
]

ECOSYSTEMS = [
    {"name": "City Park", "emoji": "🏙️", "unlock_trees": 0},
    {"name": "Tropical Rainforest", "emoji": "🌴", "unlock_trees": 10},
    {"name": "Mountain Forest", "emoji": "🏔️", "unlock_trees": 25},
    {"name": "Desert Oasis", "emoji": "🏜️", "unlock_trees": 50},
    {"name": "Island Mangrove", "emoji": "🏝️", "unlock_trees": 75},
]


def load_data() -> Dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("xp", 0)
            data.setdefault("entries", [])
            data.setdefault("profile", {})
            data["profile"].setdefault("username", "Penny User")
            data["profile"].setdefault("currency", "USD")
            data["profile"].setdefault("onboarded", False)
            data["profile"].setdefault("ecosystem", "City Park")
            data.setdefault("forest", {})
            data["forest"].setdefault("tree_names", [])
            return data
    return {
        "xp": 0,
        "entries": [],
        "profile": {
            "username": "Penny User",
            "currency": "USD",
            "onboarded": False,
            "ecosystem": "City Park",
        },
        "forest": {"tree_names": []},
    }


def save_data(data: Dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def xp_needed_for_next_level(level: int) -> int:
    # Early levels easier, later levels harder.
    return 40 + (level - 1) * 25


def xp_to_grow_one_tree() -> int:
    return sum(xp_needed_for_next_level(level) for level in range(1, MAX_LEVEL_PER_TREE))


def level_state_from_tree_xp(tree_xp: int) -> Tuple[int, int, int]:
    level = 1
    remaining = tree_xp
    while level < MAX_LEVEL_PER_TREE:
        needed = xp_needed_for_next_level(level)
        if remaining >= needed:
            remaining -= needed
            level += 1
        else:
            break

    if level >= MAX_LEVEL_PER_TREE:
        return MAX_LEVEL_PER_TREE, 0, 0
    return level, remaining, xp_needed_for_next_level(level)


def stage_for_level(level: int) -> Tuple[str, str]:
    for stage_level, stage_name, stage_emoji in reversed(TREE_STAGES):
        if level >= stage_level:
            return stage_name, stage_emoji
    return "Seed", "🌰"


def tree_name_for_index(data: Dict, index: int) -> str:
    default_names = [
        "Aurora", "Moss", "Clover", "Maple", "Willow", "Sage", "River", "Ash",
        "Cedar", "Ivy", "Blossom", "Flora", "Nova", "Luna", "Echo", "Birch",
    ]
    forest = data.setdefault("forest", {})
    tree_names = forest.setdefault("tree_names", [])
    while len(tree_names) <= index:
        next_name = default_names[len(tree_names) % len(default_names)]
        suffix = (len(tree_names) // len(default_names)) + 1
        tree_names.append(next_name if suffix == 1 else f"{next_name} {suffix}")
    return tree_names[index]


def add_entry(data: Dict, action_label: str, action_emoji: str, amount: float, xp: int) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    data["entries"].append(
        {
            "timestamp": timestamp,
            "date": date.today().isoformat(),
            "action": action_label,
            "emoji": action_emoji,
            "amount": round(amount, 2),
            "xp": xp,
            "currency": data.get("profile", {}).get("currency", "USD"),
        }
    )
    data["xp"] += xp
    save_data(data)


def aggregate(entries: List[Dict]) -> Tuple[Dict, Dict, Dict]:
    daily = defaultdict(float)
    weekly = defaultdict(float)
    monthly = defaultdict(float)
    for row in entries:
        dt = datetime.fromisoformat(row["timestamp"])
        amount = float(row["amount"])
        daily[dt.strftime("%Y-%m-%d")] += amount
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly[week_key] += amount
        monthly[dt.strftime("%Y-%m")] += amount
    return daily, weekly, monthly


def entries_for_currency(entries: List[Dict], currency_code: str) -> List[Dict]:
    # Only show activity created in the currently selected currency.
    return [entry for entry in entries if entry.get("currency") == currency_code]


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_currency_for_code(value: float, currency_code: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency_code, "$")
    return f"{symbol}{value:,.2f}"


def local_amount_from_usd(usd_amount: float, currency_code: str) -> float:
    ppp_per_usd = CURRENCY_PPP_PER_USD.get(currency_code, 1.0)
    return round(usd_amount * ppp_per_usd, 2)


def xp_from_amount(amount: float, currency_code: str) -> int:
    # XP rule anchored to USD-equivalent value:
    # every 5 USD-equivalent saved earns 10 XP.
    ppp_per_usd = CURRENCY_PPP_PER_USD.get(currency_code, 1.0)
    usd_equivalent = amount / ppp_per_usd if ppp_per_usd > 0 else amount
    return int(usd_equivalent // 5) * 10


def min_local_amount_for_xp(currency_code: str) -> float:
    return local_amount_from_usd(5.0, currency_code)


def greeting_for_time() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


st.markdown(
    """
<style>
    .stApp {
        max-width: 760px;
        margin: 0 auto;
        font-family: "SF Pro Text", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    html, body, [class*="css"] {
        font-family: "SF Pro Text", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .hero {
        background: linear-gradient(135deg, #e4f7ea, #f6efe5);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 14px;
        text-align: center;
    }
    .tree { font-size: 70px; line-height: 1.1; }
    .title { font-size: 28px; font-weight: 700; color: #173b2b; }
    .subtitle { color: #4b5f55; margin-top: 4px; }
    .cover {
        background: linear-gradient(135deg, #d9f5e2, #eaf3ff, #fff0e7);
        border-radius: 24px;
        padding: 48px 24px;
        text-align: center;
        margin-top: 24px;
        border: 1px solid #d7e8dc;
    }
    .cover-logo { font-size: 72px; }
    .cover-title { font-size: 42px; font-weight: 800; color: #1d3f30; margin-top: 8px; }
    .cover-tagline { font-size: 18px; color: #4f6157; margin-top: 8px; }
    .finance-note {
        background: #f4f8ff;
        border: 1px solid #dae6ff;
        border-radius: 12px;
        padding: 10px 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

data = load_data()
entries = data.get("entries", [])
xp = int(data.get("xp", 0))
profile = data.get("profile", {})
username = profile.get("username", "Penny User")
currency_code = profile.get("currency", "USD")
is_onboarded = bool(profile.get("onboarded", False))
selected_ecosystem = profile.get("ecosystem", "City Park")
xp_per_tree = xp_to_grow_one_tree()
mature_trees = min(xp // xp_per_tree, MAX_TREES)
xp_in_current_tree = xp % xp_per_tree
level, xp_in_level, next_level_requirement = level_state_from_tree_xp(xp_in_current_tree)
stage_name, tree_emoji = stage_for_level(level)
current_tree_index = min(mature_trees, MAX_TREES - 1)
current_tree_name = tree_name_for_index(data, current_tree_index)
save_data(data)

if "show_cover" not in st.session_state:
    st.session_state.show_cover = True

if st.session_state.show_cover:
    st.markdown(
        """
<div class="cover">
    <div class="cover-logo">🌳</div>
    <div class="cover-title">Penny</div>
    <div class="cover-tagline">Small steps lead to big dreams</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Loading your forest...")
    time.sleep(3)
    st.session_state.show_cover = False
    st.rerun()
    st.stop()

if not is_onboarded:
    st.markdown("## Welcome to Penny")
    st.info("Set up your profile to start using the app.")
    with st.form("onboarding_form"):
        onboarding_name = st.text_input("What should we call you?", placeholder="Nancy")
        onboarding_currency = st.selectbox("Pick your currency", options=list(CURRENCY_SYMBOLS.keys()), index=0)
        submitted = st.form_submit_button("Start my Penny journey")

    if submitted:
        data["profile"] = {
            "username": onboarding_name.strip() if onboarding_name.strip() else "Penny User",
            "currency": onboarding_currency,
            "onboarded": True,
            "ecosystem": "City Park",
        }
        save_data(data)
        st.success("Profile saved. Loading your home page...")
        st.rerun()
    st.stop()

st.sidebar.title("Penny")
if "nav_view" not in st.session_state:
    st.session_state.nav_view = "home"

nav_col1, nav_col2 = st.sidebar.columns(2)
with nav_col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.nav_view = "home"
with nav_col2:
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.nav_view = "settings"

selected_view = st.session_state.nav_view

active_currency_entries = entries_for_currency(entries, currency_code)
active_currency_xp = int(sum(int(e.get("xp", 0)) for e in active_currency_entries))
active_currency_mature_trees = min(active_currency_xp // xp_per_tree, MAX_TREES)
active_currency_stage_level, _, _ = level_state_from_tree_xp(active_currency_xp % xp_per_tree)
active_currency_tree_emoji = stage_for_level(active_currency_stage_level)[1]
active_currency_tree_index = min(active_currency_mature_trees, MAX_TREES - 1)
active_currency_tree_name = tree_name_for_index(data, active_currency_tree_index)

unlocked_ecosystems = [e for e in ECOSYSTEMS if active_currency_mature_trees >= e["unlock_trees"]]
if selected_ecosystem not in [e["name"] for e in unlocked_ecosystems]:
    selected_ecosystem = unlocked_ecosystems[0]["name"]
    data["profile"]["ecosystem"] = selected_ecosystem
    save_data(data)

st.sidebar.markdown("---")
st.sidebar.subheader("Forest view")
filled = active_currency_mature_trees
forest_cells = []
for cell in range(MAX_TREES):
    if cell < filled:
        forest_cells.append("🌲")
    elif cell == filled and filled < MAX_TREES:
        forest_cells.append(active_currency_tree_emoji)
    else:
        forest_cells.append("▫️")
forest_rows = []
for start in range(0, MAX_TREES, 10):
    forest_rows.append("".join(forest_cells[start:start + 10]))
st.sidebar.markdown("\n".join(forest_rows))
if active_currency_mature_trees < MAX_TREES:
    st.sidebar.markdown(f"In progress: {active_currency_tree_emoji} **{active_currency_tree_name}**")
st.sidebar.caption(f"{active_currency_mature_trees}/{MAX_TREES} trees planted in {selected_ecosystem} ({currency_code})")

if selected_view == "home":
    currency_entries = entries_for_currency(entries, currency_code)
    currency_xp = int(sum(int(e.get("xp", 0)) for e in currency_entries))
    currency_xp_per_tree = xp_to_grow_one_tree()
    currency_mature_trees = min(currency_xp // currency_xp_per_tree, MAX_TREES)
    currency_xp_in_current_tree = currency_xp % currency_xp_per_tree
    currency_level, currency_xp_in_level, currency_next_level_requirement = level_state_from_tree_xp(
        currency_xp_in_current_tree
    )
    currency_stage_name, currency_tree_emoji = stage_for_level(currency_level)
    currency_tree_index = min(currency_mature_trees, MAX_TREES - 1)
    currency_tree_name = tree_name_for_index(data, currency_tree_index)

    st.markdown(f"### Hi {username}, {greeting_for_time()}")
    st.caption(f"Your current tree is **{currency_tree_name}** — **{currency_stage_name}** at **Level {currency_level}**.")
    st.markdown(
        f"""
<div class="hero">
    <div class="tree">{currency_tree_emoji}</div>
    <div class="title">{currency_tree_name}</div>
    <div class="subtitle">{currency_stage_name} • Level {currency_level} • {username}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if currency_next_level_requirement > 0:
        st.progress(
            currency_xp_in_level / currency_next_level_requirement,
            text=f"⭐ {currency_xp} XP in {currency_code} • {currency_next_level_requirement - currency_xp_in_level} XP to next level",
        )
    else:
        st.progress(1.0, text=f"⭐ {currency_xp} XP in {currency_code} • Tree fully grown")

    st.markdown("---")
    st.subheader("Forest progress")
    forest_col1, forest_col2, forest_col3 = st.columns(3)
    forest_col1.metric("Mature trees", f"{currency_mature_trees}/{MAX_TREES}")
    forest_col2.metric("Current tree level", f"{currency_level}/{MAX_LEVEL_PER_TREE}")
    forest_col3.metric("Current ecosystem", selected_ecosystem)
    st.progress(
        currency_mature_trees / MAX_TREES,
        text=f"{currency_mature_trees} trees planted • {MAX_TREES - currency_mature_trees} until full forest",
    )
    next_unlock = next((e for e in ECOSYSTEMS if e["unlock_trees"] > currency_mature_trees), None)
    if next_unlock:
        remaining_trees = next_unlock["unlock_trees"] - currency_mature_trees
        st.caption(
            f"Next ecosystem unlock: {next_unlock['emoji']} {next_unlock['name']} in {remaining_trees} more trees."
        )
    else:
        st.caption("All ecosystems unlocked. Amazing consistency.")

    daily, weekly, monthly = aggregate(currency_entries)
    total_saved = sum(float(e["amount"]) for e in currency_entries)
    today_key = date.today().strftime("%Y-%m-%d")
    today_iso_year, today_iso_week, _ = date.today().isocalendar()
    this_week_key = f"{today_iso_year}-W{today_iso_week:02d}"
    this_month_key = date.today().strftime("%Y-%m")

    col1, col2, col3 = st.columns(3)
    col1.metric("Today", format_currency_for_code(daily.get(today_key, 0.0), currency_code))
    col2.metric("This Week", format_currency_for_code(weekly.get(this_week_key, 0.0), currency_code))
    col3.metric("This Month", format_currency_for_code(monthly.get(this_month_key, 0.0), currency_code))

    st.markdown("---")
    st.subheader("Add a money win")
    threshold = min_local_amount_for_xp(currency_code)
    st.caption(
        f"XP is automatic by PPP: every {format_currency_for_code(threshold, currency_code)} saved = 10 XP."
    )

    action_labels = [f"{a['emoji']} {a['label']}" for a in ACTIONS]
    selected = st.selectbox("Quick action", action_labels, index=0)
    selected_action = ACTIONS[action_labels.index(selected)]

    amount_value = st.number_input(
        "Saved amount",
        min_value=0.0,
        value=float(local_amount_from_usd(selected_action["default_amount_usd"], currency_code)),
        step=1.0,
    )
    auto_xp = xp_from_amount(amount_value, currency_code)
    st.caption(f"Auto XP for this amount: **+{auto_xp} XP**")

    if st.button("Log action", type="primary", use_container_width=True):
        if auto_xp <= 0:
            st.warning(f"Enter at least {format_currency_for_code(threshold, currency_code)} to earn XP.")
        else:
            add_entry(data, selected_action["label"], selected_action["emoji"], amount_value, auto_xp)
            st.success(
                f"Added {selected_action['label']} • {format_currency_for_code(amount_value, currency_code)} • +{auto_xp} XP"
            )
            st.rerun()

    with st.expander("Custom action"):
        custom_label = st.text_input("Action name", placeholder="Moved spare change to investment")
        custom_amount = st.number_input(
            "Custom saved amount",
            min_value=0.0,
            value=float(threshold),
            step=1.0,
            key="custom_amount",
        )
        custom_auto_xp = xp_from_amount(custom_amount, currency_code)
        st.caption(f"Auto XP for this amount: **+{custom_auto_xp} XP**")
        if st.button("Log custom action", use_container_width=True):
            if not custom_label.strip():
                st.warning("Please enter an action name.")
            elif custom_auto_xp <= 0:
                st.warning(f"Enter at least {format_currency_for_code(threshold, currency_code)} to earn XP.")
            else:
                add_entry(data, custom_label.strip(), "✨", custom_amount, custom_auto_xp)
                st.success(
                    f"Added {custom_label.strip()} • {format_currency_for_code(custom_amount, currency_code)} • +{custom_auto_xp} XP"
                )
                st.rerun()

    st.markdown("---")
    st.subheader("Savings timeline")
    st.markdown('<div class="finance-note">Market-style savings view: track your momentum over time.</div>', unsafe_allow_html=True)
    timeline_tab_day, timeline_tab_week, timeline_tab_month = st.tabs(["Daily", "Weekly", "Monthly"])

    with timeline_tab_day:
        if daily:
            day_rows = [{"period": k, "saved": v} for k, v in sorted(daily.items())]
            st.area_chart(day_rows, x="period", y="saved")
        else:
            st.info("No entries yet. Log your first action above.")

    with timeline_tab_week:
        if weekly:
            week_rows = [{"period": k, "saved": v} for k, v in sorted(weekly.items())]
            st.line_chart(week_rows, x="period", y="saved")
        else:
            st.info("No weekly data yet.")

    with timeline_tab_month:
        if monthly:
            month_rows = [{"period": k, "saved": v} for k, v in sorted(monthly.items())]
            st.line_chart(month_rows, x="period", y="saved")
        else:
            st.info("No monthly data yet.")

    st.markdown("---")
    st.subheader("Recent activity")
    if currency_entries:
        for entry in reversed(currency_entries[-8:]):
            st.markdown(
                f"{entry['emoji']} **{entry['action']}** • {format_currency_for_code(float(entry['amount']), currency_code)} • +{entry['xp']} XP"
            )
    else:
        st.caption(f"No activity yet for {currency_code}.")

    st.markdown("---")
    st.info(f"Lifetime saved: {format_currency_for_code(total_saved, currency_code)}")

elif selected_view == "settings":
    st.subheader("Profile settings")
    st.caption("Your settings are saved for future use in Penny.")
    settings_username = st.text_input("Username", value=username, max_chars=30)
    currency_options = list(CURRENCY_SYMBOLS.keys())
    current_currency_index = currency_options.index(currency_code) if currency_code in currency_options else 0
    settings_currency = st.selectbox("Preferred currency", options=currency_options, index=current_currency_index)
    ecosystem_options = [e["name"] for e in unlocked_ecosystems]
    ecosystem_index = ecosystem_options.index(selected_ecosystem) if selected_ecosystem in ecosystem_options else 0
    settings_ecosystem = st.selectbox("Ecosystem", options=ecosystem_options, index=ecosystem_index)
    st.caption(
        f"Currency selected: {CURRENCY_NAMES.get(settings_currency, settings_currency)}. "
        "XP progression adapts using estimated purchasing power."
    )

    if st.button("Save settings", type="primary"):
        data["profile"] = {
            "username": settings_username.strip() if settings_username.strip() else "Penny User",
            "currency": settings_currency,
            "onboarded": True,
            "ecosystem": settings_ecosystem,
        }
        save_data(data)
        st.success("Settings saved.")
        st.rerun()

