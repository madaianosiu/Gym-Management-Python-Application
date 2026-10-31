import os
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AICoachService:
    SCOPE_KEYWORDS = [
        "gym", "fitness", "workout", "training", "exercise", "cardio", "strength", "muscle", "protein",
        "calorie", "calories", "meal", "meals", "nutrition", "diet", "food", "macros", "supplement",
        "recovery", "sleep", "weight", "fat", "bulk", "cut", "health", "wellness", "motivation",
        "plan", "program", "routine", "week", "weekly", "schedule", "coach", "goal",
        "sala", "antrenament", "antrenez", "exercitii", "masa", "slabire", "proteine", "calorii",
        "nutritie", "dieta", "mancare", "suplimente", "recuperare", "somn", "greutate", "sanatate",
        "saptamana", "programare", "obiectiv",
    ]
    OUT_OF_SCOPE_KEYWORDS = [
        "python", "javascript", "java", "html", "css", "code", "coding", "programming", "script",
        "homework", "essay", "politics", "election", "finance", "stock", "crypto", "travel",
        "movie", "game", "recipe for cake", "weather", "history of", "write me an email",
        "cod", "programare in", "tema", "politica", "alegeri", "bursa", "actiuni", "crypto",
    ]

    GOAL_ALIASES = {
        "weight_loss": ["slabire", "slăbire", "lose weight", "weight loss", "fat loss", "cut", "cutting", "deficit"],
        "muscle_gain": ["masa", "masă", "muscle", "bulk", "bulking", "gain muscle", "hypertrophy"],
        "maintenance": ["maintain", "mentinere", "menținere", "recomp", "balance"],
    }

    @staticmethod
    def _safe_float(value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _goal_from_text(text: str):
        normalized = (text or "").lower()
        for goal, aliases in AICoachService.GOAL_ALIASES.items():
            if any(alias in normalized for alias in aliases):
                return goal
        return None

    @staticmethod
    def _parse_days(text: str):
        match = re.search(r"(\d+)\s*(days|day|zile|zi|times|ori)", text.lower())
        if not match:
            return None
        value = int(match.group(1))
        return value if 1 <= value <= 7 else None

    @staticmethod
    def _is_in_scope(message: str):
        normalized = (message or "").lower()
        return any(keyword in normalized for keyword in AICoachService.SCOPE_KEYWORDS)

    @staticmethod
    def _is_clearly_out_of_scope(message: str):
        normalized = (message or "").lower()
        return any(keyword in normalized for keyword in AICoachService.OUT_OF_SCOPE_KEYWORDS)

    @staticmethod
    def _extract_profile_updates(message: str, existing: dict | None = None):
        existing = existing or {}
        normalized = (message or "").lower().replace(",", ".")
        updates = {}

        weight_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*(kg|kilograms|kilogram)", normalized)
        if weight_match:
            updates["weight_kg"] = float(weight_match.group(1))

        height_match = re.search(r"(\d{3}(?:\.\d+)?)\s*(cm|centimeters|centimetres)", normalized)
        if height_match:
            updates["height_cm"] = float(height_match.group(1))
        else:
            meters_match = re.search(r"(\d\.\d{1,2})\s*(m|meters|metres)", normalized)
            if meters_match:
                updates["height_cm"] = float(meters_match.group(1)) * 100

        goal = AICoachService._goal_from_text(normalized)
        if goal:
            updates["goal"] = goal

        days = AICoachService._parse_days(normalized)
        if days:
            updates["training_days"] = days

        if "beginner" in normalized or "incepator" in normalized or "începător" in normalized:
            updates["level"] = "beginner"
        elif "intermediate" in normalized or "mediu" in normalized:
            updates["level"] = "intermediate"
        elif "advanced" in normalized or "avansat" in normalized:
            updates["level"] = "advanced"

        merged = {**existing, **updates}
        return updates, merged

    @staticmethod
    def _protein_range(weight_kg: float | None, goal: str | None):
        if not weight_kg:
            return None

        if goal == "weight_loss":
            return round(weight_kg * 1.8), round(weight_kg * 2.2)
        if goal == "muscle_gain":
            return round(weight_kg * 1.8), round(weight_kg * 2.1)
        return round(weight_kg * 1.6), round(weight_kg * 2.0)

    @staticmethod
    def _calorie_hint(weight_kg: float | None, height_cm: float | None, goal: str | None, training_days: int | None):
        if not weight_kg or not height_cm:
            return None

        activity_bonus = (training_days or 3) * 55
        maintenance = int(weight_kg * 30 + activity_bonus + (height_cm - 160) * 4)

        if goal == "weight_loss":
            return max(maintenance - 350, 1400), "gentle deficit"
        if goal == "muscle_gain":
            return maintenance + 220, "small surplus"
        return maintenance, "maintenance"

    @staticmethod
    def _goal_label(goal: str | None):
        labels = {
            "weight_loss": "weight loss",
            "muscle_gain": "muscle gain",
            "maintenance": "maintenance",
        }
        return labels.get(goal or "", "general fitness")

    @staticmethod
    def _meal_ideas(goal: str | None):
        if goal == "weight_loss":
            return [
                "Greek yogurt, berries, and oats for breakfast",
                "Chicken rice bowl with greens and a light yogurt sauce",
                "Salmon, potatoes, and a big salad for dinner",
                "Protein shake plus fruit after training",
            ]
        if goal == "muscle_gain":
            return [
                "Eggs, toast, avocado, and a protein yogurt breakfast",
                "Lean beef, rice, and vegetables for lunch",
                "Pasta with chicken, olive oil, and parmesan after training",
                "Milk, banana, oats, and whey shake as a calorie-dense snack",
            ]
        return [
            "Eggs with toast and fruit in the morning",
            "Turkey wrap with vegetables at lunch",
            "Rice, chicken, and mixed greens for dinner",
            "A protein shake or cottage cheese snack between meals",
        ]

    @staticmethod
    def _weekly_plan(goal: str | None, training_days: int | None, level: str | None):
        days = training_days or 3
        if days <= 3:
            return [
                "Day 1: Full body strength",
                "Day 2: Lower body + core",
                "Day 3: Upper body + conditioning",
            ]
        if days == 4:
            return [
                "Day 1: Upper body",
                "Day 2: Lower body",
                "Day 3: Push focus",
                "Day 4: Pull focus + core",
            ]
        return [
            "Day 1: Push",
            "Day 2: Pull",
            "Day 3: Legs",
            "Day 4: Upper pump + cardio",
            "Day 5: Lower body + abs",
        ]

    @staticmethod
    def _yearly_plan(weight_kg: float, height_cm: float, goal: str | None, training_days: int | None):
        goal_label = AICoachService._goal_label(goal)
        days = training_days or 3
        return "\n".join(
            [
                f"Yes. For a full year, I would split your {goal_label} plan into phases instead of repeating the same week forever.",
                "",
                "Months 1-3: Foundation",
                f"- Train {days} days per week with full-body or upper/lower sessions.",
                "- Learn clean technique, build consistency, and keep 2-3 reps in reserve on most sets.",
                "- Track body weight, energy, sleep, and gym performance weekly.",
                "",
                "Months 4-6: Progressive strength",
                "- Add weight or reps slowly on your main lifts every 1-2 weeks.",
                "- Keep cardio easy/moderate 2 times per week if fat loss is still the goal.",
                "- Take 1 lighter deload week every 6-8 weeks.",
                "",
                "Months 7-9: Muscle and conditioning",
                "- Add more volume for weak areas: shoulders, back, glutes, legs, or core.",
                "- Use 8-12 reps for most muscle-building work and 12-20 reps for accessories.",
                "- Keep protein high and adjust calories based on progress.",
                "",
                "Months 10-12: Refinement",
                "- Keep the exercises that worked best and remove what did not help.",
                "- Push performance for 3 weeks, then use 1 easier week.",
                "- Take progress photos, measurements, and strength notes before planning the next year.",
                "",
                f"For your current stats ({int(weight_kg)} kg, {int(height_cm)} cm), start with a simple first month before making it more advanced.",
            ]
        )

    @staticmethod
    def _detailed_weekly_plan(
        weight_kg: float,
        height_cm: float,
        goal: str | None,
        training_days: int | None,
        level: str | None,
    ):
        days = training_days or 3
        protein_range = AICoachService._protein_range(weight_kg, goal)
        calorie_hint = AICoachService._calorie_hint(weight_kg, height_cm, goal, days)
        plan = AICoachService._weekly_plan(goal, days, level)

        lines = [
            "Absolutely. Here is a more detailed version for this week:",
            "",
        ]
        for item in plan:
            lines.append(item)
            lines.append("- Warm-up: 5-8 minutes easy cardio + 2 light sets for the first exercise.")
            lines.append("- Main work: 3-4 exercises, 3 sets each, 8-12 reps.")
            lines.append("- Finish: 8-12 minutes easy cardio or core work.")
            lines.append("- Effort: stop with 1-3 reps left in the tank.")
            lines.append("")

        if protein_range:
            lines.append(f"Protein target: {protein_range[0]}-{protein_range[1]} g per day.")
        if calorie_hint:
            calories, mode = calorie_hint
            lines.append(f"Calories: start around {calories} kcal/day using a {mode} approach.")

        lines.extend(
            [
                "",
                "Recovery rules:",
                "- Sleep 7-9 hours when possible.",
                "- Rest at least 1 day after hard lower-body work.",
                "- If a joint hurts sharply, stop that exercise and switch to a pain-free version.",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def build_response(message: str, ai_profile: dict | None = None, conversation_history: list[dict] | None = None):
        ai_profile = ai_profile or {}
        conversation_history = conversation_history or []
        updates, merged = AICoachService._extract_profile_updates(message, ai_profile)

        if (
            AICoachService._is_clearly_out_of_scope(message)
            and not AICoachService._is_in_scope(message)
            and not updates
        ):
            return {
                "reply": (
                    "I can help with gym training, fitness, nutrition, recovery, habits, and general wellness. "
                    "Ask me about workouts, meal ideas, calories, protein, weight loss, muscle gain, or recovery."
                ),
                "profile": merged,
            }

        ai_reply = AICoachService._build_openai_response(message, merged, updates, conversation_history)
        if ai_reply:
            return {"reply": ai_reply, "profile": merged}

        return AICoachService._build_rule_based_response(message, merged, updates, conversation_history)

    @staticmethod
    def _build_openai_response(
        message: str,
        ai_profile: dict,
        updates: dict | None = None,
        conversation_history: list[dict] | None = None,
    ):
        if os.getenv("AI_ENABLED", "0") != "1":
            return None

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or OpenAI is None:
            return None

        model = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
        updates = updates or {}

        profile_summary = {
            "weight_kg": ai_profile.get("weight_kg"),
            "height_cm": ai_profile.get("height_cm"),
            "goal": ai_profile.get("goal"),
            "training_days": ai_profile.get("training_days"),
            "level": ai_profile.get("level"),
            "newly_saved_fields": sorted(updates.keys()),
        }
        recent_messages = conversation_history[-10:] if conversation_history else []

        instructions = (
            "You are the GYM+ AI Coach inside a gym membership web app. "
            "Only answer questions related to gym training, fitness, nutrition, recovery, habits, "
            "body composition, supplements, motivation, and general wellness. "
            "Because the user is chatting inside an AI Coach panel, treat short or ambiguous requests "
            "like 'make me a plan', 'what should I do this week', or 'help me improve' as fitness and wellness requests. "
            "If the user asks about anything outside that scope, politely say that you can only help "
            "with gym, fitness, nutrition, and wellness topics, then invite them to ask a related question. "
            "Do not answer unrelated topics such as coding, school homework, finance, politics, travel, "
            "entertainment, or general trivia. "
            "Give practical, friendly fitness guidance in the user's language. "
            "Use the recent conversation to understand follow-up messages like 'and for a year?', "
            "'yes please', 'more details', or 'make it harder'. Do not restart the same answer when the user asks a follow-up. "
            "Use the saved profile when available. If important details are missing, ask for them, "
            "but still give a useful next step. Keep answers concise, structured, and motivating. "
            "Do not claim to diagnose or treat medical conditions. For injuries, pregnancy, eating disorders, "
            "or medical issues, recommend speaking with a qualified professional. "
            "Use kg, cm, days per week, calories, and grams of protein when relevant."
        )

        prompt = (
            "Saved coach profile:\n"
            f"{profile_summary}\n\n"
            "Recent conversation:\n"
            f"{recent_messages}\n\n"
            "Customer message:\n"
            f"{message}"
        )

        try:
            client = OpenAI(api_key=api_key, timeout=20)
            response = client.responses.create(
                model=model,
                instructions=instructions,
                input=prompt,
                max_output_tokens=700,
            )
            return (response.output_text or "").strip() or None
        except Exception:
            return None

    @staticmethod
    def _build_rule_based_response(
        message: str,
        merged: dict,
        updates: dict | None = None,
        conversation_history: list[dict] | None = None,
    ):
        updates = updates or {}
        conversation_history = conversation_history or []
        goal = merged.get("goal")
        weight_kg = AICoachService._safe_float(merged.get("weight_kg"))
        height_cm = AICoachService._safe_float(merged.get("height_cm"))
        training_days = int(merged.get("training_days") or 0) or None
        level = merged.get("level")

        lower_message = (message or "").lower()
        wants_meals = any(token in lower_message for token in ["meal", "meals", "mese", "food", "macros", "protein"])
        wants_plan = any(token in lower_message for token in ["plan", "workout", "program", "training", "antren"])
        wants_year = any(token in lower_message for token in ["year", "annual", "12 months", "an intreg", "un an"])
        wants_more_detail = any(token in lower_message for token in ["more details", "detail", "yes please", "explain", "more", "mai detaliat"])

        if not goal and any(token in lower_message for token in ["slabire", "slăbire", "masa", "masă", "lose", "muscle"]):
            goal = AICoachService._goal_from_text(lower_message)
            merged["goal"] = goal

        missing = []
        if not weight_kg:
            missing.append("weight in kg")
        if not height_cm:
            missing.append("height in cm")

        intro_bits = []
        if updates:
            tracked = []
            if "weight_kg" in updates:
                tracked.append(f"{int(updates['weight_kg'])} kg")
            if "height_cm" in updates:
                tracked.append(f"{int(updates['height_cm'])} cm")
            if "goal" in updates:
                tracked.append(AICoachService._goal_label(updates["goal"]))
            if "training_days" in updates:
                tracked.append(f"{updates['training_days']} training days")
            if tracked:
                intro_bits.append("I saved " + ", ".join(tracked) + " for your coach profile.")

        if missing:
            response = " ".join(intro_bits) + (" " if intro_bits else "")
            missing_text = missing[0] if len(missing) == 1 else ", ".join(missing[:-1]) + f", and {missing[-1]}"
            response += "I can make this much more personal. Send me your " + missing_text + "."
            response += " For example: `I want weight loss, I am 82 kg, 176 cm, and I train 4 days.`"
            return {"reply": response, "profile": merged}

        if wants_year:
            return {
                "reply": AICoachService._yearly_plan(weight_kg, height_cm, goal, training_days),
                "profile": merged,
            }

        if wants_more_detail and conversation_history:
            return {
                "reply": AICoachService._detailed_weekly_plan(weight_kg, height_cm, goal, training_days, level),
                "profile": merged,
            }

        protein_range = AICoachService._protein_range(weight_kg, goal)
        calorie_hint = AICoachService._calorie_hint(weight_kg, height_cm, goal, training_days)
        meal_ideas = AICoachService._meal_ideas(goal)
        weekly_plan = AICoachService._weekly_plan(goal, training_days, level)

        lines = []
        if intro_bits:
            lines.extend(intro_bits)

        lines.append(
            f"Based on {int(weight_kg)} kg, {int(height_cm)} cm, and a {AICoachService._goal_label(goal)} goal, here is your first coach recommendation:"
        )

        if protein_range:
            lines.append(f"Protein target: about {protein_range[0]}-{protein_range[1]} g per day.")

        if calorie_hint:
            calories, mode = calorie_hint
            lines.append(f"Calories: start around {calories} kcal/day with a {mode} approach and adjust based on progress.")

        if wants_meals or ("protein" in lower_message) or ("meal" in lower_message) or ("mese" in lower_message):
            lines.append("Meal ideas:")
            lines.extend(f"- {idea}" for idea in meal_ideas)

        if wants_plan or not wants_meals:
            lines.append("Weekly training direction:")
            lines.extend(f"- {item}" for item in weekly_plan)

        lines.append("If you want, next I can build a stricter meal day, a 7-day workout split, or a fat-loss version with exact meal structure.")

        return {"reply": "\n".join(lines), "profile": merged}
