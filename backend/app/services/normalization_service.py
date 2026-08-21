import re
from urllib.parse import urlparse
from typing import Dict, List, Optional
from app.models.schemas import NormalizedProduct

class NormalizationService:
    @staticmethod
    def unwrap_product_url(url: Optional[str]) -> Optional[str]:
        if not url or not isinstance(url, str):
            return None

        url = url.strip()
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

        if "amazon" in marketplace_name or host.endswith("amazon.in"):
            return host.endswith("amazon.in") and bool(re.search(r"/(?:dp|gp/product|gp/aw/d)/[a-z0-9]+", path))
        if "flipkart" in marketplace_name or host.endswith("flipkart.com"):
            return host.endswith("flipkart.com") and ("/p/" in path or "/product/" in path) and "search" not in query
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

        elif category == "skincare":
            # Volume
            vol_match = re.search(r'\b(\d{2,4})\s*(?:ml|g|gm)\b', text)
            if vol_match:
                specs["Net Volume"] = f"{vol_match.group(1)} ml"

            # Key actives
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

            # Skin Type Suitability
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

    @classmethod
    def normalize_product(cls, product: NormalizedProduct) -> NormalizedProduct:
        # Standardize Brand
        b = product.brand.strip().title()
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

        # Extract specifications if empty
        extracted = cls.extract_specs(product.title, product.features, product.category)
        for k, v in extracted.items():
            if k not in product.specifications:
                product.specifications[k] = v

        # Calculate discount if missing
        if product.original_price and product.current_price and product.current_price > 0 and product.original_price > product.current_price:
            if not product.discount_percent:
                product.discount_percent = round(((product.original_price - product.current_price) / product.original_price) * 100, 1)

        return product
