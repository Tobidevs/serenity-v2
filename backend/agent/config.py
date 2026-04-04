# Constants for Domain Filtering
REPOSITORIES = {
    "general": [
        "ccel.org", "newadvent.org", "biblegateway.com", 
        "stepbible.org", "earlychristianwritings.com"
    ],
    "denominations": {
        "catholic": ["vatican.va", "papalencyclicals.net", "dhspriory.org", "catholic.com"],
        "orthodox": ["orthodoxchurchfathers.com", "svots.edu", "goarch.org", "ancientfaith.com"],
        "reformed": ["monergism.com", "prdl.org", "thegospelcoalition.org", "ligonier.org"],
        "anglican": ["anglicanhistory.org", "bcponline.org", "episcopalarchives.org"],
        "lutheran": ["lutheranlibrary.org", "lcms.org", "bookofconcord.org"]
    },
    "modes": {
        "academic": [
            "biblical-studies.org.uk", "theology.edu.au", 
            "atla.com", "place.asburyseminary.edu"
        ],
        "devotional": [
            "desiringgod.org", "wordonfire.org", 
            "biblehub.com/sermons", "crosswalk.com"
        ]
    }
}

AVAILABLE_TRANSLATIONS = ["KJV"]

OT_HINTS = {
    "old testament",
    "torah",
    "psalms",
    "proverbs",
    "isaiah",
    "genesis",
    "exodus",
}
NT_HINTS = {"new testament", "gospel", "epistle", "jesus", "paul", "revelation", "acts"}

VALID_GENRES = {"Gospel", "Epistle", "Torah", "Prophecy", "History/Wisdom/Other"}