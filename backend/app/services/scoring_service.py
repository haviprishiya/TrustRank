import math
import re
from typing import List, Dict, Any, Tuple, Optional
from app.models.schemas import (
    NormalizedProduct,
    ScoredRecommendation,
    UserRequirementAnswers
)
from app.services.review_service import ReviewService
from app.services.comparison_service import ComparisonService

def parse_first_number(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    # Find numbers like 16, 250, 55, 3.5, etc.
    m = re.search(r"(\d+(?:\.\d+)?)", str(text))
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            return None
    return None

class ScoringService:
    @staticmethod
    def calculate_budget_fit(
        price: Optional[float],
        target_budget: float = 0.0,
        min_price: float = 0.0,
        max_price: float = 0.0
    ) -> Tuple[float, List[str], List[str]]:
        if not price or price <= 0:
            return 0.0, [], ["Retail price not provided in source feed (check merchant link)"]

        if max_price <= 0 and target_budget > 0:
            max_price = target_budget

        if max_price <= 0 and min_price <= 0:
            return 0.0, [f"Live price: ₹{price:,.0f}"], []

        pos = []
        neg = []

        # Case 1: Both Min and Max Price are specified
        if min_price > 0 and max_price > 0:
            if price < min_price:
                under = min_price - price
                ratio = price / min_price
                if ratio >= 0.85:
                    score = 75.0
                    neg.append(f"Slightly below min price of ₹{min_price:,.0f} by ₹{under:,.0f} (Priced at ₹{price:,.0f})")
                elif ratio >= 0.70:
                    score = 50.0
                    neg.append(f"Below your min price of ₹{min_price:,.0f} (₹{price:,.0f})")
                else:
                    score = 25.0
                    neg.append(f"Significantly below specified price range (₹{price:,.0f} vs min ₹{min_price:,.0f})")
            elif price <= max_price:
                score = 100.0
                pos.append(f"Fits within your price range of ₹{min_price:,.0f} - ₹{max_price:,.0f} (Priced at ₹{price:,.0f})")
            elif price <= max_price * 1.15:
                score = 80.0
                over = price - max_price
                neg.append(f"Slightly above max budget by ₹{over:,.0f} (within 15% stretch)")
            elif price <= max_price * 1.30:
                score = 55.0
                over = price - max_price
                ratio = price / max_price
                neg.append(f"Exceeds max budget by ₹{over:,.0f} (+{int((ratio-1)*100)}%)")
            else:
                score = 25.0
                neg.append(f"Significantly exceeds max budget (₹{price:,.0f} vs max ₹{max_price:,.0f})")
            return score, pos, neg

        # Case 2: Only Max Price / target_budget specified
        ratio = price / max_price
        if ratio <= 0.85:
            score = 95.0
            savings = max_price - price
            pos.append(f"Well under your budget (Saves ₹{savings:,.0f})")
        elif ratio <= 1.0:
            score = 100.0
            pos.append(f"Fits your target budget of ₹{max_price:,.0f} (Priced at ₹{price:,.0f})")
        elif ratio <= 1.15:
            score = 80.0
            over = price - max_price
            neg.append(f"Slightly above target budget by ₹{over:,.0f} (within 15% stretch)")
        elif ratio <= 1.30:
            score = 55.0
            over = price - max_price
            neg.append(f"Exceeds target budget by ₹{over:,.0f} (+{int((ratio-1)*100)}%)")
        else:
            score = 25.0
            neg.append(f"Significantly exceeds target budget (₹{price:,.0f} vs ₹{max_price:,.0f})")

        return score, pos, neg

    @classmethod
    def evaluate_product(
        cls,
        product: NormalizedProduct,
        answers: Dict[str, Any],
        category: str
    ) -> ScoredRecommendation:
        # Attach review analysis if not already attached
        if not product.review_analysis:
            product.review_analysis = ReviewService.analyze_product_reviews(product)

        positive_reasons: List[str] = []
        negative_reasons: List[str] = []
        neutral_observations: List[str] = []
        scoring_explanations: Dict[str, str] = {}

        # 1. Budget Evaluation (Min & Max Range)
        raw_budget = answers.get("budget", 0.0)
        target_budget = 0.0
        min_price = 0.0
        max_price = 0.0

        if isinstance(raw_budget, dict):
            min_price = float(raw_budget.get("min", 0.0) or 0.0)
            max_price = float(raw_budget.get("max", 0.0) or 0.0)
            target_budget = max_price
        elif isinstance(raw_budget, (int, float)):
            target_budget = float(raw_budget)
            max_price = target_budget
        elif isinstance(raw_budget, str):
            b_match = re.search(r'\d[\d,]*(?:\.\d+)?', raw_budget)
            if b_match:
                try:
                    target_budget = float(b_match.group(0).replace(",", ""))
                    max_price = target_budget
                except ValueError:
                    target_budget = 0.0

        if "min_price" in answers and answers["min_price"] is not None:
            try:
                min_price = float(answers["min_price"])
            except (ValueError, TypeError):
                pass
        if "max_price" in answers and answers["max_price"] is not None:
            try:
                max_price = float(answers["max_price"])
                if max_price > 0:
                    target_budget = max_price
            except (ValueError, TypeError):
                pass

        budget_score, b_pos, b_neg = cls.calculate_budget_fit(
            product.current_price,
            target_budget=target_budget,
            min_price=min_price,
            max_price=max_price
        )
        positive_reasons.extend(b_pos)
        negative_reasons.extend(b_neg)
        
        range_label = f"₹{min_price:,.0f} - ₹{max_price:,.0f}" if min_price > 0 and max_price > 0 else f"₹{target_budget:,.0f}"
        scoring_explanations["budget_fit"] = f"Budget alignment score {budget_score:.0f}/100" + (f" (₹{product.current_price:,.0f} vs {range_label})" if product.current_price and (target_budget or max_price) else "")

        # 2. Dynamic Weighted Requirement Matching
        earned_weight_points = 0.0
        total_possible_weight_points = 0.0

        title_lower = product.title.lower()
        specs = product.specifications or {}
        specs_lower = {k.lower(): str(v).lower() for k, v in specs.items()}
        features_lower = [f.lower() for f in product.features]
        brand_lower = (product.brand or "").lower()
        desc_lower = (product.description or "").lower()

        # Combine listing corpus for keyword verification
        listing_corpus = " ".join([
            title_lower,
            brand_lower,
            desc_lower,
            " ".join(specs_lower.values()),
            " ".join(features_lower)
        ])

        # A. Preferred Brands
        preferred_brands = answers.get("brands", [])
        matched_brand = False
        if preferred_brands and isinstance(preferred_brands, list) and len(preferred_brands) > 0:
            b_weight = 2.0
            total_possible_weight_points += b_weight
            matched_brand = any(pb.lower() in brand_lower or pb.lower() in title_lower for pb in preferred_brands)
            if matched_brand:
                earned_weight_points += b_weight
                positive_reasons.append(f"Matches your preferred brand ({product.brand})")
            else:
                earned_weight_points += 0.0
                negative_reasons.append(f"Alternative brand ({product.brand}) rather than your selected brands ({', '.join(preferred_brands[:2])})")

        # Helper for evaluating numeric >= specs
        def evaluate_numeric_requirement(
            spec_key: str,
            user_val: str,
            weight: float,
            unit_label: str = "",
            spec_name: str = ""
        ):
            nonlocal earned_weight_points, total_possible_weight_points
            total_possible_weight_points += weight
            req_num = parse_first_number(user_val)
            if req_num is None:
                earned_weight_points += 0.7 * weight
                return

            # Find actual value in specs or title
            actual_str = specs.get(spec_name or spec_key, "")
            if not actual_str:
                norm_key = re.sub(r"[\s_-]+", "", spec_key.lower())
                for k, v in specs_lower.items():
                    norm_k = re.sub(r"[\s_-]+", "", k)
                    if norm_key in norm_k or norm_k in norm_key:
                        actual_str = v
                        break

            actual_num = parse_first_number(actual_str)
            if actual_num is None:
                # Try regex on title
                if "ram" in spec_key.lower():
                    m = re.search(r"(\d+)\s*gb\s*(?:ram|lpddr|ddr)", title_lower)
                    if m:
                        actual_num = float(m.group(1))
                    else:
                        slash_m = re.search(r"(\d+)\s*(?:gb|g)\s*[\/,\+]\s*(\d+)\s*(?:gb|g)", title_lower)
                        if slash_m:
                            v1 = float(slash_m.group(1))
                            v2 = float(slash_m.group(2))
                            actual_num = min(v1, v2) if min(v1, v2) <= 24 else None
                        else:
                            m_gram = re.search(r"(\d+)\s*g\s*ram", title_lower)
                            if m_gram:
                                actual_num = float(m_gram.group(1))
                            else:
                                candidates = re.finditer(r"\b(\d+)\s*gb\b(?!\s*(?:storage|rom|ssd|internal))", title_lower)
                                nums = []
                                for c in candidates:
                                    val = float(c.group(1))
                                    if val <= 24:
                                        nums.append(val)
                                if nums:
                                    actual_num = nums[0]
                elif "storage" in spec_key.lower() or "rom" in spec_key.lower() or "ssd" in spec_key.lower():
                    m = re.search(r"(\d+)\s*(?:gb|tb)\s*(?:storage|rom|ssd|internal)", title_lower)
                    if m:
                        val = float(m.group(1))
                        if "tb" in m.group(0) and val <= 16:
                            val *= 1024
                        actual_num = val
                    else:
                        slash_m = re.search(r"(\d+)\s*(?:gb|g)\s*[\/,\+]\s*(\d+)\s*(?:gb|g)", title_lower)
                        if slash_m:
                            v1 = float(slash_m.group(1))
                            v2 = float(slash_m.group(2))
                            actual_num = max(v1, v2) if max(v1, v2) >= 32 else None
                        else:
                            all_matches = re.finditer(r"\b(\d+)\s*(gb|tb)\b", title_lower)
                            stor_candidates = []
                            for mat in all_matches:
                                num = float(mat.group(1))
                                unit = mat.group(2)
                                if unit == "tb" and num <= 16:
                                    num *= 1024
                                if num >= 32:
                                    stor_candidates.append(num)
                            if stor_candidates:
                                actual_num = max(stor_candidates)
                elif "capacity" in spec_key.lower() or "litre" in unit_label.lower():
                    m = re.search(r"(\d+)\s*(?:l|ltr|litre|litres)", title_lower)
                    if m:
                        actual_num = float(m.group(1))
                elif "screen" in spec_key.lower() or "inch" in unit_label.lower():
                    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:inch|\"|-inch)", title_lower)
                    if m:
                        actual_num = float(m.group(1))
                elif "refresh" in spec_key.lower() or "hz" in unit_label.lower():
                    m = re.search(r"(\d+)\s*hz", title_lower)
                    if m:
                        actual_num = float(m.group(1))
                elif "battery" in spec_key.lower() or "mah" in unit_label.lower():
                    m = re.search(r"(\d{4,5})\s*mah", title_lower)
                    if m:
                        actual_num = float(m.group(1))
                elif "power" in spec_key.lower() or "w" in unit_label.lower():
                    m = re.search(r"(\d+)\s*w(?:att)?", title_lower)
                    if m:
                        actual_num = float(m.group(1))
                elif "star" in spec_key.lower():
                    m = re.search(r"(\d+)\s*star", title_lower)
                    if m:
                        actual_num = float(m.group(1))

            if unit_label == "GB/TB":
                if "tb" in user_val.lower() and req_num and req_num <= 16:
                    req_num = req_num * 1024
                if actual_num is not None:
                    check_str = (actual_str or title_lower).lower()
                    if "tb" in check_str and actual_num <= 16:
                        actual_num = actual_num * 1024

            if actual_num is not None:
                if unit_label == "GB/TB":
                    disp_val = f"{int(actual_num/1024) if (actual_num/1024).is_integer() else actual_num/1024} TB" if actual_num >= 1024 else f"{int(actual_num) if actual_num.is_integer() else actual_num} GB"
                else:
                    disp_unit = f" {unit_label}" if unit_label else ""
                    disp_val = f"{int(actual_num) if actual_num.is_integer() else actual_num}{disp_unit}"

                if actual_num >= req_num:
                    earned_weight_points += weight
                    if actual_num > req_num:
                        positive_reasons.append(f"Exceeds your {user_val} requirement with {disp_val}")
                    else:
                        positive_reasons.append(f"Meets your {user_val} requirement ({disp_val})")
                else:
                    earned_weight_points += 0.2 * weight
                    negative_reasons.append(f"{spec_name or spec_key}: {disp_val} (below your {user_val} preference)")
            else:
                # Not available in listing data
                earned_weight_points += 0.5 * weight
                neutral_observations.append(f"{spec_name or spec_key}: Not available in listing specifications")

        # Helper for evaluating categorical specs
        def evaluate_categorical_requirement(
            field_id: str,
            user_val: str,
            weight: float,
            field_label: str = ""
        ):
            nonlocal earned_weight_points, total_possible_weight_points
            total_possible_weight_points += weight
            if not user_val or user_val.lower() in {"any", "not applicable", "flexible"}:
                earned_weight_points += weight
                return

            label = field_label or field_id.title()
            val_clean = user_val.strip().lower()
            norm_val = re.sub(r"[\s_-]+", "", val_clean)
            norm_field = re.sub(r"[\s_-]+", "", field_id.lower())

            # Find matching key in specifications
            actual_val = ""
            for k, v in specs_lower.items():
                norm_k = re.sub(r"[\s_-]+", "", k)
                if norm_field in norm_k or norm_k in norm_field:
                    actual_val = v
                    break
                # Common synonyms
                if field_id == "frost_free" and ("defrost" in norm_k or "frost" in norm_k):
                    actual_val = v
                    break
                if field_id == "display_type" and ("panel" in norm_k or "display" in norm_k):
                    actual_val = v
                    break
                if field_id == "door_type" and "door" in norm_k:
                    actual_val = v
                    break

            raw_tokens = [t for t in re.split(r"[\s/,_-]+", val_clean) if t and t not in {"and", "the", "for", "with", "type", "standard", "only", "pure", "best", "required"}]

            matched = False
            if actual_val:
                norm_actual = re.sub(r"[\s_-]+", "", actual_val)
                if norm_val in norm_actual or norm_actual in norm_val:
                    matched = True
                elif any(t in actual_val for t in raw_tokens):
                    matched = True

                if matched:
                    earned_weight_points += weight
                    positive_reasons.append(f"Matches your {label.lower()} requirement ({actual_val.title()})")
                else:
                    earned_weight_points += 0.2 * weight
                    negative_reasons.append(f"{label}: Listing specifies {actual_val} (you requested {user_val})")
            else:
                # Check in listing title and features
                norm_corpus = re.sub(r"[\s_-]+", "", listing_corpus)
                if norm_val in norm_corpus or any(t in listing_corpus for t in raw_tokens):
                    earned_weight_points += weight
                    positive_reasons.append(f"Matches your {label.lower()} preference ({user_val})")
                else:
                    earned_weight_points += 0.5 * weight
                    neutral_observations.append(f"{label}: Not available in listing specifications")

        # B. Category Specific Evaluation
        if category == "laptop":
            if "ram" in answers:
                evaluate_numeric_requirement("RAM", str(answers["ram"]), weight=1.4, unit_label="GB", spec_name="RAM")
            if "storage" in answers:
                evaluate_numeric_requirement("Storage", str(answers["storage"]), weight=1.1, unit_label="GB/TB", spec_name="Storage")
            if "processor" in answers:
                p_pref = str(answers["processor"]).lower()
                total_possible_weight_points += 1.3
                if p_pref in {"any", ""}:
                    earned_weight_points += 1.3
                elif p_pref == "apple_silicon" and ("apple" in brand_lower or "macbook" in title_lower or "m1" in title_lower or "m2" in title_lower or "m3" in title_lower):
                    earned_weight_points += 1.3
                    positive_reasons.append("Equipped with Apple Silicon for high efficiency")
                elif p_pref == "ryzen" and ("ryzen" in title_lower or "amd" in title_lower):
                    earned_weight_points += 1.3
                    positive_reasons.append("Equipped with AMD Ryzen multi-core processor")
                elif p_pref == "intel" and ("intel" in title_lower or "core i" in title_lower or "ultra" in title_lower):
                    earned_weight_points += 1.3
                    positive_reasons.append("Equipped with Intel Core processor")
                else:
                    proc_val = specs.get("Processor", "")
                    if proc_val:
                        earned_weight_points += 0.3 * 1.3
                        negative_reasons.append(f"Processor: {proc_val} (differs from {answers['processor']})")
                    else:
                        earned_weight_points += 0.6 * 1.3
                        neutral_observations.append("Processor: Specific family not available in listing")
            if "gpu" in answers:
                g_pref = str(answers["gpu"]).lower()
                total_possible_weight_points += 1.3
                has_ded = "rtx" in title_lower or "gtx" in title_lower or "radeon" in title_lower or "graphics" in specs_lower
                if g_pref == "dedicated":
                    if has_ded:
                        earned_weight_points += 1.3
                        positive_reasons.append("Dedicated graphics GPU for gaming & 3D workloads")
                    else:
                        earned_weight_points += 0.2 * 1.3
                        negative_reasons.append("Integrated graphics — lacks requested dedicated gaming GPU")
                elif g_pref == "integrated":
                    if not has_ded:
                        earned_weight_points += 1.3
                        positive_reasons.append("Energy efficient integrated graphics for extended battery")
                    else:
                        earned_weight_points += 0.8 * 1.3
                else:
                    earned_weight_points += 1.3

        elif category == "phone":
            if "ram" in answers:
                evaluate_numeric_requirement("RAM", str(answers["ram"]), weight=1.3, unit_label="GB", spec_name="RAM")
            if "storage" in answers:
                evaluate_numeric_requirement("Storage", str(answers["storage"]), weight=1.2, unit_label="GB", spec_name="Storage")
            if "battery" in answers:
                b_ans = str(answers["battery"]).lower()
                if "5000" in b_ans or "6000" in b_ans:
                    evaluate_numeric_requirement("Battery", b_ans, weight=1.2, unit_label="mAh", spec_name="Battery")
                else:
                    total_possible_weight_points += 1.2
                    earned_weight_points += 1.0
            if "display" in answers:
                d_ans = str(answers["display"]).lower()
                total_possible_weight_points += 1.1
                if "amoled" in d_ans:
                    if "amoled" in listing_corpus or "oled" in listing_corpus:
                        earned_weight_points += 1.1
                        positive_reasons.append("Vibrant AMOLED display with rich contrast")
                    else:
                        earned_weight_points += 0.5 * 1.1
                        neutral_observations.append("Display: AMOLED not confirmed in listing specs")
                else:
                    earned_weight_points += 1.1
            if "connectivity_5g" in answers:
                c_5g_pref = str(answers.get("connectivity_5g", "")).lower()
                c_weight = 1.5 if "5g_required" in c_5g_pref else 1.0
                total_possible_weight_points += c_weight
                has_5g = "5g" in title_lower or "5g" in listing_corpus
                if "5g_required" in c_5g_pref:
                    if has_5g:
                        earned_weight_points += c_weight
                        positive_reasons.append("5G high-speed connectivity verified")
                    else:
                        earned_weight_points += 0.0
                        negative_reasons.append("Lacks verified 5G support (you specified 5G required)")
                else:
                    if has_5g:
                        earned_weight_points += c_weight
                        positive_reasons.append("5G high-speed connectivity included")
                    else:
                        earned_weight_points += 0.8 * c_weight

        elif category == "dress":
            if "fabric" in answers:
                evaluate_categorical_requirement("fabric", str(answers["fabric"]), weight=1.4, field_label="Fabric")
            if "fit" in answers:
                evaluate_categorical_requirement("fit", str(answers["fit"]), weight=1.3, field_label="Silhouette Fit")
            if "pattern" in answers:
                evaluate_categorical_requirement("pattern", str(answers["pattern"]), weight=1.1, field_label="Pattern")
            if "color" in answers:
                evaluate_categorical_requirement("color", str(answers["color"]), weight=1.2, field_label="Color")
            if "size" in answers:
                evaluate_categorical_requirement("size", str(answers["size"]), weight=1.4, field_label="Size")
            if "occasion" in answers:
                evaluate_categorical_requirement("occasion", str(answers["occasion"]), weight=1.2, field_label="Occasion")

        elif category == "shoes":
            if "type" in answers:
                evaluate_categorical_requirement("type", str(answers["type"]), weight=1.4, field_label="Shoe Type")
            if "material" in answers:
                evaluate_categorical_requirement("material", str(answers["material"]), weight=1.2, field_label="Upper Material")
            if "sole" in answers:
                evaluate_categorical_requirement("sole", str(answers["sole"]), weight=1.2, field_label="Sole")
            if "usage" in answers:
                evaluate_categorical_requirement("usage", str(answers["usage"]), weight=1.3, field_label="Usage Activity")
            if "size" in answers:
                evaluate_categorical_requirement("size", str(answers["size"]), weight=1.4, field_label="Shoe Size")
            if "color" in answers:
                evaluate_categorical_requirement("color", str(answers["color"]), weight=1.1, field_label="Color")

        elif category == "tv":
            if "screen_size" in answers:
                evaluate_numeric_requirement("Screen Size", str(answers["screen_size"]), weight=1.4, unit_label="inch", spec_name="Screen Size")
            if "resolution" in answers:
                evaluate_categorical_requirement("resolution", str(answers["resolution"]), weight=1.3, field_label="Resolution")
            if "display_type" in answers:
                evaluate_categorical_requirement("display_type", str(answers["display_type"]), weight=1.3, field_label="Display Panel")
            if "refresh_rate" in answers:
                evaluate_numeric_requirement("Refresh Rate", str(answers["refresh_rate"]), weight=1.1, unit_label="Hz", spec_name="Refresh Rate")
            if "smart_features" in answers:
                evaluate_categorical_requirement("smart_features", str(answers["smart_features"]), weight=1.1, field_label="Smart OS")

        elif category == "refrigerator":
            if "capacity" in answers:
                evaluate_numeric_requirement("Capacity", str(answers["capacity"]), weight=1.4, unit_label="Litres", spec_name="Capacity")
            if "door_type" in answers:
                evaluate_categorical_requirement("door_type", str(answers["door_type"]), weight=1.4, field_label="Door Type")
            if "energy_rating" in answers:
                evaluate_numeric_requirement("Energy Rating", str(answers["energy_rating"]), weight=1.3, unit_label="Star", spec_name="Energy Rating")
            if "inverter" in answers:
                evaluate_categorical_requirement("inverter", str(answers["inverter"]), weight=1.2, field_label="Inverter Technology")
            if "frost_free" in answers:
                evaluate_categorical_requirement("frost_free", str(answers["frost_free"]), weight=1.3, field_label="Defrost System")

        elif category == "headphones":
            if "type" in answers:
                evaluate_categorical_requirement("type", str(answers["type"]), weight=1.4, field_label="Form Factor")
            if "anc" in answers:
                evaluate_categorical_requirement("anc", str(answers["anc"]), weight=1.3, field_label="Noise Cancellation")
            if "battery_life" in answers:
                evaluate_numeric_requirement("battery_life", str(answers["battery_life"]), weight=1.2, unit_label="Hours", spec_name="Battery Life")
            if "bluetooth" in answers:
                evaluate_categorical_requirement("bluetooth", str(answers["bluetooth"]), weight=1.1, field_label="Bluetooth Connectivity")
            if "microphone" in answers:
                evaluate_categorical_requirement("microphone", str(answers["microphone"]), weight=1.2, field_label="Microphone")

        elif category == "camera":
            if "sensor" in answers:
                evaluate_categorical_requirement("sensor", str(answers["sensor"]), weight=1.4, field_label="Sensor Format")
            if "megapixel" in answers:
                evaluate_numeric_requirement("megapixel", str(answers["megapixel"]), weight=1.2, unit_label="MP", spec_name="Megapixel")
            if "lens" in answers:
                evaluate_categorical_requirement("lens", str(answers["lens"]), weight=1.3, field_label="Lens Setup")
            if "video_resolution" in answers:
                evaluate_categorical_requirement("video_resolution", str(answers["video_resolution"]), weight=1.3, field_label="Video Resolution")
            if "stabilization" in answers:
                evaluate_categorical_requirement("stabilization", str(answers["stabilization"]), weight=1.2, field_label="Image Stabilization")

        elif category == "smartwatch":
            if "display" in answers:
                evaluate_categorical_requirement("display", str(answers["display"]), weight=1.3, field_label="Display")
            if "battery" in answers:
                evaluate_categorical_requirement("battery", str(answers["battery"]), weight=1.3, field_label="Battery Life")
            if "gps" in answers:
                evaluate_categorical_requirement("gps", str(answers["gps"]), weight=1.2, field_label="GPS")
            if "calling" in answers:
                evaluate_categorical_requirement("calling", str(answers["calling"]), weight=1.3, field_label="Bluetooth Calling")
            if "health_features" in answers:
                evaluate_categorical_requirement("health_features", str(answers["health_features"]), weight=1.3, field_label="Health Features")

        elif category == "furniture":
            if "material" in answers:
                evaluate_categorical_requirement("material", str(answers["material"]), weight=1.4, field_label="Material")
            if "size" in answers:
                evaluate_categorical_requirement("size", str(answers["size"]), weight=1.3, field_label="Dimensions")
            if "style" in answers:
                evaluate_categorical_requirement("style", str(answers["style"]), weight=1.2, field_label="Design Style")
            if "color" in answers:
                evaluate_categorical_requirement("color", str(answers["color"]), weight=1.1, field_label="Color Finish")
            if "storage" in answers:
                evaluate_categorical_requirement("storage", str(answers["storage"]), weight=1.2, field_label="Storage")

        elif category == "kitchen_appliances":
            if "type" in answers:
                evaluate_categorical_requirement("type", str(answers["type"]), weight=1.4, field_label="Appliance Type")
            if "capacity" in answers:
                evaluate_categorical_requirement("capacity", str(answers["capacity"]), weight=1.3, field_label="Capacity")
            if "power" in answers:
                evaluate_numeric_requirement("power", str(answers["power"]), weight=1.2, unit_label="W", spec_name="Power")
            if "features" in answers:
                evaluate_categorical_requirement("features", str(answers["features"]), weight=1.2, field_label="Features")

        elif category == "washing_machine":
            if "machine_type" in answers:
                evaluate_categorical_requirement("machine_type", str(answers["machine_type"]), weight=1.4, field_label="Machine Type")
            if "capacity" in answers:
                evaluate_numeric_requirement("capacity", str(answers["capacity"]), weight=1.3, unit_label="kg", spec_name="Capacity")
            if "inverter" in answers:
                evaluate_categorical_requirement("inverter", str(answers["inverter"]), weight=1.2, field_label="Inverter Motor")

        elif category == "skincare":
            skin_concern = answers.get("skin_concern", "general_glow")
            total_possible_weight_points += 1.5
            actives = specs.get("Key Actives", "") or specs.get("Ingredients", "")
            if skin_concern == "oily_acne":
                if "Salicylic" in actives or "Tea Tree" in actives or "Niacinamide" in actives or "salicylic" in title_lower or "acne" in title_lower:
                    earned_weight_points += 1.5
                    positive_reasons.append("Formulated with active ingredients targeting acne and oil control")
                else:
                    earned_weight_points += 0.4 * 1.5
                    negative_reasons.append("Does not specifically target acne control or pore congestion")
            elif skin_concern == "hyperpigmentation":
                if "Niacinamide" in actives or "Vitamin C" in actives or "Arbutin" in actives:
                    earned_weight_points += 1.5
                    positive_reasons.append("Contains actives proven to fade dark spots and even skin tone")
                else:
                    earned_weight_points += 0.5 * 1.5
            else:
                earned_weight_points += 1.2

            avoid_list = answers.get("avoid_ingredients", [])
            if avoid_list:
                total_possible_weight_points += 1.2
                avoid_violation = any(avoid.lower() in listing_corpus for avoid in avoid_list)
                if not avoid_violation:
                    earned_weight_points += 1.2
                    positive_reasons.append("Free from your requested avoided ingredients")
                else:
                    earned_weight_points += 0.2 * 1.2
                    negative_reasons.append("Contains ingredients you requested to avoid")

        else:
            # Generic fallback scoring
            total_possible_weight_points += 2.0
            earned_weight_points += 1.8
            positive_reasons.append("Solid feature set aligning with your search requirements")

        # Fallback if no questions answered
        if total_possible_weight_points <= 0.0:
            total_possible_weight_points = 1.0
            earned_weight_points = 0.9

        # Calculate Requirement Match %
        req_match_pct = round(min(100.0, max(0.0, (earned_weight_points / total_possible_weight_points) * 100.0)), 1)
        scoring_explanations["requirement_match"] = f"Matches {req_match_pct:.0f}% of your stated preferences"

        # 3. Rating and Review Confidence Scores
        rating = product.review_analysis.combined_rating if product.review_analysis and product.review_analysis.combined_rating is not None else product.rating
        review_count = product.review_analysis.total_reviews_analyzed if product.review_analysis else (product.review_count or 0)
        review_confidence_score = (
            round(min(100.0, (math.log10(max(1, review_count)) / 4.0) * 100.0), 1)
            if review_count > 0 else 0.0
        )
        
        if rating is not None and rating > 0:
            rating_score = round((rating / 5.0) * 100.0, 1)
            scoring_explanations["rating"] = f"Customer rating: {rating:.1f}/5.0★ with {review_count:,} reviews"
            
            if rating >= 4.3 and review_count >= 500:
                positive_reasons.append(f"Verified customer satisfaction ({rating:.1f}★ across {review_count:,} reviews on {product.marketplace})")
            elif rating < 3.8:
                negative_reasons.append(f"Average rating of {rating:.1f}★ suggests mixed customer feedback")
        else:
            rating_score = 0.0
            scoring_explanations["rating"] = "No customer ratings published by source for this listing"
            neutral_observations.append(f"Rating data not provided by {product.marketplace}")

        # 4. Calculate Value for Money Score
        cat_base_prices = {
            "laptop": 60000.0, "phone": 28000.0, "skincare": 700.0, "headphones": 4500.0,
            "dress": 2200.0, "shoes": 3500.0, "tv": 40000.0, "refrigerator": 28000.0,
            "smartwatch": 4000.0, "furniture": 12000.0, "kitchen_appliances": 5500.0
        }
        base_p = target_budget if target_budget > 0 else cat_base_prices.get(category, 10000.0)
        
        if product.current_price and product.current_price > 0:
            price_val_ratio = base_p / product.current_price
            vfm_raw = (req_match_pct * 0.4) + (rating_score * 0.3) + (min(150.0, price_val_ratio * 100.0) * 0.3)
            # If product exceeds target budget by > 15%, dampen vfm_score
            if target_budget > 0 and product.current_price > target_budget * 1.15:
                over_ratio = (product.current_price - target_budget) / target_budget
                vfm_raw = max(25.0, vfm_raw - (over_ratio * 20.0))
            vfm_score = round(min(100.0, max(25.0, vfm_raw)), 1)
        else:
            vfm_score = 0.0
            
        if vfm_score >= 84:
            vfm_label = "Excellent"
        elif vfm_score >= 72:
            vfm_label = "Great"
        elif vfm_score >= 60:
            vfm_label = "Good"
        else:
            vfm_label = "Fair"
        scoring_explanations["price_value"] = f"Value rating: {vfm_label} ({vfm_score:.0f}/100)"

        # 5. Availability & Source Reliability Scores
        availability = (product.availability or "").strip().lower()
        if availability in {"in stock", "in_stock", "available"}:
            availability_score = 100.0
        elif availability in {"out of stock", "out_of_stock", "unavailable"}:
            availability_score = 0.0
        else:
            availability_score = 0.0
        source_reliability_score = 95.0 if any(p in product.provider for p in ["amazon", "flipkart", "croma", "open_beauty"]) else 85.0
        scoring_explanations["availability"] = f"Availability: {product.availability} on {product.marketplace}"
        scoring_explanations["source_reliability"] = f"Source: {product.source or product.marketplace}"

        neutral_observations.append(f"Offered on {product.marketplace} ({product.seller or 'Authorized Merchant'})")
        if product.specifications:
            spec_summary = ", ".join([f"{k}: {v}" for k, v in list(product.specifications.items())[:3]])
            neutral_observations.append(f"Key Specifications: {spec_summary}")

        # 6. Overall TrustRank Score Formula (0 - 100)
        # Weights: Requirement (35%) + Price/Value (25%) + Rating/Confidence (20%) + Availability (20%).
        has_rating = (rating is not None and rating > 0)
        rating_combined = ((rating_score * 0.6) + (review_confidence_score * 0.4)) if has_rating else 0.0
        avail_combined = availability_score
        
        if has_rating:
            overall_score = round(
                (req_match_pct * 0.35) +
                (vfm_score * 0.25) +
                (rating_combined * 0.20) +
                (avail_combined * 0.20),
                1
            )
        else:
            # Re-normalize over requirement (45%), VFM (30%), availability (25%) when marketplace omitted rating
            overall_score = round(
                (req_match_pct * 0.45) +
                (vfm_score * 0.30) +
                (avail_combined * 0.25),
                1
            )
        
        # Apply Brand preference bonus or deduction
        if preferred_brands and isinstance(preferred_brands, list) and len(preferred_brands) > 0:
            if matched_brand:
                overall_score += 4.0
            else:
                overall_score -= 5.0
                
        # Apply 5G requirement penalty if missing
        if "5g_required" in str(answers.get("connectivity_5g", "")).lower() and not ("5g" in title_lower or "5g" in listing_corpus):
            overall_score -= 8.0

        # Budget penalties for exceeding max_price or falling below min_price
        effective_max = max_price if max_price > 0 else target_budget
        if effective_max > 0 and product.current_price and product.current_price > effective_max:
            over_ratio = (product.current_price - effective_max) / effective_max
            if over_ratio > 0.15:
                # Progressive penalty up to 35 points
                budget_penalty = min(35.0, round((over_ratio - 0.15) * 25.0, 1))
                overall_score = round(max(15.0, overall_score - budget_penalty), 1)

        if min_price > 0 and product.current_price and product.current_price < min_price:
            under_ratio = (min_price - product.current_price) / min_price
            if under_ratio > 0.15:
                under_penalty = min(35.0, round((under_ratio - 0.15) * 30.0, 1))
                overall_score = round(max(15.0, overall_score - under_penalty), 1)

        overall_score = min(100.0, max(0.0, overall_score))

        # Personalized Narrative ("Best For You" Explanation)
        best_for_you_parts = [
            f"Based on your requirements, the **{product.title}** achieves a **{req_match_pct:.0f}% requirement match**."
        ]
        if b_pos:
            best_for_you_parts.append(b_pos[0] + ".")
        elif b_neg:
            best_for_you_parts.append(b_neg[0] + ".")

        # Highlight key matched specs
        top_pos = [p for p in positive_reasons if not p.startswith("Fits your") and not p.startswith("Well under")][:2]
        if top_pos:
            best_for_you_parts.append(" ".join(top_pos) + ".")

        if negative_reasons:
            top_neg = negative_reasons[0]
            if not top_neg.startswith("Slightly above") and not top_neg.startswith("Exceeds target"):
                best_for_you_parts.append(f"Trade-off: {top_neg}.")

        best_for_you_parts.append(f"Verified live listing on {product.marketplace} with {product.availability or 'available'} stock status.")
        best_for_you_explanation = " ".join(best_for_you_parts)

        return ScoredRecommendation(
            product=product,
            trustrank_score=overall_score,
            requirement_match_percentage=req_match_pct,
            budget_fit_score=budget_score,
            value_for_money=vfm_label,
            value_for_money_score=vfm_score,
            requirement_match_score=req_match_pct,
            price_value_score=vfm_score,
            rating_score=rating_score,
            review_confidence_score=review_confidence_score,
            availability_score=availability_score,
            source_reliability_score=source_reliability_score,
            scoring_breakdown_explanation=scoring_explanations,
            positive_reasons=positive_reasons[:4],
            negative_reasons=negative_reasons[:3],
            neutral_observations=neutral_observations[:3],
            best_for_you_explanation=best_for_you_explanation,
            category_badges=[],
            marketplace_comparison=ComparisonService.marketplace_offers(product)
        )

    @staticmethod
    def _is_sufficient_data_for_best_value(product: NormalizedProduct) -> bool:
        """
        Determines whether the product has genuine, sufficient data to warrant
        an authentic 'Best Value' evaluation.
        Never invents missing data. Requires real price > 0, real rating >= 3.5,
        and real specifications or features.
        """
        if not product.current_price or product.current_price <= 0:
            return False
        if product.rating is None or product.rating < 3.5:
            return False
        has_specs = bool(product.specifications and len(product.specifications) > 0)
        has_features = bool(product.features and len(product.features) >= 1)
        if not (has_specs or has_features):
            return False
        return True

    @classmethod
    def rank_and_assign_badges(
        cls,
        recommendations: List[ScoredRecommendation],
        target_budget: float = 0.0,
        min_price: float = 0.0,
        max_price: float = 0.0
    ) -> List[ScoredRecommendation]:
        if not recommendations:
            return []

        if max_price <= 0 and target_budget > 0:
            max_price = target_budget

        # Sort primarily by TrustRank score descending
        sorted_recs = sorted(recommendations, key=lambda r: r.trustrank_score, reverse=True)

        # 1. Best for You -> Top TrustRank recommendation that fits the min and max price range
        best_for_you = None
        for r in sorted_recs:
            if r.product.current_price:
                price = r.product.current_price
                in_min = (min_price <= 0 or price >= min_price * 0.85)
                in_max = (max_price <= 0 or price <= max_price * 1.15)
                if in_min and in_max:
                    best_for_you = r
                    break
        if not best_for_you and sorted_recs:
            best_for_you = sorted_recs[0]

        if best_for_you:
            best_for_you.category_badges.append("Best for You")

        # 2. Best Value -> Real data sufficiency check (genuine price, rating >= 3.5, specs/features, and available offers)
        # If there is insufficient data, do not display a Best Value label.
        val_candidates = []
        for r in sorted_recs:
            if r.category_badges:
                continue
            p = r.product
            # Check data sufficiency: never invent missing data
            if not cls._is_sufficient_data_for_best_value(p):
                continue
            # Budget adherence
            if min_price > 0 and p.current_price < min_price * 0.85:
                continue
            if max_price > 0 and p.current_price > max_price * 1.15:
                continue
            val_candidates.append(r)

        if val_candidates:
            # Score each candidate using existing VFM, trustrank score, real discount/offer boost, and spec richness
            def calc_best_value_metric(rec: ScoredRecommendation) -> float:
                prod = rec.product
                metric = (rec.value_for_money_score * 0.40) + (rec.trustrank_score * 0.30) + ((prod.rating or 4.0) * 4.0)
                # Boost if real merchant discount exists
                if prod.original_price and prod.original_price > prod.current_price:
                    discount_pct = ((prod.original_price - prod.current_price) / prod.original_price) * 100.0
                    metric += min(12.0, discount_pct * 0.25)
                # Boost if product has verified marketplace offers
                if prod.offers and len(prod.offers) > 1:
                    metric += 4.0
                return metric

            best_val = max(val_candidates, key=calc_best_value_metric)
            if calc_best_value_metric(best_val) >= 55.0:
                best_val.category_badges.append("Best Value")
        # If no candidates meet the data sufficiency criteria, DO NOT display a Best Value label.

        # 3. Best Reviewed -> Highest rating * log(reviews) (prioritizing price range)
        rated_recs = [
            r for r in sorted_recs 
            if r.product.rating is not None and r.product.rating > 0 and not r.category_badges
            and (
                (min_price <= 0 or not r.product.current_price or r.product.current_price >= min_price * 0.85) and
                (max_price <= 0 or not r.product.current_price or r.product.current_price <= max_price * 1.25)
            )
        ]
        if not rated_recs:
            rated_recs = [r for r in sorted_recs if r.product.rating is not None and r.product.rating > 0 and not r.category_badges]
        if rated_recs:
            best_rev = max(rated_recs, key=lambda r: r.product.rating * math.log10(max(10, r.product.review_count or 10)))
            best_rev.category_badges.append("Best Reviewed")
        elif len(sorted_recs) > 2:
            remaining = [r for r in rated_recs if not r.category_badges]
            if remaining:
                remaining_best_rev = max(remaining, key=lambda r: (r.product.rating or 0.0))
                remaining_best_rev.category_badges.append("Best Reviewed")

        # 4. Best Alternative -> High rank with a different brand or distinct feature
        top_brand = (best_for_you.product.brand or "") if best_for_you else ""
        alt_candidates = [r for r in sorted_recs if r.product.brand != top_brand and not r.category_badges]
        if alt_candidates:
            alt_candidates[0].category_badges.append("Best Alternative")
        else:
            remaining = [r for r in sorted_recs if not r.category_badges]
            if remaining:
                remaining[0].category_badges.append("Best Alternative")

        return sorted_recs
