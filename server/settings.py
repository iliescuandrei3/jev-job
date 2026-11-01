import os

from dotenv import load_dotenv


load_dotenv()

ALLOWED_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
)

# An application whose latest status is "applied" becomes "ghosted" after this many days of silence
GHOST_AFTER_DAYS = 21
# A new application process starts at the same company after this many days of silence
PROCESS_GAP_DAYS = 120

# Sender domains that never identify the employer: ATS and job boards.
# Entries with a dot match the domain or its subdomains; entries without one match the start of any
# domain label (so "myworkday" covers myworkday.com and myworkdayjobs.com).
ATS_DOMAINS = (
    "greenhouse",
    "lever.co",
    "myworkday",
    "teamtailor",
    "smartrecruiters",
    "ashbyhq",
    "workable",
    "linkedin",
    "indeed",
    "recruitee",
    "personio",
    "jobvite",
    "icims",
    "successfactors",
    "taleo",
    "bamboohr",
    "jobylon",
    "varbi",
    "breezy",
    "join.com",
    "stepstone",
    "glassdoor",
    "xing",
    "welcometothejungle",
    "otta",
    "wellfound",
    "oraclecloud",
    # e-signature tools that send offer and contract emails
    "docusign",
    "hellosign",
    "echosign",
)
# Personal mail providers, which don't identify the employer either
MAIL_PROVIDER_DOMAINS = (
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
)
# Trailing company name tokens dropped when normalising ("Spotify AB" -> "spotify"), plus a few
# descriptors that aren't legal forms but name the same employer ("Sandvik Group" -> "sandvik")
LEGAL_SUFFIXES = frozenset({
    "gmbh", "ab", "ag", "inc", "ltd", "llc", "bv", "as", "asa", "aps", "oy", "oyj", "sa", "sas",
    "sarl", "srl", "spa", "nv", "plc", "corp", "corporation", "co", "company", "kg", "se", "limited",
    "group", "holding", "holdings",
})
