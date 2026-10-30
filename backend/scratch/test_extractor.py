import re
from typing import Dict, Any, Optional, Set, Tuple

def normalize_title(title: str) -> str:
    t = title.lower()
    # Normalize unit spacing: "128 gb" -> "128gb", "8 gb" -> "8gb", "55 inch" -> "55inch", "4 k" -> "4k"
    t = re.sub(r'(\d+)\s*(gb|tb|mb|mp|mah|hz|w|inch|k)\b', r'\1\2', t)
    # Normalize hyphens/spaces in models: "a-56" -> "a56", "m-36" -> "m36"
    t = re.sub(r'\b([a-z])\s*[-_]?\s*(\d{2,3}[a-z0-9]*)\b', r'\1\2', t)
    return t

def extract_model_identifiers(title: str, brand: str) -> Set[str]:
    norm = normalize_title(title)
    models = set()
    
    # 1. Look for family names like "galaxy a56", "galaxy m36", "iphone 16 pro", "redmi note 13"
    family_match = re.findall(
        r'\b(?:galaxy\s+[a-z0-9]+|iphone\s+\d+(?:\s+pro\s+max|\s+pro|\s+plus|\s+mini)?|nord\s+[a-z0-9]+|redmi\s+note\s+\d+[a-z0-9]*|nitro\s+[a-z0-9]+|victus\s+\d*|loq\s+[a-z0-9]*|tuf\s+[a-z0-9]+|bravia\s+\d*)\b',
        norm
    )
    for fm in family_match:
        models.add(re.sub(r'\s+', '', fm))
        
    # 2. Look for alphanumeric standalone model codes e.g. a06, a07, a56, a27, m36, s24, 15arp9, 43pft6130
    code_matches = re.findall(r'\b(?:[a-z]{1,3}\d{1,4}[a-z0-9]*|\d{1,4}[a-z]{1,3}[a-z0-9]*)\b', norm)
    for cm in code_matches:
        # Filter out common units and harmless words
        if cm not in ("128gb", "256gb", "512gb", "64gb", "32gb", "16gb", "8gb", "6gb", "4gb", "2gb", "1tb", "2tb", "5g", "4g", "3g", "4k", "2k", "1080p", "720p", "144hz", "120hz", "60hz", "6000mah", "5000mah", "4500mah", "50mp", "64mp", "108mp", "200mp", "12mp", "43inch", "55inch", "65inch", "32inch", "15inch", "16inch", "14inch"):
            models.add(cm)
            
    return models

def extract_hardware_variants(title: str) -> Dict[str, str]:
    norm = normalize_title(title)
    variants = {}
    
    # RAM
    ram_match = re.search(r'\b(2|3|4|6|8|12|16|24|32|64)gb\s*(?:ram)?\b', norm)
    if ram_match:
        variants["ram"] = f"{ram_match.group(1)}gb"
        
    # Storage
    storage_match = re.search(r'\b(16|32|64|128|256|512)gb\s*(?:rom|storage|ssd|emmc|internal)?\b|\b(1|2)tb\s*(?:ssd|hdd)?\b', norm)
    if storage_match:
        if storage_match.group(1):
            variants["storage"] = f"{storage_match.group(1)}gb"
        elif storage_match.group(2):
            variants["storage"] = f"{storage_match.group(2)}tb"
            
    # Screen Size
    size_match = re.search(r'\b(\d{2}(?:\.\d+)?)\s*(?:inch|cm|\"|\')\b', norm)
    if size_match:
        variants["screen_size"] = size_match.group(1)
        
    # 5G/4G
    if "5g" in norm:
        variants["network"] = "5g"
    elif "4g" in norm:
        variants["network"] = "4g"
        
    return variants

print("Testing model and variant extraction:")
cases = [
    "Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)",
    "SAMSUNG Galaxy A06 5G (Black, 128 GB) (4 GB RAM)",
    "Galaxy A56 5G Samsung (Awesome Graphite, 8GB RAM, 128GB Storage)",
    "SAMSUNG Galaxy A56 5G (Awesome Iceblue, 128 GB) (8 GB RAM)",
    "Samsung Galaxy A07 5G (Light Blue, 6GB, 128GB Storage)",
    "Samsung Galaxy A27 5G (Awesome Violet, 6GB RAM, 128GB Storage)",
    "Samsung M36 5G (Midnight Blue, 6GB RAM, 128GB Storage) | 6000mAh Battery",
    "SAMSUNG Galaxy M36 5G (Midnight Blue, 128 GB) (6 GB RAM)"
]
for c in cases:
    print(f"\nTitle: {c}")
    print(f"  Models: {extract_model_identifiers(c, 'Samsung')}")
    print(f"  Variants: {extract_hardware_variants(c)}")
