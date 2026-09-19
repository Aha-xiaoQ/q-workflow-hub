"""Behavior scenarios: policy advice is not an authorization engine."""
import copy
import itertools
import unittest
from execution_policy import advise


def scenario(**updates):
    facts = dict(intent="change", risk="low", claim="local", authority="in-scope",
                 evidence="not-run", decision_missing=False, pending_tools=False,
                 unresolved_concerns=False, independent_work=False,
                 useful_main_work=False, delegation_permitted=False,
                 delegation_available=False, review_required=False,
                 monitor_available=False)
    facts.update(updates)
    return facts


class ExecutionPolicyTests(unittest.TestCase):
    def test_authorized_small_fix_does_not_ask(self):
        r = advise(scenario())
        self.assertEqual(r["next_action"], "implement-in-scope")
        self.assertEqual(r["test_tier"], "T1")

    def test_side_question_is_read_only(self):
        for intent in ("answer", "diagnose"):
            r = advise(scenario(intent=intent))
            self.assertEqual(r["next_action"], "inspect-read-only")
            self.assertEqual(r["requested_mode"], "no-artifact-mutation")

    def test_latest_no_push_dominates_pass(self):
        r = advise(scenario(claim="release", authority="denied", evidence="pass"))
        self.assertEqual(r["next_action"], "stop-out-of-scope")

    def test_material_missing_choice_asks(self):
        self.assertEqual(advise(scenario(decision_missing=True))["next_action"], "ask-focused-question")

    def test_pending_async_result_is_not_completion(self):
        self.assertEqual(advise(scenario(evidence="pass", pending_tools=True))["next_action"], "reconcile-pending-tools")

    def test_fresh_sufficient_checks_stop(self):
        r = advise(scenario(evidence="pass"))
        self.assertEqual(r["next_action"], "handoff-with-evidence")
        self.assertFalse(r["repeat_checks"])

    def test_changed_scope_invalidates_test_evidence(self):
        r = advise(scenario(evidence="stale"))
        self.assertEqual(r["next_action"], "targeted-validation-or-repair")
        self.assertTrue(r["repeat_checks"])

    def test_failed_tests_cannot_handoff(self):
        self.assertNotEqual(advise(scenario(evidence="fail"))["next_action"], "handoff-with-evidence")

    def test_failed_diagnosis_does_not_suggest_repair(self):
        for intent in ("answer", "diagnose"):
            self.assertEqual(advise(scenario(intent=intent, evidence="fail"))["next_action"], "targeted-read-only-validation")

    def test_denied_action_does_not_suggest_child(self):
        self.assertNotEqual(advise(scenario(authority="denied", independent_work=True,
                                           useful_main_work=True, delegation_permitted=True,
                                           delegation_available=True))["delegation"], "bounded-child")

    def test_independent_review_cannot_be_skipped(self):
        r = advise(scenario(evidence="pass", review_required=True))
        self.assertEqual(r["next_action"], "complete-independent-review")
        self.assertEqual(r["delegation"], "review-needed")

    def test_monitor_uses_host_mechanism_or_reports_gap(self):
        self.assertEqual(advise(scenario(intent="monitor", monitor_available=True))["next_action"], "use-native-monitor")
        self.assertEqual(advise(scenario(intent="monitor"))["next_action"], "report-capability-gap")

    def test_claim_drives_validation_scope(self):
        for claim, tier in [("local", "T1"), ("mirror", "T2"), ("remote-rebuild", "T3"), ("release", "T4")]:
            self.assertEqual(advise(scenario(claim=claim))["test_tier"], tier)

    def test_local_risk_does_not_invent_workflow_mirrors(self):
        for risk in ("material", "high"):
            r = advise(scenario(risk=risk))
            self.assertEqual(r["test_tier"], "T1")
            self.assertEqual(r["next_action"], "implement-in-scope")
            self.assertEqual(advise(scenario(risk=risk, claim="mirror"))["test_tier"], "T2")

    def test_authorized_release_keeps_review_without_reapproval(self):
        facts = scenario(claim="release", evidence="pass", review_required=True)
        self.assertEqual(advise(facts)["next_action"], "complete-independent-review")
        facts["review_required"] = False
        result = advise(facts)
        self.assertEqual(result["next_action"], "handoff-with-evidence")
        self.assertFalse(result["grants_authority"])
        facts["authority"] = "denied"
        self.assertEqual(advise(facts)["next_action"], "stop-out-of-scope")

    def test_delegation_requires_all_four_conditions(self):
        for values in itertools.product((False, True), repeat=4):
            f = scenario(**dict(zip(("independent_work", "useful_main_work", "delegation_permitted", "delegation_available"), values)))
            self.assertEqual(advise(f)["delegation"] == "bounded-child", all(values))

    def test_never_grants_authority_across_input_matrix(self):
        for authority, evidence, pending in itertools.product(("denied", "missing", "in-scope"), ("pass", "fail", "stale", "not-run"), (False, True)):
            r = advise(scenario(authority=authority, evidence=evidence, pending_tools=pending))
            self.assertFalse(r["grants_authority"])
            self.assertFalse(r["promotion_eligible"])
            if authority != "in-scope" or pending or evidence != "pass":
                self.assertNotEqual(r["next_action"], "handoff-with-evidence")

    def test_missing_and_wrong_types_fail_closed(self):
        for value in [None, [], {}, scenario(authority="approved-ish"), scenario(pending_tools="false"), scenario(pending_tools=0), scenario(intent=[]), scenario(extra=True)]:
            self.assertEqual(advise(value)["status"], "needs-context")

    def test_deterministic_and_no_input_mutation(self):
        facts = scenario()
        before = copy.deepcopy(facts)
        self.assertEqual(advise(facts), advise(facts))
        self.assertEqual(facts, before)


if __name__ == "__main__":
    unittest.main()
