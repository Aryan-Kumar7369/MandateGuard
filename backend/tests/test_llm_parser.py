from app.services.llm_mandate_parser import LLMMandateParser

def test_fallback_mandate_parser():
    prompt = "Spend up to 200 on shoes"
    result = LLMMandateParser._fallback_parser(prompt)
    assert result.cumulative_budget == 200.00
    assert result.approval_threshold == 50.00
    assert "electronics" in result.allowed_categories