
# open website data set
websites = {
    # Social Media & Messaging
    "youtube": "www.youtube.com",
    "facebook": "www.facebook.com",
    "instagram": "www.instagram.com",
    "twitter": "www.twitter.com",
    "linkedin": "www.linkedin.com",
    "tiktok": "www.tiktok.com",
    "reddit": "www.reddit.com",
    "snapchat": "www.snapchat.com",
    "discord": "www.discord.com",
    "telegram": "web.telegram.org",
    "whatsapp": "www.whatsapp.com",

    # Search & Productivity
    "google": "www.google.com",
    "bing": "www.bing.com",
    "yahoo": "www.yahoo.com",
    "wikipedia": "www.wikipedia.org",
    "notion": "www.notion.so",
    "trello": "www.trello.com",
    "asana": "www.asana.com",
    "evernote": "www.evernote.com",

    # AI & Tech
    "chatgpt": "chat.openai.com",
    "openai": "openai.com",
    "huggingface": "www.huggingface.co",
    "deepmind": "www.deepmind.com",
    "midjourney": "www.midjourney.com",
    
    # Entertainment
    "netflix": "www.netflix.com",
    "spotify": "www.spotify.com",
    "amazon prime": "www.primevideo.com",
    "disney plus": "www.disneyplus.com",
    "hulu": "www.hulu.com",
    "twitch": "www.twitch.tv",
    "soundcloud": "www.soundcloud.com",

    # Shopping & E-commerce
    "amazon": "www.amazon.com",
    "ebay": "www.ebay.com",
    "aliexpress": "www.aliexpress.com",
    "walmart": "www.walmart.com",
    "etsy": "www.etsy.com",
    "flipkart": "www.flipkart.com",
    "best buy": "www.bestbuy.com",
    "target": "www.target.com",

    # Freelancing & Learning
    "fiverr": "www.fiverr.com",
    "upwork": "www.upwork.com",
    "coursera": "www.coursera.org",
    "udemy": "www.udemy.com",
    "edx": "www.edx.org",
    "khan academy": "www.khanacademy.org",
    "codecademy": "www.codecademy.com",
    "stack overflow": "www.stackoverflow.com",
    "medium": "www.medium.com",
    "quora": "www.quora.com",

    # Finance & Banking
    "paypal": "www.paypal.com",
    "stripe": "www.stripe.com",
    "wise": "www.wise.com",
    "revolut": "www.revolut.com",
    "bank of america": "www.bankofamerica.com",
    "chase": "www.chase.com",

    # Design & Development
    "github": "www.github.com",
    "gitlab": "www.gitlab.com",
    "adobe": "www.adobe.com",
    "canva": "www.canva.com",
    "figma": "www.figma.com",
    "dribbble": "www.dribbble.com",
    "behance": "www.behance.net",

    # Cloud & Storage
    "google drive": "drive.google.com",
    "dropbox": "www.dropbox.com",
    "onedrive": "www.onedrive.com",
    "icloud": "www.icloud.com",

    # Travel & Transport
    "uber": "www.uber.com",
    "lyft": "www.lyft.com",
    "airbnb": "www.airbnb.com",
    "booking": "www.booking.com",
    "expedia": "www.expedia.com",
    "tripadvisor": "www.tripadvisor.com",

    # Government & News
    "irs": "www.irs.gov",
    "usps": "www.usps.com",
    "bbc": "www.bbc.com",
    "cnn": "www.cnn.com",
    "ny times": "www.nytimes.com",
    
    # Developer & API Tools
    "postman": "www.postman.com",
    "docker": "www.docker.com",
    "kubernetes": "www.kubernetes.io",
    "mongodb": "www.mongodb.com",
    "firebase": "firebase.google.com",
    "aws": "aws.amazon.com",
    "azure": "azure.microsoft.com",
    "digitalocean": "www.digitalocean.com",
    "heroku": "www.heroku.com",

    # Health & Fitness
    "webmd": "www.webmd.com",
    "mayoclinic": "www.mayoclinic.org",
    "who": "www.who.int",
    "healthline": "www.healthline.com",
    "fitbit": "www.fitbit.com",
    "myfitnesspal": "www.myfitnesspal.com",
    
    # Sports & Gaming
    "espn": "www.espn.com",
    "nba": "www.nba.com",
    "fifa": "www.fifa.com",
    "chesscom": "www.chess.com",
    "lichess": "www.lichess.org",
    "xbox": "www.xbox.com",
    "playstation": "www.playstation.com",
    "steam": "store.steampowered.com",

    # Crypto & Blockchain
    "coinbase": "www.coinbase.com",
    "binance": "www.binance.com",
    "opensea": "www.opensea.io",
    "etherscan": "www.etherscan.io",
    "coingecko": "www.coingecko.com",

    # News & Magazines
    "the guardian": "www.theguardian.com",
    "time": "time.com",
    "forbes": "www.forbes.com",
    "the atlantic": "www.theatlantic.com",
    "business insider": "www.businessinsider.com",
    "the economist": "www.economist.com",

    # Food Delivery & Restaurants
    "ubereats": "www.ubereats.com",
    "grubhub": "www.grubhub.com",
    "door dash": "www.doordash.com",
    "postmates": "www.postmates.com",
    "dominos": "www.dominos.com",
    "pizza hut": "www.pizzahut.com",

    # Online Marketplaces
    "craigslist": "www.craigslist.org",
    "offerup": "www.offerup.com",
    "letgo": "www.letgo.com",
    "poshmark": "www.poshmark.com",
    "mercari": "www.mercari.com",

    # Real Estate
    "zillow": "www.zillow.com",
    "realtor": "www.realtor.com",
    "trulia": "www.trulia.com",
    "redfin": "www.redfin.com",
    
    # Job Search & Career
    "linkedin jobs": "www.linkedin.com/jobs",
    "indeed": "www.indeed.com",
    "glassdoor": "www.glassdoor.com",
    "monster": "www.monster.com",
    "career builder": "www.careerbuilder.com",
    "angelist": "angel.co",

    # Music & Audio
    "pandora": "www.pandora.com",
    "soundcloud": "www.soundcloud.com",
    "apple music": "music.apple.com",
    "tidal": "www.tidal.com",
    "deezer": "www.deezer.com",

    # Gaming & Esports
    "esports": "www.esports.com",
    "twitch": "www.twitch.tv",
    "steam": "store.steampowered.com",
    "riot games": "www.riotgames.com",
}
