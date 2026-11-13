TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Get the user's schedule for a date (defaults to today). Use before creating or moving items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "ISO date YYYY-MM-DD. Omit for today.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_goals",
            "description": "Get monthly goals and progress for a month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "string",
                        "description": "First day of month YYYY-MM-01. Omit for current month.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_annual_goal",
            "description": "Get the active 1-year dream.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_activity",
            "description": "Recent completed, missed, and upcoming items plus daily progress.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_free_slots",
            "description": "Find free time on a date within the user's working window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "min_minutes": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_schedule_item",
            "description": "Create a calendar block. Times must be HH:MM 24-hour. Fails on overlap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_time": {"type": "string", "description": "HH:MM"},
                    "end_time": {"type": "string", "description": "HH:MM"},
                    "goal_id": {"type": "integer", "description": "Monthly goal id"},
                    "notes": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["focus", "break", "fixed", "habit", "flexible"],
                    },
                    "is_fixed": {"type": "boolean"},
                },
                "required": ["title", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_day_plan",
            "description": (
                "Atomically replace today's remaining schedule with this exact plan. "
                "Completed items are kept. Use this whenever the user approves a reschedule "
                "or pastes a full plan. Do not create/move items one-by-one for a full plan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD. Omit for today."},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "start_time": {"type": "string", "description": "HH:MM 24-hour"},
                                "end_time": {"type": "string", "description": "HH:MM 24-hour"},
                                "kind": {
                                    "type": "string",
                                    "enum": ["focus", "break", "fixed", "habit", "flexible"],
                                },
                                "goal_id": {"type": "integer"},
                                "notes": {"type": "string"},
                            },
                            "required": ["title", "start_time", "end_time"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_schedule_item",
            "description": "Update an existing schedule item by id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "goal_id": {"type": "integer"},
                    "notes": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["upcoming", "in_progress", "completed", "missed", "rescheduled"],
                    },
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_schedule_item",
            "description": "Delete a schedule item by id.",
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_schedule_item",
            "description": "Move a block to a new start/end time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["id", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": (
                "Mark a schedule item completed. Pass progress_amount when the user reports "
                "how many units they finished (e.g. 2 problems). Do not invent a number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "progress_amount": {
                        "type": "number",
                        "description": "Units to add to the linked monthly goal (problems, modules, chapters).",
                    },
                    "goal_id": {
                        "type": "integer",
                        "description": "Monthly goal to increment if the block is not already linked.",
                    },
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "increment_goal_progress",
            "description": (
                "Add units to a monthly goal (e.g. +2 NeetCode problems). "
                "Use when the user reports progress even if they do not complete a calendar block."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {"type": "integer"},
                    "amount": {"type": "number"},
                },
                "required": ["goal_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_goal",
            "description": "Create the annual dream or a monthly goal. Prefer measurable monthly goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["annual", "monthly"]},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "target_date": {"type": "string", "description": "Required for annual. YYYY-MM-DD."},
                    "metric_target": {"type": "number"},
                    "metric_unit": {"type": "string"},
                    "priority": {"type": "integer", "description": "1 highest, 5 lowest"},
                    "month": {"type": "string", "description": "YYYY-MM-01 for monthly goals"},
                },
                "required": ["level", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_goal",
            "description": "Update an annual or monthly goal, including metric_current.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["annual", "monthly"]},
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "metric_target": {"type": "number"},
                    "metric_current": {"type": "number"},
                    "metric_unit": {"type": "string"},
                    "priority": {"type": "integer"},
                    "status": {"type": "string", "enum": ["active", "completed", "paused"]},
                },
                "required": ["level", "id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_preferences",
            "description": "Save working hours, energy window, weekday shape, or blockers from onboarding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "peak_energy": {"type": "string", "enum": ["morning", "afternoon", "evening"]},
                    "typical_weekday": {"type": "string"},
                    "blockers": {"type": "string"},
                    "work_start": {"type": "string"},
                    "work_end": {"type": "string"},
                    "preferred_block_minutes": {"type": "integer"},
                    "onboarding_completed": {"type": "boolean"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_productivity_insights",
            "description": "Get computed recommendation scores and daily/monthly progress.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
