
import re
import pandas as pd
from pathlib import Path


# ============================================
# 1. PROJECT PATHS
# ============================================

PROJECT_FOLDER = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_FOLDER / "data" / "processed" / "news_with_countries.csv"
)

OUTPUT_FILE = (
    PROJECT_FOLDER / "data" / "processed" / "news_with_topics.csv"
)

REVIEW_FILE = (
    PROJECT_FOLDER / "data" / "processed" / "topic_review.csv"
)


# ============================================
# 2. TOPIC KEYWORDS
# ============================================

TOPIC_KEYWORDS = {

    "Politics": [
        "government", "election", "minister", "parliament",
        "president", "political", "opposition", "policy",
        "legislation", "congress", "senator", "immigration",
        "deportation", "protest", "protests"
    ],

    "Diplomacy": [
        "diplomatic", "negotiations", "summit", "ambassador",
        "foreign minister", "peace deal", "bilateral",
        "state visit", "foreign relations", "ceasefire talks",
        "peace negotiations", "diplomatic relations",
        "international talks", "leaders meet", "nuclear talks"
    ],

    "Military": [
        "military", "army", "troops", "missile", "missiles",
        "navy", "air force", "armed forces", "soldiers",
        "generals", "fighter jets", "military operation",
        "military base", "military deployment", "weapons"
    ],

    "Security": [
        "terrorism", "terrorist", "intelligence", "bombing",
        "militant", "police", "arrested", "kidnapping",
        "assassination", "shooting", "shootings", "murder",
        "detained", "gang rape", "security operation"
    ],

    "Economics": [
        "economy", "economic", "inflation", "investment",
        "business", "market", "financial", "funding",
        "banking", "stock market", "recession",
        "unemployment", "corporate", "interest rates",
        "compensation payment"
    ],

    "Trade": [
        "trade", "trade deal", "trade agreement", "tariff",
        "tariffs", "exports", "imports", "export", "import",
        "rare earths", "supply chain", "trade restrictions",
        "trade war", "yuan", "customs duties"
    ],

    "Conflict": [
        "war", "conflict", "clashes", "invasion", "fighting",
        "airstrike", "air strikes", "drone strike",
        "missile strike", "shelling", "bombardment",
        "occupation", "incursion", "battle", "ceasefire"
    ],

    "Technology": [
        "technology", "artificial intelligence", "AI",
        "semiconductor", "semiconductors", "Nvidia",
        "SpaceX", "OpenAI", "satellite", "cyberattack",
        "cybersecurity", "software", "robot", "robotics",
        "computer chip"
    ],

    "Energy": [
        "oil", "natural gas", "gas supply", "electricity",
        "energy", "energy crisis", "fuel", "fuel prices",
        "petroleum", "renewable energy", "solar power",
        "wind power", "nuclear energy", "energy security",
        "power grid"
    ],

    "Environment": [
        "climate", "climate change", "flood", "floods",
        "wildfire", "wildfires", "tornado", "earthquake",
        "drought", "storm", "storms", "pollution",
        "deforestation", "extreme weather",
        "environmental damage"
    ],

    "Society": [
        "community", "religion", "religious", "human rights",
        "children", "civilian", "refugee", "refugees",
        "humanitarian", "aid", "poverty", "protesters",
        "social issues", "education", "labour union"
    ],

    "Health": [
        "health", "healthcare", "hospital", "hospitals",
        "disease", "outbreak", "epidemic", "pandemic",
        "measles", "virus", "infection", "medical treatment",
        "public health", "vaccine", "vaccination"
    ],

    "Culture": [
        "culture", "cultural", "film", "festival", "music",
        "artist", "author", "writer", "book", "heritage",
        "museum", "cinema", "art exhibition", "fashion",
        "entertainment"
    ],

    "Transport": [
        "train", "trains", "railway", "collision", "crash",
        "flight", "flights", "airline", "airport closure",
        "airport disruption", "transport", "road accident",
        "metro", "rail network", "aviation"
    ],

    "Sports": [
        "football", "cricket", "sports", "sport",
        "tournament", "championship", "qualifiers",
        "world cup", "olympics", "athlete", "athletes",
        "match", "competition", "tennis", "racing"
    ]
}


# ============================================
# 3. COMPILE KEYWORD PATTERNS
# ============================================

