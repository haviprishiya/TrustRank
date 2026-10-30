import re
from typing import Optional, List, Tuple
from app.models.schemas import SearchIntent

CATEGORY_DEFINITIONS = {
    "laptop": {
        "display_name": "Electronics & Computing",
        "keywords": ["laptop", "laptops", "notebook", "notebooks", "macbook", "macbooks", "chromebook", "ultrabook", "thinkpad"],
        "negative_keywords": ["laptop bag", "laptop sleeve", "laptop stand", "laptop skin", "laptop cooler", "laptop charger", "computer table", "laptop table", "study table", "computer desk", "desk table", "mouse pad", "mouse", "keyboard", "keyboards", "gaming mouse", "gaming keyboard", "headset", "earphones", "backpack"],
        "default_budget": 60000,
        "brands": ["Apple", "Dell", "HP", "Lenovo", "ASUS", "Acer", "MSI", "Samsung", "LG", "Honor", "Xiaomi", "Infinix"]
    },
    "phone": {
        "display_name": "Smartphones & Mobiles",
        "keywords": ["phone", "phones", "smartphone", "smartphones", "mobile", "mobiles", "iphone", "iphones", "android", "cellphone"],
        "negative_keywords": ["headphone", "headphones", "earphone", "earphones", "microphone", "intercom", "phone case", "phone cover", "tempered glass", "phone stand"],
        "default_budget": 25000,
        "brands": ["Apple", "Samsung", "OnePlus", "Google", "Pixel", "Xiaomi", "Redmi", "Poco", "Realme", "Vivo", "iQOO", "Oppo", "Motorola", "Nothing"]
    },
    "skincare": {
        "display_name": "Skincare & Beauty",
        "keywords": ["skincare", "skin care", "face wash", "facewash", "moisturizer", "moisturiser", "sunscreen", "serum", "cleanser", "toner", "face cream", "lotion", "night cream", "sunblock", "salicylic", "niacinamide", "retinol", "hyaluronic", "vitamin c serum"],
        "negative_keywords": [],
        "default_budget": 800,
        "brands": ["Minimalist", "Plum", "Cetaphil", "Neutrogena", "The Ordinary", "Dot & Key", "Mamaearth", "CeraVe", "Derma Co", "Bioderma", "L'Oreal", "Forest Essentials", "Simple", "Innisfree"]
    },
    "hair_care": {
        "display_name": "Hair Care",
        "keywords": ["shampoo", "shampoos", "conditioner", "conditioners", "hair care", "hair serum", "hair oil", "hair mask", "anti dandruff"],
        "negative_keywords": [],
        "default_budget": 800,
        "brands": ["L'Oreal", "Dove", "Pantene", "Head & Shoulders", "Tresemme", "Mamaearth", "Minimalist", "WOW", "Sebamed", "Biotique"]
    },
    "makeup": {
        "display_name": "Makeup",
        "keywords": ["makeup", "lipstick", "foundation", "concealer", "mascara", "eyeliner", "blush", "primer", "highlighter"],
        "negative_keywords": [],
        "default_budget": 1500,
        "brands": ["Maybelline", "Lakme", "MAC", "Nykaa", "Sugar", "NARS", "L'Oreal", "Colorbar"]
    },
    "furniture": {
        "display_name": "Furniture & Home",
        "keywords": ["furniture", "office chair", "desk chair", "ergonomic chair", "sofa", "table", "desk", "bed", "bookshelf"],
        "negative_keywords": [],
        "default_budget": 15000,
        "brands": ["Ikea", "Wakefit", "Green Soul", "Nilkamal", "Godrej", "Durian"]
    },
    "headphones": {
        "display_name": "Headphones & Audio",
        "keywords": ["headphone", "headphones", "earphone", "earphones", "earbuds", "earbud", "tws", "airpods", "headset", "neckband", "iem", "over ear", "in ear audio"],
        "negative_keywords": [],
        "default_budget": 5000,
        "brands": ["Sony", "Bose", "Sennheiser", "JBL", "boAt", "Noise", "Apple", "Realme", "OnePlus", "Skullcandy", "Audio-Technica", "Marshall", "Anker", "Soundcore", "Nothing"]
    },
    "camera": {
        "display_name": "Cameras & Photography",
        "keywords": ["camera", "cameras", "dslr", "mirrorless", "vlogging camera", "action camera", "gopro", "camcorder"],
        "negative_keywords": ["camera bag", "camera strap", "camera lens cleaner", "security camera", "cctv", "webcam"],
        "default_budget": 55000,
        "brands": ["Sony", "Canon", "Nikon", "Fujifilm", "Panasonic", "GoPro", "DJI", "Insta360", "Olympus"]
    },
    "tv": {
        "display_name": "Televisions & Smart TVs",
        "keywords": ["tv", "tvs", "television", "televisions", "smart tv", "smart tvs", "oled tv", "qled tv", "4k tv", "led tv"],
        "negative_keywords": ["tv mount", "tv remote", "tv stand", "tv cover"],
        "default_budget": 35000,
        "brands": ["Sony", "Samsung", "LG", "TCL", "Xiaomi", "Mi", "Hisense", "OnePlus", "VU", "Acer", "Toshiba"]
    },
    "washing_machine": {
        "display_name": "Washing Machines",
        "keywords": ["washing machine", "washing machines", "washer", "dryer combo", "front load", "top load"],
        "negative_keywords": ["washing machine cover", "washing machine stand", "washing machine liquid", "detergent"],
        "default_budget": 25000,
        "brands": ["LG", "Samsung", "Bosch", "Whirlpool", "IFB", "Godrej", "Panasonic", "Haier"]
    },
    "shoes": {
        "display_name": "Footwear & Running",
        "keywords": ["shoes", "shoe", "sneakers", "sneaker", "running shoes", "walking shoes", "training shoes", "boots", "loafers", "sports shoes"],
        "negative_keywords": ["shoe rack", "shoe box", "shoe polish", "shoe laces"],
        "default_budget": 3500,
        "brands": ["Nike", "Adidas", "Puma", "Reebok", "Asics", "New Balance", "Skechers", "Under Armour", "Woodland", "Campus", "Red Tape"]
    },
    "smartwatch": {
        "display_name": "Smartwatches & Wearables",
        "keywords": ["smartwatch", "smart watch", "smartwatches", "fitness band", "fitness tracker", "apple watch", "galaxy watch"],
        "negative_keywords": ["smartwatch strap", "watch strap", "watch charger", "screen protector"],
        "default_budget": 4000,
        "brands": ["Apple", "Samsung", "Garmin", "Fitbit", "Amazfit", "Fossil", "Noise", "Fire-Boltt", "boAt", "Fastrack"]
    },
    "monitor": {
        "display_name": "Monitors & Displays",
        "keywords": ["monitor", "monitors", "display", "gaming monitor", "computer screen", "4k monitor", "curved monitor"],
        "negative_keywords": ["monitor arm", "monitor stand", "monitor light", "baby monitor", "blood pressure monitor"],
        "default_budget": 15000,
        "brands": ["LG", "Dell", "Samsung", "BenQ", "ASUS", "Acer", "MSI", "ViewSonic", "Gigabyte"]
    },
    "keyboard": {
        "display_name": "Keyboards & Peripherals",
        "keywords": ["keyboard", "keyboards", "mechanical keyboard", "wireless keyboard", "gaming keyboard"],
        "negative_keywords": ["keyboard cover", "keycaps", "keyboard wrist rest", "piano keyboard", "musical keyboard"],
        "default_budget": 3000,
        "brands": ["Logitech", "Keychron", "Corsair", "Razer", "Redragon", "Royal Kludge", "HyperX", "Portronics", "HP", "Dell"]
    },
    "dress": {
        "display_name": "Dresses & Apparel",
        "keywords": ["dress", "dresses", "gown", "gowns", "frock", "frocks", "kurti", "kurtis", "saree", "sarees", "maxi dress", "midi dress", "mini dress", "one piece", "lehenga", "anarkali", "top", "tunic", "skirt"],
        "negative_keywords": ["dress shoes", "dressing table", "dress up", "hair dressing", "shoe", "shoes"],
        "default_budget": 2500,
        "brands": ["Zara", "H&M", "Biba", "W for Woman", "FabIndia", "ONLY", "Vero Moda", "Mango", "Forever 21", "AND", "Aurelia", "Marks & Spencer", "Levi's", "Allen Solly"]
    },
    "refrigerator": {
        "display_name": "Refrigerators & Cooling",
        "keywords": ["refrigerator", "refrigerators", "fridge", "fridges", "single door fridge", "double door fridge", "side by side fridge", "deep freezer", "mini fridge"],
        "negative_keywords": ["fridge cover", "fridge stand", "fridge magnet", "fridge bottle", "fridge storage", "refrigerator cover", "fridge mat"],
        "default_budget": 28000,
        "brands": ["Samsung", "LG", "Whirlpool", "Haier", "Godrej", "Bosch", "Panasonic", "Voltas", "Beko", "Liebherr"]
    },
    "kitchen_appliances": {
        "display_name": "Kitchen Appliances",
        "keywords": ["air fryer", "airfryer", "microwave", "microwave oven", "mixer grinder", "mixer", "grinder", "blender", "juicer", "induction cooktop", "induction", "coffee maker", "espresso machine", "toaster", "electric kettle", "kettle", "food processor", "sandwich maker", "kitchen appliance", "kitchen appliances"],
        "negative_keywords": ["microwave cover", "air fryer liners", "air fryer paper", "kettle cleaner", "cookware set", "dinner set"],
        "default_budget": 4500,
        "brands": ["Philips", "Prestige", "Bajaj", "Morphy Richards", "Havells", "Pigeon", "Bosch", "Wonderchef", "Inalsa", "Kent", "Agaro", "Cuisinart", "Instant Pot", "IFB"]
    }
}

