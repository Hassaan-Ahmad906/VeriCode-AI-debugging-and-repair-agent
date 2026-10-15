"""Explicit denominators and unresolved outcomes for independent scoring."""

def evaluation_metrics(scores: list[dict]) -> dict:
    total = len(scores)
    passed = sum(score["suite_passed"] is True for score in scores)
    failed = sum(score["suite_passed"] is False for score in scores)
    unknown = total - passed - failed
    baseline_known = [score for score in scores if score["baseline_suite_passed"] is True and score["suite_passed"] is not None]
    accepted_known = [score for score in scores if score["agent_accepted"] is True and score["suite_passed"] is not None]
    regressions = sum(score["regression"] is True for score in scores)
    overfit = sum(score["accepted_but_failed"] is True for score in scores)
    statuses = {}
    for score in scores:
        execution = score.get("candidate_execution")
        status = execution["status"] if execution else "not_submitted_or_blocked"
        statuses[status] = statuses.get(status, 0) + 1
    return {"tasks": total, "evaluation_passed": passed, "evaluation_failed": failed,
            "evaluation_unknown": unknown, "candidate_execution_statuses": statuses,
            "evaluation_pass_fraction": passed / total if total and not unknown else None,
            "observed_pass_lower_bound": passed / total if total else None,
            "observed_pass_upper_bound": (passed + unknown) / total if total else None,
            "baseline_passes_with_known_candidate": len(baseline_known), "regressions": regressions,
            "regression_fraction": regressions / len(baseline_known) if baseline_known else None,
            "accepted_with_known_evaluation": len(accepted_known), "accepted_but_failed": overfit,
            "accepted_but_failed_fraction": overfit / len(accepted_known) if accepted_known else None,
            "infrastructure_errors": sum(score["status"] == "infrastructure_error" for score in scores)}