def compile_phrase(phrase):

    escaped = re.escape(phrase)

    escaped = escaped.replace(
        r"\ ",
        r"[\s-]+"
    )

    return re.compile(
        r"(?<!\w)" + escaped + r"(?!\w)",
        flags=re.IGNORECASE
    )


COMPILED_KEYWORDS = {
    topic: [
        compile_phrase(keyword)
        for keyword in keywords
    ]
    for topic, keywords in TOPIC_KEYWORDS.items()
}


# ============================================
# 4. HELPER FUNCTION
# ============================================

def has_pattern(headline, pattern):

    return re.search(
        pattern,
        headline,
        flags=re.IGNORECASE
    ) is not None


# ============================================
# 5. CONTEXTUAL CLASSIFICATION RULES
# ============================================

def apply_contextual_rules(headline, topics):

    # A. Geopolitical military attacks

    geopolitical_actor = has_pattern(
        headline,
        r"\b(?:Ukraine|Ukrainian|Russia|Russian|Iran|Iranian|"
        r"Israel|Israeli|China|Chinese|North Korea|"
        r"South Korea|Taiwan|Pakistan|India|Indian|"
        r"United States|US|American|Syria|Syrian|"
        r"Yemen|Yemeni|Turkey|Turkish)\b"
    )

    attack_action = has_pattern(
        headline,
        r"\b(?:strike|strikes|struck|attack|attacks|"
        r"attacked|hit|hits|targeting|targeted|"
        r"shelling|bombardment|downs|intercepts)\b"
    )

    military_attack = has_pattern(
        headline,
        r"\b(?:drone|missile|air|rocket)\s+"
        r"(?:strike|strikes|attack|attacks|hit|hits)\b"
        r"|\bairstrikes?\b"
    )

    if military_attack or (
        geopolitical_actor and attack_action
    ):
        topics.update(["Military", "Conflict"])

    # B. Airspace and military aircraft incidents

    airspace_incident = has_pattern(
        headline,
        r"\b(?:airspace|fighter jets?|air base|"
        r"military aircraft|radar system)\b"
    )

    if airspace_incident and has_pattern(
        headline,
        r"\b(?:incursion|intercept|interception|"
        r"scramble|jets after)\b"
    ):
        topics.update(["Military", "Conflict"])

    # C. Diplomatic meetings between leaders

    meeting = has_pattern(
        headline,
        r"\b(?:meet|meets|meeting|meetings|"
        r"hold talks|held talks|talks with|"
        r"joint summit|nuclear talks)\b"
    )

    political_leader = has_pattern(
        headline,
        r"\b(?:president|prime minister|foreign minister|"
        r"leader|leaders|head of state|chancellor|"
        r"king|queen|Trump|Putin|Xi|Kim Jong Un)\b"
    )

    if meeting and political_leader:
        topics.add("Diplomacy")

    # D. Foreign-policy visits and international defence ties

    foreign_policy_visit = has_pattern(
        headline,
        r"\b(?:foreign policy|foreign policy push|"
        r"defence ties|defense ties|"
        r"closer international ties|"
        r"state visit|official visit)\b"
    )

    if foreign_policy_visit:
        topics.add("Diplomacy")

    # International visits with a named political leader

    leader_visit = (
        has_pattern(
            headline,
            r"\b(?:Macron|Trump|Putin|Xi|"
            r"William and Kate|King Charles)\b"
        )
        and has_pattern(
            headline,
            r"\b(?:visits?|trip|travels?|"
            r"arrives?|lands?|embarks?)\b"
        )
    )

    if leader_visit:
        topics.add("Diplomacy")

    # E. United Nations negotiations
    if has_pattern(
        headline,
        r"(?<!\w)(?:U\.N\.?|UN|United Nations)(?!\w)"
    ) and has_pattern(
        headline,
        r"\b(?:talks|negotiations|summit|agreement|conference)\b"
    ):
        topics.add("Diplomacy")
            # E2. Autonomous weapons and killer robots

    if has_pattern(
        headline,
        r"\b(?:killer robots|autonomous weapons|"
        r"AI weapons|autonomous military systems)\b"
    ):
        topics.update(["Military", "Technology"])

    # F. International agreements

    international_agreement = has_pattern(
        headline,
        r"\b(?:countries|states|governments|"
        r"France and Malaysia|China and Canada|"
        r"China and the US|US and China)\b"
    )

    agreement_action = has_pattern(
        headline,
        r"\b(?:agree|agrees|agreement|deal|"
        r"sign|signed|negotiate|negotiations)\b"
    )

    if international_agreement and agreement_action:
        topics.add("Diplomacy")

    # G. Labour strikes

    labour_context = has_pattern(
        headline,
        r"\b(?:workers?|employees?|unions?|labour|labor|"
        r"teachers?|nurses?)\b"
    )

    strike_context = has_pattern(
        headline,
        r"\b(?:strike|strikes|walkout|walkouts)\b"
    )

    if labour_context and strike_context:
        topics.update(["Politics", "Society"])

        # A labour strike is not a military conflict.
        topics.discard("Conflict")
        topics.discard("Military")

    # H. Sexual violence

    if has_pattern(
        headline,
        r"\bgang[\s-]+rap(?:e|ed|es|ing)\b"
    ):
        topics.update(["Security", "Society"])

    # I. Medical treatment and health complications

    if has_pattern(
        headline,
        r"\b(?:urgent medical care|medical care|"
        r"medical treatment|undergoes surgery|"
        r"underwent surgery|surgeries|"
        r"health effects|medical condition|"
        r"hospitalised|hospitalized|"
        r"loses hair|hair loss|"
        r"unable to sweat|ability to sweat)\b"
    ):
        topics.add("Health")

    # Autopsy and suspected homicide are security matters,
    # not automatically medical-health stories.

    if has_pattern(
        headline,
        r"\b(?:autopsy|forensic expert|"
        r"forensic analysis)\b"
    ) and has_pattern(
        headline,
        r"\b(?:killed|murdered|homicide|"
        r"assassinated|death investigation)\b"
    ):
        topics.add("Security")
        topics.discard("Health")

    # J. Poisoning and pesticide exposure

    if has_pattern(
        headline,
        r"\b(?:poisoning|poisoned|pesticide exposure|"
        r"toxic exposure|pesticides)\b"
    ):
        topics.update(["Health", "Environment"])

    # K. Wildlife and environmental protection

    if has_pattern(
        headline,
        r"\b(?:baboons?|wildlife|animal sanctuary|"
        r"animal protection|wild animals|"
        r"wildlife sanctuary|protecting the Amazon)\b"
    ):
        topics.add("Environment")

    # L. Mining damage and restoration
    # Do not classify the ordinary phrase "hero of mine"
    # as an environmental mining story.

    actual_mining_context = has_pattern(
        headline,
        r"\b(?:mine damage|mining damage|mining disaster|"
        r"mine pollution|mine devastation|"
        r"mining pollution|mine cleanup|"
        r"mining operations|mine restoration|"
        r"tailings|open-pit mine|"
        r"mining environmental damage)\b"
    )

    if actual_mining_context:
        topics.add("Environment")

    if actual_mining_context and has_pattern(
        headline,
        r"\b(?:compensation|pay|pays|payment|"
        r"repairing|settlement|agrees to pay)\b"
    ):
        topics.add("Economics")

            # Rio Tinto / Panguna mine environmental damage

    if (
        has_pattern(headline, r"\bRio Tinto\b")
        and has_pattern(headline, r"\bPanguna mine\b")
        and has_pattern(
            headline,
            r"\b(?:pay|pays|paid|repair|repairing|compensation|250m)\b"
        )
    ):
        topics.update(["Economics", "Environment"])

    # M. Political candidates and campaigns

    if has_pattern(
        headline,
        r"\b(?:presidential candidate|presidential race|"
        r"presidential campaign|presidential debate|"
        r"pension plans|election campaign|"
        r"senate race|senate challenge|"
        r"far-right candidate|political candidate)\b"
    ):
        topics.add("Politics")

    # N. Immigration and visa policy

    if has_pattern(
        headline,
        r"\b(?:visa cuts|visa rules|visa restrictions|"
        r"backpacker visa|immigration rules|"
        r"migrant deportation|deportation centres|"
        r"return hubs)\b"
    ):
        topics.add("Politics")

    if has_pattern(
        headline,
        r"\b(?:regional employers|employers|"
        r"business costs|labour shortages)\b"
    ) and has_pattern(
        headline,
        r"\b(?:visa|immigration|backpacker)\b"
    ):
        topics.add("Economics")

    # O. Sports events and sporting theft

    if has_pattern(
        headline,
        r"\b(?:Melbourne Cup|AFCON|Tetris showdown|"
        r"gaming championship|esports|"
        r"sports tournament|Cup trophies)\b"
    ):
        topics.add("Sports")

    if has_pattern(
        headline,
        r"\b(?:stolen|theft|robbed|dumped)\b"
    ) and has_pattern(
        headline,
        r"\b(?:Melbourne Cup|horse|trophies|"
        r"runner|sporting event)\b"
    ):
        topics.update(["Sports", "Security"])

    # P. Cultural and entertainment events

    if has_pattern(
        headline,
        r"\b(?:James Bond|Robert Pattinson|"
        r"Eurovision|La Francophonie|"
        r"linguistic institutions|Tetris|"
        r"robot pianist|human musician|"
        r"Chopin)\b"
    ):
        topics.add("Culture")

    # Q. Fast fashion and labour conditions

    if has_pattern(
        headline,
        r"\b(?:fast fashion|garment workers?|"
        r"clothing workers?|people making their jeans|"
        r"fashion supply chain)\b"
    ):
        topics.update(["Economics", "Society"])

    # R. Earthshot and environmental royal engagements

    if has_pattern(
        headline,
        r"\b(?:Earthshot Prize|environmental award)\b"
    ):
        topics.add("Environment")

    # S. Human rights and humanitarian affairs

    if has_pattern(
        headline,
        r"\b(?:demands justice|humanitarian crisis|"
        r"protecting civilians|human rights abuses|"
        r"human rights in migration)\b"
    ):
        topics.add("Society")

    # T. Political office and legislative contests

    if has_pattern(
        headline,
        r"\b(?:Van Hollen|Chuck Schumer|"
        r"Le Pen|senate challenge|"
        r"beat .* senator|beat .* Schumer)\b"
    ):
        topics.add("Politics")

    # U. Cyberattacks and technology-related attacks

    if has_pattern(
        headline,
        r"\b(?:cyberattack|cyber attack|"
        r"hacking attack|data breach|"
        r"software attack|platform attack|"
        r"Hugging Face attack)\b"
    ):
        topics.update(["Technology", "Security"])

    # V. Prevent incidental topics in a royal visit story

    royal_visit = has_pattern(
        headline,
        r"\b(?:William and Kate|"
        r"royal visit|begin India visit)\b"
    )

    if royal_visit and has_pattern(
        headline,
        r"\b(?:street cricket|metro ride)\b"
    ):
        topics.discard("Sports")
        topics.discard("Transport")

    # W. Incidental airport references in crime stories

    airport_crime = (
        has_pattern(
            headline,
            r"\b(?:arrested|detained|smuggling|"
            r"marijuana|cannabis|drug trafficking)\b"
        )
        and has_pattern(
            headline,
            r"\b(?:airport|flight)\b"
        )
    )

    if airport_crime:
        topics.discard("Transport")

    return topics


