import os
from db import get_conn, list_goals, add_goal, delete_goal

def test_add_list_delete_goal():
    # Create a test goal for a fake user
    gid = add_goal(
        user_id=9999,
        goal_title="pytest-goal",
        goal_type="steps_daily",
        target_value=1234,
        unit="steps",
        start_date="2025-01-01",
        end_date=None,
        notes=""
    )

    # Ensure an ID was returned
    assert gid is not None

    # Ensure goal appears in list
    goals = list_goals(9999)
    assert any(g["goal_title"] == "pytest-goal" for g in goals)

    # Delete the goal
    assert delete_goal(gid)

    # Ensure it's deleted
    goals = list_goals(9999)
    assert not any(g["id"] == gid for g in goals)