import re

RISK_PATTERNS: dict[str, list[str]] = {
    "fraud_or_security": [
        r"\bfraud\b", r"\bunauthorized (charge|transaction|access|login)\b",
        r"\bhack(ed|er)?\b", r"\bstolen\b", r"\bphish(ing)?\b",
        r"\bcompromised\b", r"\bsuspicious (activity|login|transaction)\b",
        r"\bidentity theft\b",
    ],
    "account_access": [
        r"\bcan'?t log ?in\b", r"\blocked out\b", r"\breset my password\b.*\burgent\b",
        r"\btwo.?factor\b.*\b(lost|broken|removed)\b", r"\baccount (suspended|banned|disabled)\b",
        r"\bdelete my account\b", r"\bclose my account\b",
    ],
    "billing_dispute": [
        r"\brefund\b", r"\bdispute(d)? (charge|transaction|billing)\b",
        r"\bcharged twice\b", r"\bcancel.*(subscription|charge)\b.*\bnot\b",
        r"\bunexpected charge\b", r"\bchargeback\b",
    ],
    "assessment_integrity": [
        r"\bcheat(ing)?\b", r"\bproctor(ing)?\b.*\b(fail|flag|issue)\b",
        r"\btest (result|score) (wrong|incorrect|disputed)\b",
        r"\bplagiar\w*\b", r"\bexam (violation|integrity)\b",
    ],
    "pii_or_legal": [
        r"\bssn\b", r"\bsocial security\b", r"\bpassport number\b",
        r"\bgdpr\b", r"\blawsuit\b", r"\blegal action\b", r"\bsubpoena\b",
        r"\bdata breach\b",
    ],
    "self_harm_or_crisis": [
        r"\bsuicid\w*\b", r"\bself.?harm\b", r"\bkill myself\b",
        r"\bhurt myself\b", r"\bwant to die\b",
    ],
    "adversarial_content": [
        r"\bignore (previous|all) instructions\b", r"\bsystem prompt\b",
        r"\byou are now\b", r"\bact as\b.*\b(dan|jailbreak)\b",
        r"\bpretend (you|to) (are|be)\b",
    ],
}

def assess_risk(text: str) -> list[str]:
    text_lower = text.lower()
    triggered = []
    for category, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                triggered.append(category)
                break
    return triggered

def should_force_escalate(text: str) -> tuple[bool, list[str]]:
    flags = assess_risk(text)
    hard_escalate_categories = {
        "fraud_or_security", "pii_or_legal", "self_harm_or_crisis",
        "adversarial_content", "assessment_integrity",
    }
    force = any(f in hard_escalate_categories for f in flags)
    return force, flags