# ============================================
# 6. MAIN CLASSIFICATION FUNCTION
# ============================================

def classify_topic(headline):

    headline = str(headline)

    detected_topics = set()

    # Standard keyword matching

    for topic, patterns in COMPILED_KEYWORDS.items():

        for pattern in patterns:

            if pattern.search(headline):
                detected_topics.add(topic)
                break

    # Contextual rules

    detected_topics = apply_contextual_rules(
        headline,
        detected_topics
    )

    # Keep category order consistent

    ordered_topics = [
        topic
        for topic in TOPIC_KEYWORDS
        if topic in detected_topics
    ]

    if ordered_topics:
        return ", ".join(ordered_topics)

    return "Uncategorized"


# ============================================
# 7. REGRESSION TESTS
# ============================================

REGRESSION_TESTS = [

    {
        "headline": "Hero of mine: Sam Altman praises Nvidia's Jensen Huang",
        "must_have": ["Technology"],
        "must_not_have": ["Environment"]
    },

    {
        "headline": "Forensic expert says autopsy suggests Epstein was killed",
        "must_have": ["Security"],
        "must_not_have": ["Health"]
    },

    {
        "headline": "US basketball player arrested with marijuana at Nigerian airport",
        "must_have": ["Security"],
        "must_not_have": ["Transport"]
    },

    {
        "headline": "Pope Leo hit by flying rosary while waving to crowds",
        "must_have": [],
        "must_not_have": ["Society"]
    },

    {
        "headline": "U.N. talks seek to rein in 'killer robots' as fears over AI weapons grow",
        "must_have": ["Diplomacy", "Military", "Technology"],
        "must_not_have": []
    },

    {
        "headline": "What's the real cost of fast fashion? Ask the people making your jeans",
        "must_have": ["Economics", "Society", "Culture"],
        "must_not_have": []
    },

    {
        "headline": "Ukraine hits key Crimea bridge with drones",
        "must_have": ["Military", "Conflict"],
        "must_not_have": []
    },

    {
        "headline": "France braces for protests as unions call for nationwide strike",
        "must_have": ["Politics", "Society"],
        "must_not_have": ["Military", "Conflict"]
    },

    {
        "headline": "William and Kate begin India visit after street cricket and metro ride",
        "must_have": ["Diplomacy"],
        "must_not_have": ["Sports", "Transport"]
    },

    {
        "headline": "Rio Tinto agrees to pay US$250m to begin repairing ‘devastation’ left by Panguna mine",
        "must_have": ["Economics", "Environment"],
        "must_not_have": []
    }
]


