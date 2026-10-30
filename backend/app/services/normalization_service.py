import re
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional
from app.models.schemas import NormalizedProduct

class NormalizationService:
    @classmethod
    def resolve_official_product_url(
        cls,
        url: Optional[str],
        title: str = "",
        marketplace: str = "Amazon India",
        source: str = ""
    ) -> Optional[str]:
        """
        Resolves and unwraps any URL to ensure it points strictly to the authentic official
        merchant website. Preserves the exact valid product URL returned by Bright Data.
        """
        if not url or not isinstance(url, str):
            # Check if ASIN is available for Amazon
            if "amazon" in (marketplace or source or "").lower():
                asin_match = re.search(r'\b(B0[A-Z0-9]{8})\b', (title or ""))
                if asin_match:
                    return f"https://www.amazon.in/dp/{asin_match.group(1).upper()}"
            return None

        unwrapped = cls.unwrap_product_url(url)
        if not unwrapped:
            if "amazon" in (marketplace or source or "").lower():
                asin_match = re.search(r'\b(B0[A-Z0-9]{8})\b', (url or "") + " " + (title or ""))
                if asin_match:
                    return f"https://www.amazon.in/dp/{asin_match.group(1).upper()}"
            return None

        clean_url = unwrapped.strip()
        parsed = urlparse(clean_url)
        host = (parsed.hostname or "").lower()

        # 1. Amazon India / Amazon:
        if "amazon" in host or "amazon" in (marketplace or source or "").lower():
            if host.endswith("amazon.in") or host.endswith("amazon.com"):
                asin_match = re.search(r'/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})', clean_url, re.IGNORECASE)
                if asin_match:
                    return f"https://www.amazon.in/dp/{asin_match.group(1).upper()}"
                if "/s?" not in clean_url and "/search" not in clean_url and "/stores/" not in clean_url:
                    return clean_url
            asin_match = re.search(r'\b(B0[A-Z0-9]{8})\b', clean_url + " " + title)
            if asin_match:
                return f"https://www.amazon.in/dp/{asin_match.group(1).upper()}"
            return None

        # 2. Flipkart:
        if "flipkart" in host or "flipkart" in (marketplace or source or "").lower():
            if host.endswith("flipkart.com"):
                if "/p/" in parsed.path or "/product/" in parsed.path or "pid=" in parsed.query:
                    return clean_url
            return None

        # 3. Croma / Myntra / Other merchants:
        if host.endswith("croma.com"):
            if "/p/" in parsed.path or "/product/" in parsed.path:
                return clean_url
            return None
        if host.endswith("myntra.com"):
            if re.search(r'/\d+(?:/buy)?$', parsed.path):
                return clean_url
            return None

        # 4. Filter out search engines
        if any(se in host for se in ("google.", "duckduckgo.", "bing.", "yahoo.")):
            return None

        if clean_url.startswith(("http://", "https://")):
            return clean_url

        return None

    @staticmethod
    def unwrap_product_url(url: Optional[str]) -> Optional[str]:
        if not url or not isinstance(url, str):
            return None

        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url

        from urllib.parse import parse_qs, unquote
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if "duckduckgo.com" in host:
            qs = parse_qs(parsed.query)
            if "uddg" in qs and qs["uddg"][0]:
                return unquote(qs["uddg"][0])
        if "google." in host:
            qs = parse_qs(parsed.query)
            for key in ["url", "q", "target", "dest"]:
                if key in qs and qs[key][0].startswith("http"):
                    return unquote(qs[key][0])

        if not url.startswith(("http://", "https://")):
            return None
        return url

    @classmethod
    def is_direct_product_url(cls, url: Optional[str], marketplace: str) -> bool:
        clean_url = cls.unwrap_product_url(url)
        if not clean_url:
            return False

        parsed = urlparse(clean_url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.lower().rstrip("/")
        query = parsed.query.lower()
        marketplace_name = marketplace.lower()

        if "amazon" in marketplace_name:
            return host.endswith("amazon.in") and bool(re.search(r"/(?:dp|gp/product|gp/aw/d)/[a-z0-9]+", path))
        if "flipkart" in marketplace_name:
            return host.endswith("flipkart.com") and ("/p/" in path or "/product/" in path) and "search" not in query
        if "croma" in marketplace_name:
            return host.endswith("croma.com") and ("/p/" in path or "/product/" in path) and "search" not in query
        if "myntra" in marketplace_name:
            return host.endswith("myntra.com") and bool(re.search(r"/\d+(?:/buy)?$", path)) and "search" not in query

        # Fallback if marketplace is unknown or not specified
        if host.endswith("amazon.in"):
            return bool(re.search(r"/(?:dp|gp/product|gp/aw/d)/[a-z0-9]+", path))
        if host.endswith("flipkart.com"):
            return ("/p/" in path or "/product/" in path) and "search" not in query
        if host.endswith("croma.com"):
            return ("/p/" in path or "/product/" in path) and "search" not in query
        if host.endswith("myntra.com"):
            return bool(re.search(r"/\d+(?:/buy)?$", path)) and "search" not in query
        return "search" not in path and "search" not in query

    @staticmethod
    def extract_specs(title: str, features: List[str], category: str) -> Dict[str, str]:
        text = f"{title} {' '.join(features)}".lower()
        specs = {}

        if category == "laptop":
            # RAM
            ram_match = re.search(r'\b(4|8|16|24|32|64)\s*gb\s*(?:ddr[45]|lpddr[45]x?|ram)?\b', text)
            if ram_match:
                specs["RAM"] = f"{ram_match.group(1)} GB"

            # Storage (SSD / HDD)
            storage_match = re.search(r'\b(128|256|512)\s*gb\s*(?:ssd|nvme|pcie|emmc)?\b|\b(1|2)\s*tb\s*(?:ssd|hdd|pcie)?\b', text)
            if storage_match:
                if storage_match.group(1):
                    specs["Storage"] = f"{storage_match.group(1)} GB SSD"
                elif storage_match.group(2):
                    specs["Storage"] = f"{storage_match.group(2)} TB SSD"

            # Processor
            if "intel core i9" in text or "core i9" in text:
                specs["Processor"] = "Intel Core i9"
            elif "intel core i7" in text or "core i7" in text:
                specs["Processor"] = "Intel Core i7"
            elif "intel core i5" in text or "core i5" in text or "i5-" in text:
                specs["Processor"] = "Intel Core i5"
            elif "intel core i3" in text or "core i3" in text:
                specs["Processor"] = "Intel Core i3"
            elif "ryzen 9" in text:
                specs["Processor"] = "AMD Ryzen 9"
            elif "ryzen 7" in text:
                specs["Processor"] = "AMD Ryzen 7"
            elif "ryzen 5" in text:
                specs["Processor"] = "AMD Ryzen 5"
            elif "m3 pro" in text:
                specs["Processor"] = "Apple M3 Pro"
            elif "m3" in text:
                specs["Processor"] = "Apple M3"
            elif "m2" in text:
                specs["Processor"] = "Apple M2"
            elif "m1" in text:
                specs["Processor"] = "Apple M1"

            # Graphics
            gpu_match = re.search(r'\b(rtx\s*4090|rtx\s*4080|rtx\s*4070|rtx\s*4060|rtx\s*4050|rtx\s*3050|rtx\s*2050|gtx\s*1650|iris\s*xe|radeon)\b', text)
            if gpu_match:
                specs["Graphics"] = gpu_match.group(1).upper()

            # Display
            disp_match = re.search(r'\b(13\.[0-9]|14|14\.[0-9]|15\.6|16|17\.3)\s*(?:inch|\")\b', text)
            if disp_match:
                specs["Display Size"] = f"{disp_match.group(1)}\""

        elif category == "phone":
            # RAM
            ram_match = re.search(r'\b(4|6|8|12|16)\s*gb\s*(?:ram)?\b', text)
            if ram_match:
                specs["RAM"] = f"{ram_match.group(1)} GB"

            # Storage
            storage_match = re.search(r'\b(64|128|256|512)\s*gb\s*(?:rom|storage)?\b|\b(1)\s*tb\b', text)
            if storage_match:
                if storage_match.group(1):
                    specs["Storage"] = f"{storage_match.group(1)} GB"
                elif storage_match.group(2):
                    specs["Storage"] = "1 TB"

            # Camera
            cam_match = re.search(r'\b(48|50|64|108|200)\s*mp\b', text)
            if cam_match:
                specs["Primary Camera"] = f"{cam_match.group(1)} MP"

            # Battery
            bat_match = re.search(r'\b(\d{4,5})\s*mah\b', text)
            if bat_match:
                specs["Battery"] = f"{bat_match.group(1)} mAh"

            # Network
            if "5g" in text:
                specs["Network"] = "5G Enabled"

        elif category == "dress":
            # Size
            size_match = re.search(r'\b(xxl|2xl|3xl|xl|xs|s|m|l)\b', text)
            if size_match:
                specs["Size"] = size_match.group(1).upper()

            # Fabric
            fabrics = ["cotton", "silk", "linen", "georgette", "rayon", "polyester", "chiffon", "velvet", "satin"]
            for fab in fabrics:
                if fab in text:
                    specs["Fabric"] = fab.title()
                    break

            # Fit
            if "a-line" in text or "a line" in text:
                specs["Fit"] = "A-Line"
            elif "slim fit" in text or "slim" in text:
                specs["Fit"] = "Slim Fit"
            elif "regular fit" in text or "regular" in text:
                specs["Fit"] = "Regular Fit"
            elif "relaxed" in text:
                specs["Fit"] = "Relaxed"
            elif "bodycon" in text:
                specs["Fit"] = "Bodycon"
            elif "flared" in text or "flare" in text:
                specs["Fit"] = "Flared"

            # Pattern
            if "floral" in text:
                specs["Pattern"] = "Floral"
            elif "printed" in text or "print" in text:
                specs["Pattern"] = "Printed"
            elif "solid" in text or "plain" in text:
                specs["Pattern"] = "Solid"
            elif "striped" in text or "stripe" in text:
                specs["Pattern"] = "Striped"

            # Occasion
            if "party" in text:
                specs["Occasion"] = "Party / Festive"
            elif "formal" in text or "office" in text:
                specs["Occasion"] = "Formal / Office"
            elif "casual" in text or "daily" in text:
                specs["Occasion"] = "Casual / Everyday"
            elif "festive" in text or "ethnic" in text or "wedding" in text:
                specs["Occasion"] = "Festive / Ethnic"

        elif category == "shoes":
            # Size UK
            size_match = re.search(r'\b(?:size|uk|ind)\s*([5-9]|1[0-2])\b|\buk\s*([5-9]|1[0-2])\b', text)
            if size_match:
                sz = size_match.group(1) or size_match.group(2)
                specs["Size"] = f"UK {sz}"

            # Shoe Type
            if "running" in text:
                specs["Type"] = "Running Shoes"
            elif "sneaker" in text:
                specs["Type"] = "Sneakers"
            elif "walking" in text:
                specs["Type"] = "Walking Shoes"
            elif "training" in text or "gym" in text:
                specs["Type"] = "Training / Gym"
            elif "formal" in text or "oxford" in text or "derby" in text:
                specs["Type"] = "Formal Shoes"
            elif "loafer" in text:
                specs["Type"] = "Loafers"
            elif "boot" in text:
                specs["Type"] = "Boots"

            # Material
            if "leather" in text:
                specs["Material"] = "Leather"
            elif "mesh" in text:
                specs["Material"] = "Breathable Mesh"
            elif "canvas" in text:
                specs["Material"] = "Canvas"
            elif "synthetic" in text:
                specs["Material"] = "Synthetic"

            # Sole
            if "rubber" in text:
                specs["Sole"] = "Rubber Sole"
            elif "eva" in text:
                specs["Sole"] = "EVA Cushion Sole"
            elif "air" in text or "cushion" in text:
                specs["Sole"] = "Air Cushion Sole"

        elif category == "tv":
            # Screen Size
            size_match = re.search(r'\b(24|32|40|43|50|55|65|75|85)\s*(?:inch|\")\b', text)
            if size_match:
                specs["Screen Size"] = f"{size_match.group(1)} Inch"

            # Resolution
            if "8k" in text:
                specs["Resolution"] = "8K Ultra HD"
            elif "4k" in text or "ultra hd" in text or "uhd" in text:
                specs["Resolution"] = "4K Ultra HD"
            elif "full hd" in text or "fhd" in text or "1080p" in text:
                specs["Resolution"] = "Full HD"
            elif "hd ready" in text or "720p" in text:
                specs["Resolution"] = "HD Ready"

            # Display Type
            if "oled" in text:
                specs["Display Type"] = "OLED"
            elif "qled" in text:
                specs["Display Type"] = "QLED"
            elif "mini led" in text:
                specs["Display Type"] = "Mini LED"
            elif "led" in text:
                specs["Display Type"] = "LED"

            # Refresh Rate
            ref_match = re.search(r'\b(60|120|144)\s*hz\b', text)
            if ref_match:
                specs["Refresh Rate"] = f"{ref_match.group(1)} Hz"

            # Smart OS
            if "google tv" in text:
                specs["Smart OS"] = "Google TV"
            elif "android tv" in text or "android" in text:
                specs["Smart OS"] = "Android TV"
            elif "webos" in text:
                specs["Smart OS"] = "webOS (LG)"
            elif "tizen" in text:
                specs["Smart OS"] = "Tizen (Samsung)"
            elif "fire tv" in text:
                specs["Smart OS"] = "Fire TV"

        elif category == "refrigerator":
            # Capacity in Litres
            cap_match = re.search(r'\b(\d{2,3})\s*(?:l|ltr|litre|litres)\b', text)
            if cap_match:
                specs["Capacity"] = f"{cap_match.group(1)} L"

            # Door Type
            if "side by side" in text or "side-by-side" in text:
                specs["Door Type"] = "Side-by-Side"
            elif "french door" in text:
                specs["Door Type"] = "French Door"
            elif "double door" in text:
                specs["Door Type"] = "Double Door"
            elif "triple door" in text:
                specs["Door Type"] = "Triple Door"
            elif "single door" in text:
                specs["Door Type"] = "Single Door"

            # Energy Rating
            star_match = re.search(r'\b([1-5])\s*star\b', text)
            if star_match:
                specs["Energy Rating"] = f"{star_match.group(1)} Star"

            # Inverter
            if "inverter" in text:
                specs["Inverter"] = "Inverter Compressor"

            # Defrost
            if "frost free" in text or "frost-free" in text:
                specs["Defrost Type"] = "Frost Free"
            elif "direct cool" in text:
                specs["Defrost Type"] = "Direct Cool"

        elif category == "smartwatch":
            # Display
            if "amoled" in text:
                specs["Display"] = "AMOLED Display"
            elif "retina" in text:
                specs["Display"] = "Retina Display"
            elif "lcd" in text or "tft" in text:
                specs["Display"] = "LCD Display"

            # Calling
            if "calling" in text or "call" in text:
                specs["Calling"] = "Bluetooth Calling"

            # GPS
            if "gps" in text:
                specs["GPS"] = "Built-in GPS"

            # Battery
            bat_match = re.search(r'\b(\d{1,2})\s*(?:day|days)\s*(?:battery)?\b', text)
            if bat_match:
                specs["Battery Life"] = f"{bat_match.group(1)} Days"

            # Health
            if "spo2" in text:
                specs["SpO2 Monitor"] = "Supported"
            if "heart rate" in text:
                specs["Heart Rate Monitor"] = "Supported"

        elif category == "camera":
            # Sensor
            if "full frame" in text or "full-frame" in text:
                specs["Sensor"] = "Full Frame"
            elif "aps-c" in text or "apsc" in text:
                specs["Sensor"] = "APS-C"
            elif "micro four thirds" in text:
                specs["Sensor"] = "Micro Four Thirds"

            # Megapixel
            mp_match = re.search(r'\b(\d{2,3})\s*mp\b', text)
            if mp_match:
                specs["Resolution"] = f"{mp_match.group(1)} MP"

            # Video
            if "8k" in text:
                specs["Video"] = "8K Video"
            elif "4k" in text:
                specs["Video"] = "4K Video"
            elif "1080p" in text:
                specs["Video"] = "1080p Full HD"

            # Type
            if "mirrorless" in text:
                specs["Camera Type"] = "Mirrorless"
            elif "dslr" in text:
                specs["Camera Type"] = "DSLR"
            elif "action" in text or "gopro" in text:
                specs["Camera Type"] = "Action Camera"

        elif category == "kitchen_appliances":
            # Appliance Type
            if "air fryer" in text or "airfryer" in text:
                specs["Appliance Type"] = "Air Fryer"
                cap_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:l|ltr|litre|litres)\b', text)
                if cap_match:
                    specs["Capacity"] = f"{cap_match.group(1)} L"
            elif "microwave" in text:
                specs["Appliance Type"] = "Microwave Oven"
                cap_match = re.search(r'\b(\d{2})\s*(?:l|ltr|litre|litres)\b', text)
                if cap_match:
                    specs["Capacity"] = f"{cap_match.group(1)} L"
            elif "mixer" in text or "grinder" in text:
                specs["Appliance Type"] = "Mixer Grinder"
            elif "induction" in text:
                specs["Appliance Type"] = "Induction Cooktop"
            elif "blender" in text:
                specs["Appliance Type"] = "Blender"
            elif "kettle" in text:
                specs["Appliance Type"] = "Electric Kettle"

            # Power / Wattage
            watt_match = re.search(r'\b(\d{3,4})\s*(?:w|watt|watts)\b', text)
            if watt_match:
                specs["Power"] = f"{watt_match.group(1)} W"

        elif category == "furniture":
            if "solid wood" in text or "sheesham" in text:
                specs["Material"] = "Solid Wood"
            elif "engineered wood" in text or "mdf" in text:
                specs["Material"] = "Engineered Wood"
            elif "metal" in text or "steel" in text:
                specs["Material"] = "Metal"
            elif "fabric" in text or "leatherette" in text:
                specs["Material"] = "Upholstered Fabric"

            if "office chair" in text or "ergonomic" in text:
                specs["Furniture Type"] = "Office / Ergonomic Chair"
            elif "sofa" in text:
                specs["Furniture Type"] = "Sofa"
            elif "dining table" in text:
                specs["Furniture Type"] = "Dining Table"
            elif "bed" in text:
                specs["Furniture Type"] = "Bed"
            elif "desk" in text or "table" in text:
                specs["Furniture Type"] = "Study / Work Desk"

        elif category == "washing_machine":
            if "front load" in text:
                specs["Loading Type"] = "Front Load"
            elif "top load" in text:
                specs["Loading Type"] = "Top Load"
            elif "semi automatic" in text or "semi-automatic" in text:
                specs["Loading Type"] = "Semi-Automatic"

            cap_match = re.search(r'\b(\d+(?:\.\d+)?)\s*kg\b', text)
            if cap_match:
                specs["Capacity"] = f"{cap_match.group(1)} kg"

            if "inverter" in text:
                specs["Inverter"] = "Inverter Motor"

        elif category == "skincare":
            vol_match = re.search(r'\b(\d{2,4})\s*(?:ml|g|gm)\b', text)
            if vol_match:
                specs["Net Volume"] = f"{vol_match.group(1)} ml"

            actives = []
            if "salicylic" in text:
                actives.append("Salicylic Acid (BHA)")
            if "niacinamide" in text:
                actives.append("Niacinamide (Vitamin B3)")
            if "hyaluronic" in text:
                actives.append("Hyaluronic Acid")
            if "vitamin c" in text:
                actives.append("Vitamin C")
            if "retinol" in text:
                actives.append("Retinol")
            if "ceramide" in text:
                actives.append("Ceramides")
            if "tea tree" in text:
                actives.append("Tea Tree")
            if "centella" in text or "cica" in text:
                actives.append("Centella Asiatica (Cica)")
            if actives:
                specs["Key Actives"] = ", ".join(actives)

            if "oily" in text or "acne" in text:
                specs["Skin Type"] = "Oily & Acne-Prone"
            elif "dry" in text:
                specs["Skin Type"] = "Dry & Sensitive"
            elif "all skin" in text or "normal" in text:
                specs["Skin Type"] = "All Skin Types"

        elif category == "headphones":
            if "anc" in text or "noise cancel" in text:
                specs["Noise Cancellation"] = "Active Noise Cancellation (ANC)"
            if "tws" in text or "earbuds" in text or "airpods" in text:
                specs["Form Factor"] = "True Wireless (TWS)"
            elif "over ear" in text or "over-ear" in text:
                specs["Form Factor"] = "Over-Ear"
            elif "neckband" in text:
                specs["Form Factor"] = "Wireless Neckband"

            bat_match = re.search(r'\b(\d{1,3})\s*(?:hours|hrs|hr)\s*(?:playtime|battery)?\b', text)
            if bat_match:
                specs["Playtime"] = f"{bat_match.group(1)} Hours"

        return specs

    @staticmethod
    def is_valid_image_url(url: Any) -> bool:
        if not url or not isinstance(url, str):
            return False
        cleaned = url.strip()
        if cleaned.startswith("//"):
            cleaned = "https:" + cleaned
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            return False
        lower = cleaned.lower()

        # Reject non-product images, placeholders, logos, badges, avatars
        unwanted = (
            "transparent-pixel", "grey-pixel", "1x1", "pixel.gif",
            "prime-logo", "nav-sprite", "amazon-logo", "flipkart-logo",
            "/badge/", "/badges/", "/icons/", "/icon-", "avatar", "no-image",
            "placeholder", "spacer.gif", "beacon", "load_indicator", "source_icon"
        )
        if any(u in lower for u in unwanted):
            return False

        # Reject web pages, search engines, and HTML endpoints
        if lower.endswith((".html", ".htm", ".php", ".asp", ".aspx")):
            return False
        if any(sp in lower for sp in ("/search?", "/search/", "google.com/search", "duckduckgo.com", "bing.com")):
            if "gstatic.com" not in lower and "googleusercontent.com" not in lower:
                return False

        # If it is a direct store webpage URL without image extension or image host, reject it
        image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg", ".bmp")
        has_ext = any(lower.split("?")[0].endswith(ext) for ext in image_extensions)
        is_known_image_host = any(h in lower for h in (
            "media-amazon", "ssl-images-amazon", "images-amazon", "flixcart.com/image",
            "rukminim", "myntassets", "gstatic.com", "googleusercontent", "serpapi.com/images",
            "cloudinary", "imgix", "photobucket", "/images/", "/image/", "/img/", "/photos/", "/photo/"
        ))

        if any(store in lower for store in ("amazon.in", "amazon.com", "flipkart.com", "myntra.com", "croma.com")):
            if not has_ext and not is_known_image_host:
                return False

        return True

    @staticmethod
    def clean_image_url(url: str) -> str:
        if not isinstance(url, str):
            return ""
        cleaned = url.strip()
        if cleaned.startswith("//"):
            cleaned = "https:" + cleaned
        return cleaned

    @classmethod
    def extract_image_candidates(cls, data: Any, key_order: Optional[List[str]] = None) -> List[str]:
        """
        Safely and recursively extract valid product image URLs from arbitrary strings,
        lists, and nested dict structures. Preserves original order and deduplicates.
        """
        results: List[str] = []

        def _walk(val: Any):
            if val is None or val == "":
                return
            if isinstance(val, str):
                if cls.is_valid_image_url(val):
                    results.append(cls.clean_image_url(val))
            elif isinstance(val, list):
                for elem in val:
                    _walk(elem)
            elif isinstance(val, dict):
                preferred_keys = ["url", "link", "src", "image_url", "image", "hires", "hi_res", "large", "main", "primary", "thumbnail"]
                for pk in preferred_keys:
                    if pk in val and val[pk]:
                        _walk(val[pk])
                for k, v in val.items():
                    if k not in preferred_keys:
                        _walk(v)

        if isinstance(data, dict) and key_order:
            for k in key_order:
                if k in data and data[k]:
                    _walk(data[k])
        else:
            _walk(data)

        seen = set()
        deduped: List[str] = []
        for u in results:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    @classmethod
    def parse_price(cls, val: Any) -> Optional[float]:
        if val is None or isinstance(val, bool):
            return None
        if isinstance(val, dict):
            for k in ["final_price", "sale_price", "current_price", "value", "amount", "price"]:
                if k in val and val[k] is not None:
                    parsed = cls.parse_price(val[k])
                    if parsed is not None:
                        return parsed
            return None
        if isinstance(val, (int, float)):
            return float(val) if val > 0 else None
        if isinstance(val, str):
            clean = val.replace(",", "").strip()
            match = re.search(r'\d+(?:\.\d+)?', clean)
            if match:
                try:
                    num = float(match.group(0))
                    return num if num > 0 else None
                except ValueError:
                    return None
        return None

    @classmethod
    def extract_product_prices(cls, item: dict[str, Any]) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Extract (current_selling_price, original_list_price, discount_percent).
        Prefers final/selling price over initial/list price.
        """
        if not isinstance(item, dict):
            return None, None, None

        # 1. Look for selling price
        current = None
        for key in ["final_price", "sale_price", "current_price", "price_value", "deal_price", "offer_price"]:
            if key in item and item[key] is not None:
                current = cls.parse_price(item[key])
                if current is not None:
                    break

        # 2. Look for original / list / MRP price
        original = None
        for key in ["initial_price", "original_price", "list_price", "was_price", "mrp", "regular_price"]:
            if key in item and item[key] is not None:
                original = cls.parse_price(item[key])
                if original is not None:
                    break

        # 3. Fallback for "price" field
        price_val = cls.parse_price(item.get("price"))
        if current is None:
            current = price_val
        elif original is None and price_val is not None and price_val > current:
            original = price_val

        # Ensure original price is strictly greater than current price
        if original is not None and current is not None and original <= current:
            original = None

        # Discount calculation
        discount = None
        if current and original and original > current:
            discount = round(((original - current) / original) * 100, 1)
        elif item.get("discount") is not None or item.get("discount_percent") is not None:
            d_val = cls.parse_price(item.get("discount") or item.get("discount_percent"))
            if d_val and 0 < d_val < 100:
                discount = round(d_val, 1)

        return current, original, discount

    @classmethod
    def normalize_product(cls, product: NormalizedProduct) -> NormalizedProduct:
        # Standardize Brand
        b = (product.brand or "").strip().title()
        if not b or b.lower() in ("unknown", "none", ""):
            from app.services.intent_service import IntentService
            detected = IntentService.extract_brands(product.title, product.category)
            b = detected[0] if detected else "Unknown"

        if b.lower() in ("apple", "iphone", "macbook"):
            b = "Apple"
        elif b.lower() in ("samsung", "galaxy"):
            b = "Samsung"
        elif b.lower() in ("asus", "rog", "tuf"):
            b = "ASUS"
        elif b.lower() in ("hp", "omen", "victus", "pavilion"):
            b = "HP"
        elif b.lower() in ("lenovo", "legion", "ideapad", "thinkpad"):
            b = "Lenovo"
        elif b.lower() in ("dell", "alienware", "inspiron", "vostro"):
            b = "Dell"
        elif b.lower() in ("minimalist", "be minimalist"):
            b = "Minimalist"
        elif b.lower() in ("oneplus", "1+"):
            b = "OnePlus"
        elif b.lower() in ("xiaomi", "mi", "redmi"):
            b = "Xiaomi"
        elif b.lower() in ("sony",):
            b = "Sony"
        product.brand = b
        if product.brand and product.brand != "Unknown" and "Brand" not in product.specifications:
            product.specifications["Brand"] = product.brand

        # Extract specifications if empty
        extracted = cls.extract_specs(product.title, product.features, product.category)
        for k, v in extracted.items():
            if k not in product.specifications:
                product.specifications[k] = v

        # Standardize and normalize product prices
        price_data = {}
        if isinstance(product.raw_data, dict):
            price_data.update(product.raw_data)
        if product.current_price is not None:
            price_data["current_price"] = product.current_price
        if product.original_price is not None:
            price_data["original_price"] = product.original_price
        if product.discount_percent is not None:
            price_data["discount_percent"] = product.discount_percent

        current, original, discount = cls.extract_product_prices(price_data)
        product.current_price = current
        product.original_price = original
        product.discount_percent = discount

        # Ensure offer prices are accurate for each respective marketplace
        if product.offers:
            for offer in product.offers:
                is_same_marketplace = (offer.marketplace or "").lower() == (product.marketplace or "").lower()
                if is_same_marketplace:
                    offer.current_price = product.current_price
                    offer.original_price = product.original_price
                    offer.discount_percent = product.discount_percent
                else:
                    o_data = {}
                    if offer.current_price is not None:
                        o_data["current_price"] = offer.current_price
                    if offer.original_price is not None:
                        o_data["original_price"] = offer.original_price
                    if offer.discount_percent is not None:
                        o_data["discount_percent"] = offer.discount_percent
                    o_current, o_orig, o_disc = cls.extract_product_prices(o_data)
                    offer.current_price = o_current
                    offer.original_price = o_orig
                    offer.discount_percent = o_disc

        # Ensure image candidates and fallback
        candidates: List[str] = []
        if product.image_url and cls.is_valid_image_url(product.image_url):
            candidates.append(cls.clean_image_url(product.image_url))
        if product.image_candidates:
            for c in product.image_candidates:
                if cls.is_valid_image_url(c):
                    cleaned_c = cls.clean_image_url(c)
                    if cleaned_c not in candidates:
                        candidates.append(cleaned_c)

        if not candidates and product.raw_data and isinstance(product.raw_data, dict):
            is_flipkart = "flipkart" in product.marketplace.lower()
            key_order = [
                "primary_image", "image_url", "image", "main_image", "thumbnail",
                "image_link", "image_urls", "additional_image_urls", "additional_images", "images"
            ] if is_flipkart else [
                "image_url", "image", "main_image", "primary_image", "thumbnail",
                "image_link", "image_urls", "additional_image_urls", "images", "additional_images"
            ]
            extracted = cls.extract_image_candidates(product.raw_data, key_order)
            for c in extracted:
                if c not in candidates:
                    candidates.append(c)

        # For Amazon: handle ASIN fallback
        if "amazon" in product.marketplace.lower():
            asin = product.source_product_id or product.specifications.get("ASIN")
            if not asin:
                asin_match = re.search(r'\b(B0[A-Z0-9]{8})\b', (product.product_url or "") + " " + product.title)
                if asin_match:
                    asin = asin_match.group(1).upper()
            if asin:
                asin_img = f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SX400_.jpg"
                if "ASIN" not in product.specifications:
                    product.specifications["ASIN"] = asin
                if asin_img not in candidates:
                    candidates.append(asin_img)

        product.image_candidates = candidates
        product.image_url = candidates[0] if candidates else ""

        # Resolve primary product URL to authentic official merchant website
        product.product_url = cls.resolve_official_product_url(
            product.product_url,
            title=product.title,
            marketplace=product.marketplace,
            source=product.source
        )

        # Resolve each offer URL to authentic official merchant website
        if product.offers:
            for offer in product.offers:
                offer.product_url = cls.resolve_official_product_url(
                    offer.product_url,
                    title=product.title,
                    marketplace=offer.marketplace,
                    source=offer.seller_name or product.source
                )

        return product
