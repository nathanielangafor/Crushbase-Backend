supported_platforms = ["instagram", "tiktok", "linkedin", "twitter/x", "facebook"]

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
    "sales_development_rep": """
        {{
            "icp_name": "Sales Development Rep (SDR)",
            "industry": "B2B SaaS / Tech / Services",
            "company_stage": "Seed to Series B",
            "company_size": "10–500 employees",
            "team_context": "Part of a small-to-mid sales team, focused on pipeline generation",
            "role_titles": [
                "Sales Development Representative",
                "Business Development Representative",
                "Outbound Sales Rep"
            ],
            "work_experience": [
                "0–5 years in tech sales",
                "Uses outbound prospecting tools like Outreach, Apollo, or LinkedIn",
                "Enters leads into CRMs like HubSpot or Salesforce"
            ],
            "daily_process": [
                "Research target accounts and decision-makers",
                "Send cold emails or LinkedIn messages",
                "Follow up with warm leads",
                "Log activities into CRM",
                "Sometimes scroll social media for clues or engagement signals"
            ],
            "core_pain_points": [
                "Wasting time on poor-fit prospects",
                "Hard to identify real buyer intent",
                "Cold outreach has low conversion",
                "Manual research slows down volume goals"
            ],
            "current_workarounds": [
                "Scrape LinkedIn comments for prospects",
                "Use Excel to track interested leads",
                "Manually monitor competitor social posts"
            ],
            "emotional_states": [
                "Stressed about quota and rejection",
                "Time-starved, wants to focus on what works",
                "Hungry for tools that improve reply rate and warm lead volume"
            ],
            "language_phrases": [
                "I need more warm leads",
                "my outreach isn’t landing",
                "qualified pipeline",
                "who’s actually interested?",
                "this list is ice cold"
            ],
            "trigger_signals": [
                "“We spend hours researching before sending one message.”",
                "“Engaged leads convert better, but they’re hard to find.”",
                "“Most of my day is just list building.”"
            ],
            "early_adopter_indicators": [
                "Open to tools that boost prospecting efficiency",
                "Already experimenting with social data",
                "Driven by metrics: reply rate, meetings booked, pipeline generated"
            ]
        }}
    """,

    "bootstrapped_founder": """
        {{
            "icp_name": "Bootstrapped Founder",
            "industry": "SaaS / Creator Economy / Online Services",
            "company_stage": "Pre-seed to Series A",
            "company_size": "1–10 employees",
            "team_context": "Tiny or solo team juggling product, marketing, and growth",
            "role_titles": [
                "Founder",
                "Solo SaaS Builder",
                "Indie Hacker",
                "Technical Cofounder"
            ],
            "work_experience": [
                "Built and shipped at least one product or MVP",
                "Runs lean and relies on low-cost growth methods",
                "Active on X/Twitter, LinkedIn, Reddit to drive attention"
            ],
            "daily_process": [
                "Post product updates or share wins on social",
                "Search X/Twitter for competitor mentions",
                "Cold DM users who engage with similar products",
                "Juggle between shipping features and finding users"
            ],
            "core_pain_points": [
                "Growth feels like shouting into the void",
                "Social engagement doesn’t turn into users",
                "No time to consistently do outreach",
                "Hard to identify who’s actually interested"
            ],
            "current_workarounds": [
                "Manually message people who like competitor tweets",
                "Scrape engagement from posts using scripts or Zapier",
                "Pray for virality after posting product launches"
            ],
            "emotional_states": [
                "Exhausted from doing everything alone",
                "Hyper-aware of burn rate and traction pressure",
                "Craving validation and growth breakthroughs"
            ],
            "language_phrases": [
                "traction",
                "bootstrapped",
                "getting early users",
                "distribution is harder than building",
                "how do I convert interest into users?"
            ],
            "trigger_signals": [
                "“People liked our launch post but didn’t sign up.”",
                "“I can’t tell who’s actually serious about using our tool.”",
                "“Growth is slow even with good engagement.”"
            ],
            "early_adopter_indicators": [
                "Technical enough to value automation",
                "Already tried scraping social engagement",
                "Willing to test new tools for growth leverage"
            ]
        }}
    """,

    "content_creator": """
        {{
            "icp_name": "Content Creator",
            "industry": "Media / Education / Creator Economy",
            "company_stage": "Growing audience",
            "company_size": "1–5 (typically solo)",
            "team_context": "Runs own brand or small team; responsible for growth and monetization",
            "role_titles": [
                "Influencer",
                "Newsletter Author",
                "YouTuber",
                "TikToker",
                "Podcaster"
            ],
            "work_experience": [
                "Built an audience on at least one social platform",
                "Monetizes via brand deals, courses, subscriptions, or product links",
                "Engages with audience daily via posts, comments, or DMs"
            ],
            "daily_process": [
                "Post new content to social platforms",
                "Respond to top DMs and comments",
                "Track engagement and mentions",
                "Negotiate brand deals or promote products",
                "Manually check for potential business opportunities in replies"
            ],
            "core_pain_points": [
                "Hard to identify serious fans or buyers",
                "Overwhelmed by comments, likes, and DMs",
                "Miss out on collabs or deal requests buried in engagement",
                "Managing everything manually across platforms"
            ],
            "current_workarounds": [
                "Use spreadsheets to track high-value followers",
                "Rely on gut feeling or followers’ message tone",
                "Use VA or assistant to help sift through engagement"
            ],
            "emotional_states": [
                "Stressed by constant notifications",
                "Excited about growth but unsure how to capitalize",
                "Burned out from low ROI on high effort"
            ],
            "language_phrases": [
                "my DMs are a mess",
                "need to monetize my audience",
                "I’m missing deals",
                "engagement is high, conversions are low"
            ],
            "trigger_signals": [
                "“I have viral posts but don’t know who’s serious.”",
                "“People comment but don’t follow through.”",
                "“I miss business leads in the noise.”"
            ],
            "early_adopter_indicators": [
                "Comfortable with tools and automations",
                "Already trying to improve monetization",
                "Engagement >10% per post or >5k followers"
            ]
        }}
    """,

    "athlete": """
        {{
            "icp_name": "Athlete",
            "industry": "Sports / Fitness / Health & Wellness",
            "company_stage": "Active or transitioning to business",
            "company_size": "1–10 (often solo brand)",
            "team_context": "May be part of a team, brand, or operate independently as a personal brand",
            "role_titles": [
                "Professional Athlete",
                "Collegiate Athlete",
                "Fitness Coach",
                "Sports Influencer",
                "Personal Trainer"
            ],
            "work_experience": [
                "Competes or trains professionally or semi-professionally",
                "Maintains a public persona on Instagram, TikTok, or YouTube",
                "Monetizes through sponsorships, coaching, merch, or brand deals"
            ],
            "daily_process": [
                "Train or compete in their sport",
                "Post training clips, game highlights, or fitness content",
                "Engage with fans and sponsors on social",
                "Manage sponsorships, coaching clients, or merchandise drops",
                "Look for collaboration or growth opportunities"
            ],
            "core_pain_points": [
                "Hard to track who’s genuinely interested in working with them",
                "DMs filled with noise and fake opportunities",
                "Missing brand deals or high-value fans",
                "No system to turn engagement into partnerships or income"
            ],
            "current_workarounds": [
                "Manually respond to comments and filter DMs",
                "Use agent/manager or handle everything solo",
                "Scroll for hours to find opportunities hidden in replies"
            ],
            "emotional_states": [
                "Laser-focused on performance",
                "Excited but overwhelmed by digital attention",
                "Wants to build a business off the field but lacks tools"
            ],
            "language_phrases": [
                "serious collabs only",
                "brand partnership",
                "online coaching clients",
                "grow my personal brand",
                "turn followers into clients"
            ],
            "trigger_signals": [
                "“My inbox is full but nothing converts.”",
                "“People ask about coaching but ghost after.”",
                "“I want to work with serious brands.”"
            ],
            "early_adopter_indicators": [
                "Has >2k engaged followers",
                "Already monetizing through any channel",
                "Comfortable with new tools if results are clear"
            ]
        }}
    """,

    "job_seeker": """
        {{
            "icp_name": "Job Seeker",
            "industry": "Any industry",
            "company_stage": "Not currently employed or seeking transition",
            "company_size": "N/A",
            "team_context": "Operates independently; may be part of online communities or alumni groups",
            "role_titles": [
                "Any role"
            ],
            "work_experience": [
                "0–10+ years professional experience",
                "Currently between jobs or exploring new roles",
                "Spends time networking, refining resume, and applying online"
            ],
            "daily_process": [
                "Apply to roles on LinkedIn, Indeed, or company sites",
                "Engage with recruiters, founders, or career communities online",
                "Post open-to-work updates or portfolio pieces",
                "Cold DM people at companies of interest",
                "Track interviews and follow-ups manually"
            ],
            "core_pain_points": [
                "Applications feel like a black hole",
                "Hard to stand out or get seen",
                "Not sure who’s actually engaging with their posts",
                "Feels invisible despite effort on social"
            ],
            "current_workarounds": [
                "Use spreadsheets to track networking efforts",
                "Manually reach out to people who like or comment",
                "Search LinkedIn for people working at target companies"
            ],
            "emotional_states": [
                "Motivated but anxious",
                "Hopeful, sometimes burnt out",
                "Determined to make the right connection"
            ],
            "language_phrases": [
                "open to work",
                "actively applying",
                "referrals",
                "networking",
                "please let me know if you’re hiring"
            ],
            "trigger_signals": [
                "“I’m trying to turn engagement into interviews.”",
                "“People like my post but don’t reach out.”",
                "“I don’t know who to follow up with.”"
            ],
            "early_adopter_indicators": [
                "Posting actively on LinkedIn",
                "Cold messaging recruiters or founders",
                "Open to tools that give a networking edge"
            ]
        }}
    """
}
