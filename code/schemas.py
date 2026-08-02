from enum import Enum
from pydantic import BaseModel, Field


class ProductArea(str, Enum):
    # Claude
    CLAUDE_ACCOUNT_MANAGEMENT = "claude_account-management"
    CLAUDE_CONVERSATION_MANAGEMENT = "claude_conversation-management"
    CLAUDE_FEATURES_AND_CAPABILITIES = "claude_features-and-capabilities"
    CLAUDE_GET_STARTED = "claude_get-started-with-claude"
    CLAUDE_PERSONALIZATION_AND_SETTINGS = "claude_personalization-and-settings"
    CLAUDE_TROUBLESHOOTING = "claude_troubleshooting"
    CLAUDE_USAGE_AND_LIMITS = "claude_usage-and-limits"
    CLAUDE_AMAZON_BEDROCK = "claude_amazon-bedrock"
    CLAUDE_API_AND_CONSOLE = "claude_claude-api-and-console"
    CLAUDE_CODE = "claude_claude-code"
    CLAUDE_DESKTOP = "claude_claude-desktop"
    CLAUDE_FOR_EDUCATION = "claude_claude-for-education"
    CLAUDE_FOR_GOVERNMENT = "claude_claude-for-government"
    CLAUDE_FOR_NONPROFITS = "claude_claude-for-nonprofits"
    CLAUDE_IN_CHROME = "claude_claude-in-chrome"
    CLAUDE_MOBILE_APPS = "claude_claude-mobile-apps"
    CLAUDE_CONNECTORS = "claude_connectors"
    CLAUDE_IDENTITY_MANAGEMENT = "claude_identity-management-sso-jit-scim"
    CLAUDE_PRIVACY_AND_LEGAL = "claude_privacy-and-legal"
    CLAUDE_PRO_AND_MAX_PLANS = "claude_pro-and-max-plans"
    CLAUDE_SAFEGUARDS = "claude_safeguards"
    CLAUDE_TEAM_AND_ENTERPRISE = "claude_team-and-enterprise-plans"
    CLAUDE_GENERAL = "claude_general"

    # HackerRank
    HR_CHAKRA = "hackerrank_chakra"
    HR_ENGAGE = "hackerrank_engage"
    HR_GENERAL_HELP = "hackerrank_general-help"
    HR_COMMUNITY = "hackerrank_hackerrank_community"
    HR_INTEGRATIONS = "hackerrank_integrations"
    HR_INTERVIEWS = "hackerrank_interviews"
    HR_LIBRARY = "hackerrank_library"
    HR_SCREEN = "hackerrank_screen"
    HR_SETTINGS = "hackerrank_settings"
    HR_SKILLUP = "hackerrank_skillup"
    HR_UNCATEGORIZED = "hackerrank_uncategorized"
    HR_GENERAL = "hackerrank_general"

    # Visa
    VISA_SUPPORT = "visa_support"
    VISA_GENERAL = "visa_general"

    # Fallback
    OUT_OF_SCOPE = "out-of-scope"


class RequestType(str, Enum):
    PRODUCT_ISSUE = "product_issue"
    FEATURE_REQUEST = "feature_request"
    BUG = "bug"
    INVALID = "invalid"


class Status(str, Enum):
    REPLIED = "replied"
    ESCALATED = "escalated"


class Company(str, Enum):
    HACKERRANK = "hackerrank"
    CLAUDE = "claude"
    VISA = "visa"
    NONE = "none"


class ClassificationResult(BaseModel):
    company: Company = Field(description="Which product ecosystem this ticket belongs to")
    product_area: ProductArea = Field(description="Most specific matching category")
    request_type: RequestType
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Any risk signals detected: fraud, account_access, billing_dispute, "
                    "assessment_integrity, pii, security, legal, self_harm, adversarial_content"
    )
    reasoning: str = Field(description="Brief internal reasoning for the classification")


class TicketAnalysis(BaseModel):
    status: Status
    product_area: ProductArea
    response: str
    justification: str
    request_type: RequestType