class IntentService:
    @staticmethod
    def extract_budget(query: str) -> Optional[float]:
        q = query.lower().replace(",", "")
        
        # Patterns like: under 70000, under 70k, below 50000, below 50k, < 40000, under rs 30000, under ₹50000
        patterns = [
            r'(?:under|below|less than|within|max|budget of|budget|around|up to|upto)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(k|lakh|lac)?\b',
            r'(?:rs\.?|inr|₹)\s*(\d+(?:\.\d+)?)\s*(k|lakh|lac)?\s*(?:budget|under|below)?\b',
            r'<\s*(\d+(?:\.\d+)?)\s*(k|lakh|lac)?\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, q)
            if match:
                num_str = match.group(1)
                unit = match.group(2)
                try:
                    val = float(num_str)
                    if unit == 'k':
                        val *= 1000
                    elif unit in ('lakh', 'lac'):
                        val *= 100000
                    elif val < 1000 and "k" not in q and "laptop" in q:
                        # e.g. "under 70" for laptop might mean 70k
                        if val < 200:
                            val *= 1000
                    return val
                except ValueError:
                    continue
        return None

    @staticmethod
    def extract_brands(query: str, category: str) -> List[str]:
        q_lower = query.lower()
        found_brands = []
        
        # Check brands from the category
        if category in CATEGORY_DEFINITIONS:
            for b in CATEGORY_DEFINITIONS[category]["brands"]:
                # Use word boundary
                pattern = r'\b' + re.escape(b.lower()) + r'\b'
                if re.search(pattern, q_lower):
                    found_brands.append(b)
        else:
            # Check across all brands
            for cat_data in CATEGORY_DEFINITIONS.values():
                for b in cat_data["brands"]:
                    pattern = r'\b' + re.escape(b.lower()) + r'\b'
                    if re.search(pattern, q_lower) and b not in found_brands:
                        found_brands.append(b)
                        
        return found_brands

    @staticmethod
    def extract_features_and_use(query: str) -> Tuple[List[str], Optional[str]]:
        q_lower = query.lower()
        features = []
        use_case = None
        
        feature_map = {
            "gaming": ("Gaming", "Gaming / High Performance"),
            "programming": ("Programming / Coding", "Software Development"),
            "coding": ("Programming / Coding", "Software Development"),
            "office": ("Office Work", "Office / Productivity"),
            "student": ("Student / Learning", "Study & Schoolwork"),
            "video editing": ("Video Editing", "Content Creation"),
            "editing": ("Photo & Video Editing", "Content Creation"),
            "photography": ("High Quality Camera / Photography", "Photography"),
            "camera": ("High Quality Camera", None),
            "battery": ("Long Battery Life", None),
            "fast charging": ("Fast Charging", None),
            "lightweight": ("Lightweight & Portable", None),
            "portable": ("Portability", None),
            "oily skin": ("Oily Skin Formulation", "Oily Skin Care"),
            "acne": ("Acne & Blemish Control", "Acne Treatment"),
            "dry skin": ("Dry Skin Hydration", "Dry Skin Nourishment"),
            "sensitive": ("Sensitive Skin Safe", "Sensitive Skin Care"),
            "wireless": ("Wireless / Bluetooth", None),
            "bluetooth": ("Wireless / Bluetooth", None),
            "anc": ("Active Noise Cancellation (ANC)", None),
            "noise cancelling": ("Active Noise Cancellation (ANC)", None),
            "noise cancellation": ("Active Noise Cancellation (ANC)", None),
            "oled": ("OLED Display", None),
            "4k": ("4K Ultra HD", None),
            "5g": ("5G Connectivity", None),
            "mechanical": ("Mechanical Switches", None),
            "running": ("Running & High Impact", "Running & Athletics"),
            "gym": ("Gym & Workout", "Fitness Training"),
            "waterproof": ("Waterproof / Water Resistant", None),
            "backlit": ("Backlit / RGB", None),
            "type c": ("USB Type-C", None)
        }
        
        for key, (feat_name, uc) in feature_map.items():
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, q_lower):
                if feat_name not in features:
                    features.append(feat_name)
                if uc and not use_case:
                    use_case = uc
                    
        return features, use_case

    @staticmethod
    def extract_requirements(query: str) -> List[str]:
        """Retain natural-language purpose clauses without a category synonym list."""
        cleaned = re.sub(
            r"\s+(?:under|below|less than|within|max|budget of|budget|around|up to|upto)\s+.*$",
            "",
            query.lower().strip(),
        )
        matches = re.findall(r"\b(?:for|with|suitable for|used for)\s+([^,;]+)", cleaned)
        requirements: List[str] = []
        for clause in matches:
            for part in re.split(r"\s+(?:and|or)\s+", clause):
                value = re.sub(r"\s+", " ", part).strip(" .")
                if value and value not in requirements:
                    requirements.append(value)
        return requirements

    @classmethod
    def detect_intent(cls, raw_query: str) -> SearchIntent:
        cleaned_query = raw_query.strip()
        q_lower = cleaned_query.lower()
        
        detected_cat = "general"
        confidence = 0.5
        
        # Exact keyword scoring with word boundary checks and negative keyword penalties
        best_score = -1
        best_cat = "general"
        
        for cat_name, cat_data in CATEGORY_DEFINITIONS.items():
            score = 0
            # Check negative keywords first
            for neg in cat_data.get("negative_keywords", []):
                neg_pattern = r'\b' + re.escape(neg) + r'\b'
                if re.search(neg_pattern, q_lower):
                    score -= 10
            
            # Check positive keywords
            for kw in cat_data["keywords"]:
                pattern = r'\b' + re.escape(kw) + r'\b'
                matches = re.findall(pattern, q_lower)
                if matches:
                    # Specific longer keywords get higher weight
                    score += len(matches) * (3 if len(kw.split()) > 1 else 2)
            
            # Check brand matches
            for b in cat_data["brands"]:
                b_pattern = r'\b' + re.escape(b.lower()) + r'\b'
                if re.search(b_pattern, q_lower):
                    score += 1.5
            
            if score > best_score and score > 0:
                best_score = score
                best_cat = cat_name
        
        if best_score > 0:
            detected_cat = best_cat
            confidence = min(0.98, 0.6 + (best_score * 0.1))
        else:
            detected_cat = "general"
            confidence = 0.4
        
        display_name = CATEGORY_DEFINITIONS.get(detected_cat, {}).get("display_name", "General Products")
        budget = cls.extract_budget(cleaned_query)
        brands = cls.extract_brands(cleaned_query, detected_cat)
        features, use_case = cls.extract_features_and_use(cleaned_query)
        requirements = cls.extract_requirements(cleaned_query)
        
        # Tokenize keywords for search provider queries
        # Remove stop words and budget phrases from query to form normalized_query
        normalized_q = re.sub(r'\b(?:under|below|less than|within|budget of|budget|around|rs\.?|inr|₹|\d+k|\d+)\b', '', cleaned_query, flags=re.IGNORECASE)
        normalized_q = ' '.join(normalized_q.split()).strip()
        if not normalized_q:
            normalized_q = cleaned_query
            
        keywords = [w for w in re.findall(r'\b[a-zA-Z0-9_-]+\b', q_lower) if len(w) > 2]
        
        return SearchIntent(
            raw_query=cleaned_query,
            detected_category=detected_cat,
            category_display_name=display_name,
            confidence=confidence,
            extracted_budget=budget,
            extracted_brands=brands,
            extracted_features=features,
            extracted_requirements=requirements,
            target_audience_or_use=use_case,
            normalized_query=normalized_q,
            keywords=keywords
        )
