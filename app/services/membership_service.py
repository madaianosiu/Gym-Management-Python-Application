class MembershipService:
    @staticmethod
    def get_plans():
        return [
            {
                "id": "basic",
                "name": "Basic",
                "price": 49,
                "duration_days": 30,
                "badge": "Starter",
                "description": "A clean entry plan for members building consistency and confidence.",
                "ideal_for": "Beginners and casual training",
                "access_level": "Gym floor",
                "class_access": "No classes",
                "coach_support": "Starter guidance",
                "recovery_access": "Locker room",
                "guest_passes": 0,
                "features": [
                    "Full gym floor access",
                    "Locker room access",
                    "Basic onboarding support",
                    "Mobile member access",
                ],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 79,
                "duration_days": 30,
                "badge": "Most Popular",
                "description": "Balanced performance plan for members who train seriously every week.",
                "ideal_for": "Strength and routine-focused training",
                "access_level": "Gym + classes",
                "class_access": "Unlimited classes",
                "coach_support": "Monthly check-in",
                "recovery_access": "Sauna access",
                "guest_passes": 1,
                "features": [
                    "Everything in Basic",
                    "Unlimited group classes",
                    "Priority booking windows",
                    "Monthly progress check-in",
                ],
            },
            {
                "id": "elite",
                "name": "Elite",
                "price": 129,
                "duration_days": 30,
                "badge": "Premium",
                "description": "A premium experience with stronger support, recovery, and personal attention.",
                "ideal_for": "Advanced members and transformation goals",
                "access_level": "Full club access",
                "class_access": "Unlimited premium classes",
                "coach_support": "1-on-1 coaching",
                "recovery_access": "Premium recovery zone",
                "guest_passes": 2,
                "features": [
                    "Everything in Pro",
                    "Premium recovery zone access",
                    "1-on-1 coaching consult",
                    "VIP support and early access",
                ],
            },
        ]

    @staticmethod
    def get_plan(plan_key: str | None):
        if not plan_key:
            return None

        normalized = str(plan_key).strip().lower()
        for plan in MembershipService.get_plans():
            plan_name = str(plan.get("name", "")).strip().lower()
            plan_id = str(plan.get("id", "")).strip().lower()
            if normalized in {plan_name, plan_id}:
                return plan

        return None

    @staticmethod
    def enrich_membership(membership: dict | None):
        if not membership:
            return {}

        plan = MembershipService.get_plan(membership.get("plan_id") or membership.get("plan_name")) or {}
        enriched = dict(plan)
        enriched.update(membership)
        return enriched
