supported_platforms = ["instagram", "tiktok", "linkedin", "twitter"]

subscription_plans = {
    "tier_1": {
        "account_tracking": {
            "max_tracked_accounts": 3,
            "max_leads": 100,
        },
        "crawler": {
            "max_crawler_sessions": 5,
            "max_pages_per_crawl": 10,
            "max_depth": 3,
        },
        "contact_export": False,
    },
    "tier_2": {
        "account_tracking": {
            "max_tracked_accounts": 30,
            "max_leads": 1000,
        },
        "crawler": {
            "max_crawler_sessions": 50,
            "max_pages_per_crawl": 10,
            "max_depth": 3,
        },
        "contact_export": False,
    },
    "tier_3": {
        "max_crawler_sessions": None,
        "max_pages_per_crawl": None,
        "max_depth": None,
        "contact_export": None,
    }
}

ICPs: dict = {
    "social_savy_sdr": """
        {{
            "icp_name": "Social-Savvy SDR",
            "industry": "B2B Sales / Tech Company",
            "company_stage": "Any, ideally smaller",
            "company_size": "10–200 employees",
            "team_context": "Small sales team; every rep must maximize efficiency",
            "role_titles": [
                "Sales Development Representative",
                "Business Development Representative",
                "Account Executive (self-prospecting)"
            ],
            "work_experience": [
                "1–5 years in B2B sales or tech company",
                "Regular use of outbound prospecting tools (LinkedIn Sales Navigator, Twitter/X, Instagram)",
                "Familiarity with CRMs like Salesforce or HubSpot"
            ],
            "daily_process": [
                "Check LinkedIn, Instagram & Twitter for new engagement",
                "Manually comb competitor posts for likers & commenters",
                "Log prospects into spreadsheets or CRM",
                "Cold-call and email prospects",
                "Spends ~60% of day researching vs ~33% actively selling"
            ],
            "core_pain_points": [
                "Time-consuming manual prospecting",
                "Missing critical “intent signals” from social engagement",
                "Low response rates on purely cold outreach",
                "Daily pressure to hit pipeline quotas with limited warm leads"
            ],
            "current_workarounds": [
                "Maintain spreadsheets of competitors’ likers/commenters",
                "Use Google Alerts or basic social-listening tools (only captures mentions)",
                "Rely on cold lists and traditional outreach",
                "Drop social-media lead-hunting when slammed for time"
            ],
            "emotional_states": [
                "Stressed and anxious about meeting quotas",
                "Frustrated & FOMO—seeing competitors scoop up engaged prospects",
                "Hungry and opportunistic for any edge or efficiency gain"
            ],
            "language_phrases": [
                "pipeline",
                "lead volume",
                "MQLs/SQLs",
                "conversion rates",
                "hitting quota",
                "warm vs cold outreach",
                "I need more warm leads",
                "spending hours on LinkedIn for scraps isn’t scalable"
            ],
            "trigger_signals": [
                "“We track our competitors’ social media to find prospects.”",
                "“It takes forever to gather leads from Instagram or Twitter engagements.”",
                "“Warm leads from social convert so much better than cold calls.”",
                "“I live on LinkedIn for prospecting.”",
                "“I hate data entry and list building.”"
            ],
            "early_adopter_indicators": [
                "Already mining multiple social platforms for lead gen",
                "Comfortable testing new sales/automation tools",
                "Has closed deals originating from social media interactions",
                "Actively seeks to minimize grunt work to hit targets"
            ]
        }}
    """,
    "ICP #2": """
    """,
    "ICP #3": """
    """
}