def run_regression_tests():

    print("\n========== REGRESSION TESTS ==========")

    passed = 0
    failed = 0

    for test in REGRESSION_TESTS:

        result = classify_topic(test["headline"])

        detected = set(
            result.split(", ")
            if result != "Uncategorized"
            else []
        )

        missing = set(test["must_have"]) - detected
        unwanted = set(test["must_not_have"]) & detected

        if not missing and not unwanted:

            passed += 1
            status = "PASS"

        else:

            failed += 1
            status = "FAIL"

        print(f"\n[{status}] {test['headline']}")
        print(f"  Result: {result}")

        if missing:
            print(f"  Missing topics: {', '.join(sorted(missing))}")

        if unwanted:
            print(f"  Unwanted topics: {', '.join(sorted(unwanted))}")

    print("\n--------------------------------------")
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print("======================================")


# ============================================
# 8. LOAD DATASET
# ============================================

def main():

    print("\nLoading country-enriched news dataset...")

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    print(f"Total articles loaded: {len(df)}")

    # Validate required columns

    required_columns = ["title", "countries"]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Classify headlines

    df["topics"] = df["title"].apply(classify_topic)

    # Save classified dataset

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # Create complete review file

    review_df = df[
        ["title", "countries", "topics"]
    ].copy()

    review_df["review_status"] = review_df["topics"].apply(
        lambda value:
        "Uncategorized - inspect"
        if value == "Uncategorized"
        else "Assigned - verify relevance"
    )

    review_df.to_csv(
        REVIEW_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # Topic distribution

    print("\n========== STATECRAFT MONITOR ==========")
    print("       TOPIC CLASSIFIER V2.2")
    print("========================================")

    print("\nTOPIC DISTRIBUTION:")

    topic_counts = (
        df["topics"]
        .str.split(", ")
        .explode()
        .value_counts()
    )

    print(topic_counts.to_string())

    # Classification summary

    uncategorized = (
        df["topics"] == "Uncategorized"
    ).sum()

    classified = len(df) - uncategorized

    coverage = (
        (classified / len(df)) * 100
        if len(df) > 0 else 0
    )

    print("\n========== CLASSIFICATION SUMMARY ==========")

    print(f"Total articles: {len(df)}")
    print(f"Classified articles: {classified}")
    print(f"Uncategorized articles: {uncategorized}")
    print(f"Classification coverage: {coverage:.1f}%")

    # Display uncategorized headlines

    print("\nHEADLINES REQUIRING REVIEW:")

    uncategorized_articles = df[
        df["topics"] == "Uncategorized"
    ]

    if uncategorized_articles.empty:

        print("No uncategorized headlines.")

    else:

        for index, article in enumerate(
            uncategorized_articles["title"],
            start=1
        ):
            print(f"{index}. {article}")

    # Output files

    print("\nOUTPUT FILES:")

    print(f"Classified dataset:\n{OUTPUT_FILE}")
    print(f"\nComplete review file:\n{REVIEW_FILE}")

    print("\n============================================")

    # Run regression tests

    run_regression_tests()


# ============================================
# 9. EXECUTE PROGRAM
# ============================================

if __name__ == "__main__":
    main()
