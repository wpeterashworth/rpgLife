import math
from datetime import datetime, date, timedelta
import database as db

BASE_POINTS = {1: 10, 2: 25, 3: 50, 4: 100, 5: 200}
REWARD_COSTS = {1: 50, 2: 150, 3: 400, 4: 1000, 5: 2500}
DIFFICULTY_LABELS = {1: "Trivial", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Epic"}
DIFFICULTY_COLORS = {1: "#95A5A6", 2: "#2ECC71", 3: "#3498DB", 4: "#E67E22", 5: "#E74C3C"}

TASK_SLOT_LIMITS = {1: 3, 3: 5, 10: -1}  # level: slots (-1 = unlimited)
FEATURE_UNLOCKS = {
    "custom_categories": 3,
    "recurring_tasks": 5,
    "detailed_analytics": 10,
    "power_ups": 15,
}


def level_multiplier(level):
    return 1 + (level - 1) * 0.1


def calc_points_earned(difficulty, level):
    base = BASE_POINTS.get(difficulty, 10)
    return int(base * level_multiplier(level))


def xp_for_level(level):
    return 100 * level * level


def level_from_xp(total_xp):
    level = 1
    while xp_for_level(level) <= total_xp:
        level += 1
    return level - 1 if level > 1 else 1


def xp_progress(total_xp, level):
    current_threshold = xp_for_level(level)
    next_threshold = xp_for_level(level + 1)
    xp_into_level = total_xp - current_threshold
    xp_needed = next_threshold - current_threshold
    if xp_needed <= 0:
        return 1.0
    return max(0.0, min(1.0, xp_into_level / xp_needed))


def reward_cost(value):
    return REWARD_COSTS.get(value, 50)


def get_task_slots(level):
    slots = 3
    for lvl, s in sorted(TASK_SLOT_LIMITS.items()):
        if level >= lvl:
            slots = s
    return slots


def is_feature_unlocked(level, feature):
    required = FEATURE_UNLOCKS.get(feature, 1)
    return level >= required


def update_streak(user_id):
    stats = db.get_user_stats(user_id)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    last = stats["last_completion_date"]

    if last == today:
        return stats["current_streak"]

    if last == yesterday:
        new_streak = stats["current_streak"] + 1
    else:
        new_streak = 1

    longest = max(stats["longest_streak"], new_streak)
    db.update_user_stats(
        user_id,
        current_streak=new_streak,
        longest_streak=longest,
        last_completion_date=today,
    )
    return new_streak


def add_points(user_id, points):
    stats = db.get_user_stats(user_id)
    db.update_user_stats(user_id, available_points=stats["available_points"] + points)


def spend_points_on_xp(user_id, amount):
    stats = db.get_user_stats(user_id)
    if amount > stats["available_points"] or amount <= 0:
        return False
    new_points = stats["available_points"] - amount
    new_xp = stats["total_xp"] + amount
    new_level = level_from_xp(new_xp)
    db.update_user_stats(
        user_id,
        available_points=new_points,
        total_xp=new_xp,
        level=new_level,
    )
    db.spend_points_on_xp(user_id, amount)
    return True


def spend_points_on_reward(user_id, reward_id, cost):
    stats = db.get_user_stats(user_id)
    if cost > stats["available_points"]:
        return False
    db.update_user_stats(user_id, available_points=stats["available_points"] - cost)
    db.redeem_reward(reward_id, user_id, cost)
    return True


def check_achievements(user_id):
    stats = db.get_user_stats(user_id)
    all_achievements = db.get_all_achievements()
    unlocked = db.get_user_achievements(user_id)
    newly_unlocked = []

    total_completions = db.get_total_completions(user_id)
    max_cat = db.get_max_category_completions(user_id)
    redemptions = db.get_redemption_count(user_id)

    for ach in all_achievements:
        if ach["id"] in unlocked:
            continue

        met = False
        req_type = ach["requirement_type"]
        req_val = ach["requirement_value"]

        if req_type == "streak":
            met = stats["longest_streak"] >= req_val
        elif req_type == "tasks_completed":
            met = total_completions >= req_val
        elif req_type == "category_tasks":
            met = max_cat >= req_val
        elif req_type == "level":
            met = stats["level"] >= req_val
        elif req_type == "rewards_redeemed":
            met = redemptions >= req_val
        elif req_type == "points_saved":
            met = stats["available_points"] >= req_val

        if met:
            if db.unlock_achievement(user_id, ach["id"]):
                newly_unlocked.append(ach)

    return newly_unlocked


def get_achievement_progress(user_id):
    stats = db.get_user_stats(user_id)
    total_completions = db.get_total_completions(user_id)
    max_cat = db.get_max_category_completions(user_id)
    redemptions = db.get_redemption_count(user_id)

    def _progress(req_type, req_val):
        if req_type == "streak":
            return min(1.0, stats["longest_streak"] / req_val)
        elif req_type == "tasks_completed":
            return min(1.0, total_completions / req_val)
        elif req_type == "category_tasks":
            return min(1.0, max_cat / req_val)
        elif req_type == "level":
            return min(1.0, stats["level"] / req_val)
        elif req_type == "rewards_redeemed":
            return min(1.0, redemptions / req_val)
        elif req_type == "points_saved":
            return min(1.0, stats["available_points"] / req_val)
        return 0.0

    return _progress
