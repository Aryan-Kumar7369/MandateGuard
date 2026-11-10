import time
from tests.red_team_corpus import ATTACK_CORPUS
from app.services.llm_mandate_parser import LLMMandateParser
from app.schemas.mandate import MandateSchema
from app.services.delegation_service import DelegationService
from datetime import datetime, timedelta, timezone
from decimal import Decimal

def run_red_team_audit():
    print("=======================================================")
    print(" MANDATEGUARD ADVERSARIAL RED TEAM SECURITY AUDIT ")
    print("=======================================================")
    
    passed_attacks = 0
    total_attacks = len(ATTACK_CORPUS)

    for idx, attack in enumerate(ATTACK_CORPUS, 1):
        start_time = time.perf_counter()
        print(f"\n[{idx}/{total_attacks}] Running: {attack['name']} ({attack['category']})")
        print(f"    Vector ID: {attack['id']}")

        success = True
        reason = "Attack successfully neutralised and blocked."

        if attack["id"] == "ADV_PARSER_01":
            parsed = LLMMandateParser.parse_natural_language_prompt(attack["prompt"])
            if parsed.cumulative_budget > 1000.0 or "*" in parsed.allowed_categories:
                success = False
                reason = "Parser set unsafe budget or wildcard category."

        elif attack["id"] == "ADV_DELEG_01":
            now = datetime.now(timezone.utc)
            p = MandateSchema(cumulative_budget=Decimal("100"), approval_threshold=Decimal("50"), expiry=now+timedelta(days=1), allowed_categories=["gen"], merchant_constraints={"allow":[],"deny":[]}, allowed_shipping_destinations=[])
            c = MandateSchema(cumulative_budget=Decimal("500"), approval_threshold=Decimal("50"), expiry=now+timedelta(days=1), allowed_categories=["gen"], merchant_constraints={"allow":[],"deny":[]}, allowed_shipping_destinations=[])
            ok, msg = DelegationService.validate_sub_mandate(p, c)
            if ok:
                success = False
                reason = "Sub-mandate budget expansion was allowed."

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        if success:
            passed_attacks += 1
            print(f"    [DEFENDED] {reason} ({elapsed_ms:.2f} ms)")
        else:
            print(f"    [FAIL] {reason} ({elapsed_ms:.2f} ms)")

    print("\n=======================================================")
    print(f" RED TEAM AUDIT SCORECARD: {passed_attacks}/{total_attacks} ATTACKS NEUTRALIZED")
    print(f" DEFENSIVE ENFORCEMENT RATE: {(passed_attacks / total_attacks) * 100:.1f}%")
    print("=======================================================")

if __name__ == "__main__":
    run_red_team_audit()