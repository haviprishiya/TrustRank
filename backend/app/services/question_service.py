from typing import List, Dict, Any, Optional
from app.models.schemas import RequirementQuestion, QuestionOption, SearchIntent
from app.services.intent_service import CATEGORY_DEFINITIONS

class QuestionService:
    @staticmethod
    def get_questions_for_intent(intent: SearchIntent) -> List[RequirementQuestion]:
        cat = intent.detected_category
        budget = intent.extracted_budget
        brands = intent.extracted_brands
        features = intent.extracted_features
        use_case = intent.target_audience_or_use
        
        questions = []
        
        if cat == "laptop":
            # 1. Budget Question
            default_b = budget if budget else 65000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="We'll find the best performance and value within this price in INR",
                type="range_slider",
                min_value=25000.0,
                max_value=250000.0,
                step=5000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Primary Use Case
            default_use = "gaming" if "Gaming" in features else ("programming" if "Programming / Coding" in features else "all_round")
            questions.append(RequirementQuestion(
                id="primary_use",
                question="What will you mainly use it for?",
                subtext="This determines CPU, GPU, and thermal requirements",
                type="single_choice",
                options=[
                    QuestionOption(value="gaming", label="Gaming & Heavy 3D", icon="Gamepad2", badge="High GPU", description="AAA Gaming, esports, ray tracing"),
                    QuestionOption(value="programming", label="Coding & Development", icon="Code", badge="CPU/RAM", description="IDEs, Docker, compilation, multitasking"),
                    QuestionOption(value="editing", label="Video/Photo Editing", icon="Film", badge="Color & Power", description="Premiere Pro, DaVinci, color accurate"),
                    QuestionOption(value="office", label="Office Work & Business", icon="Briefcase", badge="Reliability", description="Excel, presentations, Zoom, multitasking"),
                    QuestionOption(value="student", label="College & Daily Study", icon="GraduationCap", badge="Battery", description="Long battery, lightweight, notes"),
                    QuestionOption(value="all_round", label="General Everyday Use", icon="Laptop", badge="Balanced", description="Browsing, streaming, media, light work")
                ],
                default_value=default_use,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Preferred RAM
            questions.append(RequirementQuestion(
                id="ram",
                question="Preferred RAM capacity?",
                subtext="Higher RAM ensures seamless multitasking without slowdowns",
                type="single_choice",
                options=[
                    QuestionOption(value="8GB", label="8 GB", description="Good for basic browsing & office tasks"),
                    QuestionOption(value="16GB", label="16 GB (Recommended)", badge="Sweet Spot", description="Standard for smooth coding, gaming & creative work"),
                    QuestionOption(value="32GB", label="32 GB+", badge="Power User", description="Heavy virtualization, 4K editing & extreme workloads")
                ],
                default_value="16GB",
                importance_weight=1.2,
                category=cat
            ))
            
            # 4. Preferred Storage
            questions.append(RequirementQuestion(
                id="storage",
                question="Preferred SSD Storage?",
                subtext="Fast NVMe SSD storage capacity for OS and files",
                type="single_choice",
                options=[
                    QuestionOption(value="512GB", label="512 GB SSD", description="Standard capacity for most users"),
                    QuestionOption(value="1TB", label="1 TB SSD", badge="Popular", description="Ample room for large games and projects"),
                    QuestionOption(value="2TB", label="2 TB SSD", description="Massive space for offline raw media and games")
                ],
                default_value="512GB",
                importance_weight=1.0,
                category=cat
            ))
            
            # 5. Priority: Performance vs Battery vs Portability
            questions.append(RequirementQuestion(
                id="priority",
                question="What is your top priority?",
                subtext="Choose what matters most in your daily use",
                type="single_choice",
                options=[
                    QuestionOption(value="performance", label="Max Performance", icon="Zap", description="Raw processing power and dedicated graphics"),
                    QuestionOption(value="battery", label="All-Day Battery Life", icon="BatteryCharging", description="8-12+ hours on a single charge"),
                    QuestionOption(value="portability", label="Thin & Lightweight", icon="Feather", description="Easy to carry in a backpack all day"),
                    QuestionOption(value="display", label="Display & Build Quality", icon="Eye", description="High refresh rate, OLED/IPS, metal chassis")
                ],
                default_value="performance" if "Gaming" in features else "portability",
                importance_weight=1.1,
                category=cat
            ))
            
            # 6. Preferred Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Any preferred brands?",
                subtext="Leave empty or select your trusted manufacturers",
                type="chip_select",
                options=[
                    QuestionOption(value="Apple", label="Apple (MacBook)"),
                    QuestionOption(value="ASUS", label="ASUS / ROG"),
                    QuestionOption(value="Lenovo", label="Lenovo / Legion"),
                    QuestionOption(value="HP", label="HP / OMEN"),
                    QuestionOption(value="Dell", label="Dell / Alienware"),
                    QuestionOption(value="Acer", label="Acer / Predator"),
                    QuestionOption(value="Samsung", label="Samsung Galaxy Book"),
                    QuestionOption(value="MSI", label="MSI")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "phone":
            # 1. Budget Question
            default_b = budget if budget else 30000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="We'll scan live smartphone prices in INR",
                type="range_slider",
                min_value=8000.0,
                max_value=160000.0,
                step=2000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Main Purpose
            default_purpose = "camera" if "High Quality Camera" in features else ("gaming" if "Gaming" in features else "balanced")
            questions.append(RequirementQuestion(
                id="primary_use",
                question="What is your main priority for this phone?",
                subtext="Help us focus on the right sensor, chipset, or battery spec",
                type="single_choice",
                options=[
                    QuestionOption(value="camera", label="Pro Photography & Video", icon="Camera", badge="Top Sensors", description="OIS, natural skin tones, 4K 60fps video, low light"),
                    QuestionOption(value="gaming", label="High-End Gaming", icon="Gamepad2", badge="High FPS", description="Flagship chipset, cooling system, 120Hz display"),
                    QuestionOption(value="battery", label="Battery Endurance & Charging", icon="Battery", badge="2-Day Life", description="5000mAh+, 65W-120W fast charging in minutes"),
                    QuestionOption(value="software", label="Clean OS & Long Updates", icon="ShieldCheck", badge="Smooth", description="No bloatware, 4-7 years of OS updates"),
                    QuestionOption(value="balanced", label="Everyday All-Rounder", icon="Smartphone", badge="Best Value", description="Reliable daily performance, good camera, great screen")
                ],
                default_value=default_purpose,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Camera Importance
            questions.append(RequirementQuestion(
                id="camera_importance",
                question="How important is camera quality to you?",
                subtext="Do you need flagship zoom/ultrawide or just clear casual photos?",
                type="single_choice",
                options=[
                    QuestionOption(value="essential", label="Crucial / Best in Class", badge="Flagship OIS", description="Must have excellent portrait, night mode & 4K video"),
                    QuestionOption(value="moderate", label="Good Quality for Social Media", description="Crisp daytime shots, good selfies, solid HDR"),
                    QuestionOption(value="basic", label="Basic Casual Snaps", description="Document scanning, casual photos are sufficient")
                ],
                default_value="essential" if "High Quality Camera" in features else "moderate",
                importance_weight=1.2,
                category=cat
            ))
            
            # 4. Preferred Storage
            questions.append(RequirementQuestion(
                id="storage",
                question="Preferred Internal Storage?",
                subtext="Storage for high-res photos, 4K videos, and apps",
                type="single_choice",
                options=[
                    QuestionOption(value="128GB", label="128 GB", description="Sufficient for light app usage"),
                    QuestionOption(value="256GB", label="256 GB (Recommended)", badge="Sweet Spot", description="Plenty of space for photos, games & offline media"),
                    QuestionOption(value="512GB", label="512 GB+", description="Massive space for high-res video recording")
                ],
                default_value="256GB",
                importance_weight=1.0,
                category=cat
            ))
            
            # 5. Preferred Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred smartphone brands?",
                subtext="Select specific brands or leave open to discover the best match",
                type="chip_select",
                options=[
                    QuestionOption(value="Apple", label="Apple (iPhone)"),
                    QuestionOption(value="Samsung", label="Samsung Galaxy"),
                    QuestionOption(value="OnePlus", label="OnePlus"),
                    QuestionOption(value="Google", label="Google Pixel"),
                    QuestionOption(value="Xiaomi", label="Xiaomi / Redmi"),
                    QuestionOption(value="iQOO", label="iQOO"),
                    QuestionOption(value="Nothing", label="Nothing Phone"),
                    QuestionOption(value="Motorola", label="Motorola"),
                    QuestionOption(value="Realme", label="Realme"),
                    QuestionOption(value="Vivo", label="Vivo")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "skincare":
            # 1. Product Type Looking For
            questions.append(RequirementQuestion(
                id="product_type",
                question="What specific skincare product are you looking for?",
                subtext="Select the step in your routine",
                type="single_choice",
                options=[
                    QuestionOption(value="face_wash", label="Face Wash / Cleanser", icon="Sparkles", description="Gel, foam, or gentle hydrating cleansers"),
                    QuestionOption(value="moisturizer", label="Moisturizer / Cream", icon="Droplets", description="Oil-free, ceramide, or barrier repair creams"),
                    QuestionOption(value="sunscreen", label="Sunscreen / SPF", icon="Sun", description="Broad spectrum SPF 50+ PA++++, matte or dewy"),
                    QuestionOption(value="serum", label="Treatment Serum", icon="FlaskConical", description="Targeted actives for pigmentation, glow, or acne"),
                    QuestionOption(value="toner", label="Toner / Exfoliant", icon="Layers", description="Hydrating or AHA/BHA pore refining toners")
                ],
                default_value="face_wash" if "face wash" in intent.raw_query.lower() else "serum",
                importance_weight=1.4,
                category=cat
            ))
            
            # 2. Main Skin Concern
            default_concern = "oily_acne" if ("oily" in intent.raw_query.lower() or "acne" in intent.raw_query.lower()) else "general_glow"
            questions.append(RequirementQuestion(
                id="skin_concern",
                question="What is your primary skin concern?",
                subtext="This ensures active ingredients match your specific dermatological goal",
                type="single_choice",
                options=[
                    QuestionOption(value="oily_acne", label="Acne, Breakouts & Excess Oil", badge="Salicylic / Tea Tree", description="Pore congestion, active pimples, blackheads"),
                    QuestionOption(value="hyperpigmentation", label="Dark Spots & Pigmentation", badge="Niacinamide / Alpha Arbutin", description="Uneven tone, sun spots, post-acne marks"),
                    QuestionOption(value="dryness", label="Dryness, Flakiness & Barrier Repair", badge="Ceramides / Hyaluronic", description="Dehydrated skin, damaged barrier, tight feeling"),
                    QuestionOption(value="sensitive", label="Sensitivity & Redness", badge="Centella / Cica", description="Easily irritated, rosacea, fragrance intolerance"),
                    QuestionOption(value="anti_aging", label="Fine Lines & Firmness", badge="Retinol / Peptides", description="Elasticity loss, aging prevention, texture"),
                    QuestionOption(value="general_glow", label="Daily Hydration & Natural Glow", badge="Vitamin C", description="Healthy radiance and balanced daily maintenance")
                ],
                default_value=default_concern,
                importance_weight=1.5,
                category=cat
            ))
            
            # 3. Budget
            default_b = budget if budget else 750.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for a standard bottle/pack",
                type="range_slider",
                min_value=200.0,
                max_value=4000.0,
                step=50.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.2,
                category=cat
            ))
            
            # 4. Preferred Active Ingredients
            questions.append(RequirementQuestion(
                id="preferred_ingredients",
                question="Preferred active ingredients?",
                subtext="Select actives you love",
                type="chip_select",
                options=[
                    QuestionOption(value="Salicylic Acid", label="Salicylic Acid (BHA)"),
                    QuestionOption(value="Niacinamide", label="Niacinamide (Vitamin B3)"),
                    QuestionOption(value="Hyaluronic Acid", label="Hyaluronic Acid"),
                    QuestionOption(value="Vitamin C", label="Vitamin C"),
                    QuestionOption(value="Ceramides", label="Ceramides"),
                    QuestionOption(value="Retinol", label="Retinol"),
                    QuestionOption(value="Centella Asiatica", label="Centella / Cica"),
                    QuestionOption(value="Tea Tree", label="Tea Tree")
                ],
                default_value=["Salicylic Acid", "Niacinamide"] if default_concern == "oily_acne" else [],
                importance_weight=1.1,
                category=cat
            ))
            
            # 5. Ingredients to Avoid
            questions.append(RequirementQuestion(
                id="avoid_ingredients",
                question="Ingredients you want to avoid?",
                subtext="We will filter out formulations containing these",
                type="chip_select",
                options=[
                    QuestionOption(value="Fragrance", label="Added Fragrance / Perfume"),
                    QuestionOption(value="Alcohol", label="Drying Alcohols"),
                    QuestionOption(value="Parabens", label="Parabens"),
                    QuestionOption(value="Sulfates", label="Sulfates (SLS/SLES)"),
                    QuestionOption(value="Essential Oils", label="Essential Oils"),
                    QuestionOption(value="Mineral Oil", label="Mineral Oil")
                ],
                default_value=["Fragrance", "Parabens"],
                importance_weight=1.2,
                category=cat
            ))
            
            # 6. Preferred Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred skincare brands?",
                subtext="Select trusted dermatology or science-backed brands",
                type="chip_select",
                options=[
                    QuestionOption(value="Minimalist", label="Minimalist (Be Minimalist)"),
                    QuestionOption(value="Cetaphil", label="Cetaphil"),
                    QuestionOption(value="The Ordinary", label="The Ordinary"),
                    QuestionOption(value="Plum", label="Plum Green Tea / Goodness"),
                    QuestionOption(value="Neutrogena", label="Neutrogena"),
                    QuestionOption(value="CeraVe", label="CeraVe"),
                    QuestionOption(value="Derma Co", label="The Derma Co"),
                    QuestionOption(value="Bioderma", label="Bioderma"),
                    QuestionOption(value="Dot & Key", label="Dot & Key")
                ],
                default_value=brands if brands else [],
                importance_weight=0.8,
                category=cat
            ))

        elif cat == "headphones":
            default_b = budget if budget else 6000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for wireless or audiophile headphones",
                type="range_slider",
                min_value=1000.0,
                max_value=35000.0,
                step=500.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="form_factor",
                question="Preferred audio form factor?",
                subtext="Choose how you prefer to wear them",
                type="single_choice",
                options=[
                    QuestionOption(value="tws", label="True Wireless Earbuds (TWS)", icon="Headphones", badge="Pocketable", description="Compact charging case, in-ear comfort"),
                    QuestionOption(value="over_ear", label="Over-Ear Headphones", icon="Headphones", badge="Max ANC & Bass", description="Plush earcups, deep immersive sound, best noise cancellation"),
                    QuestionOption(value="neckband", label="Wireless Neckband", icon="Radio", badge="Long Battery", description="Magnetic buds, stays secure around your neck"),
                    QuestionOption(value="wired_iem", label="Audiophile Wired IEMs", icon="AudioWaveform", badge="Pure Hi-Res", description="Zero latency, lossless DAC fidelity")
                ],
                default_value="over_ear" if "over ear" in intent.raw_query.lower() else "tws",
                importance_weight=1.3,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="key_features",
                question="Key features you care about most?",
                subtext="Select must-have technologies",
                type="chip_select",
                options=[
                    QuestionOption(value="anc", label="Active Noise Cancellation (ANC)"),
                    QuestionOption(value="mic_calls", label="Crystal Clear Mic for Calls/Meetings"),
                    QuestionOption(value="battery", label="30+ Hours Battery Life"),
                    QuestionOption(value="multipoint", label="Dual Device Multipoint Pairing"),
                    QuestionOption(value="low_latency", label="Low Latency Gaming Mode"),
                    QuestionOption(value="waterproof", label="IPX5+ Sweat & Waterproof for Gym")
                ],
                default_value=["anc", "battery"],
                importance_weight=1.2,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred audio brands?",
                subtext="Select brands known for sound tuning",
                type="chip_select",
                options=[
                    QuestionOption(value="Sony", label="Sony (Industry leading ANC)"),
                    QuestionOption(value="Bose", label="Bose (Supreme comfort & ANC)"),
                    QuestionOption(value="Sennheiser", label="Sennheiser (Audiophile acoustic)"),
                    QuestionOption(value="JBL", label="JBL (Signature deep bass)"),
                    QuestionOption(value="OnePlus", label="OnePlus Bullets / Buds"),
                    QuestionOption(value="Realme", label="Realme Buds Air"),
                    QuestionOption(value="boAt", label="boAt (Budget bass)"),
                    QuestionOption(value="Apple", label="Apple AirPods")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "camera":
            default_b = budget if budget else 65000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Budget in INR for body or kit lens combo",
                type="range_slider",
                min_value=25000.0,
                max_value=250000.0,
                step=5000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="primary_use",
                question="What will you primarily shoot?",
                subtext="Helps match autofocus speed, sensor size, and video capabilities",
                type="single_choice",
                options=[
                    QuestionOption(value="vlogging", label="Vlogging & YouTube 4K", icon="Video", description="Flip screen, sharp eye AF, microphone input"),
                    QuestionOption(value="travel", label="Travel & Street Photography", icon="Compass", description="Compact, lightweight, weather-sealed"),
                    QuestionOption(value="portrait", label="Portraits & Studio Photography", icon="User", description="Crisp bokeh, high dynamic range, great color science"),
                    QuestionOption(value="action", label="Sports, Wildlife & Fast Action", icon="Zap", description="Fast burst FPS, super telephoto reach, fast tracking")
                ],
                default_value="vlogging",
                importance_weight=1.3,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred camera brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Sony", label="Sony Alpha"),
                    QuestionOption(value="Canon", label="Canon EOS"),
                    QuestionOption(value="Nikon", label="Nikon Z"),
                    QuestionOption(value="Fujifilm", label="Fujifilm X"),
                    QuestionOption(value="GoPro", label="GoPro Action")
                ],
                default_value=brands if brands else [],
                importance_weight=1.0,
                category=cat
            ))

        elif cat == "tv":
            default_b = budget if budget else 45000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for smart TV",
                type="range_slider",
                min_value=12000.0,
                max_value=180000.0,
                step=2000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="screen_size",
                question="Desired Screen Size?",
                subtext="Choose based on room viewing distance",
                type="single_choice",
                options=[
                    QuestionOption(value="32-43", label="32\" - 43\" (Small/Bedrooms)"),
                    QuestionOption(value="50-55", label="50\" - 55\" (Most Popular for Living Rooms)", badge="Sweet Spot"),
                    QuestionOption(value="65+", label="65\"+ (Cinema & Large Hall Experience)")
                ],
                default_value="50-55",
                importance_weight=1.3,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="display_tech",
                question="Preferred Display Panel?",
                type="single_choice",
                options=[
                    QuestionOption(value="oled", label="OLED (Perfect blacks, infinite contrast)", badge="Premium"),
                    QuestionOption(value="qled", label="QLED / Mini-LED (Vibrant colors, ultra bright)", badge="Bright Room"),
                    QuestionOption(value="4k_led", label="4K Ultra HD LED (Best Value)", badge="Value")
                ],
                default_value="4k_led",
                importance_weight=1.2,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred TV brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Sony", label="Sony Bravia"),
                    QuestionOption(value="Samsung", label="Samsung QLED/Crystal"),
                    QuestionOption(value="LG", label="LG OLED/NanoCell"),
                    QuestionOption(value="TCL", label="TCL QLED"),
                    QuestionOption(value="Xiaomi", label="Xiaomi / Mi TV"),
                    QuestionOption(value="OnePlus", label="OnePlus TV")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "washing_machine":
            default_b = budget if budget else 28000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                type="range_slider",
                min_value=10000.0,
                max_value=60000.0,
                step=1000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="machine_type",
                question="Washing Machine Type?",
                type="single_choice",
                options=[
                    QuestionOption(value="front_load", label="Front Load (Best fabric care & water saving)", badge="Recommended"),
                    QuestionOption(value="top_load_auto", label="Top Load Fully Automatic (Convenient & budget friendly)"),
                    QuestionOption(value="semi_auto", label="Semi-Automatic (Entry level, manual drain)")
                ],
                default_value="front_load",
                importance_weight=1.4,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="capacity",
                question="Family Size / Capacity?",
                type="single_choice",
                options=[
                    QuestionOption(value="6-7kg", label="6 to 7 kg (1 - 3 Persons)"),
                    QuestionOption(value="7-8kg", label="7 to 8 kg (3 - 5 Persons / Recommended)", badge="Popular"),
                    QuestionOption(value="8kg+", label="8.5 kg+ (Large Family 5+ Persons)")
                ],
                default_value="7-8kg",
                importance_weight=1.2,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="LG", label="LG Direct Drive"),
                    QuestionOption(value="Bosch", label="Bosch German Engineering"),
                    QuestionOption(value="Samsung", label="Samsung EcoBubble"),
                    QuestionOption(value="IFB", label="IFB Aqua Energie"),
                    QuestionOption(value="Whirlpool", label="Whirlpool")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "shoes":
            default_b = budget if budget else 4500.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                type="range_slider",
                min_value=800.0,
                max_value=18000.0,
                step=200.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="shoe_purpose",
                question="Primary Use & Activity?",
                type="single_choice",
                options=[
                    QuestionOption(value="running", label="Daily Running & Marathons", badge="Cushioning"),
                    QuestionOption(value="training_gym", label="Gym, HIIT & Weight Training", badge="Stability"),
                    QuestionOption(value="walking", label="All-Day Walking & Standing", badge="Comfort"),
                    QuestionOption(value="lifestyle_casual", label="Casual Daily Wear & Sneakers", badge="Style")
                ],
                default_value="running" if "running" in intent.raw_query.lower() else "walking",
                importance_weight=1.4,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Footwear Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Nike", label="Nike"),
                    QuestionOption(value="Adidas", label="Adidas"),
                    QuestionOption(value="Puma", label="Puma"),
                    QuestionOption(value="Asics", label="Asics (Top Gel Cushioning)"),
                    QuestionOption(value="New Balance", label="New Balance"),
                    QuestionOption(value="Skechers", label="Skechers (Memory Foam)")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        else:
            # General fallback questions tailored dynamically
            default_b = budget if budget else 15000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your target budget?",
                subtext="Maximum amount you wish to spend in INR",
                type="range_slider",
                min_value=500.0,
                max_value=100000.0,
                step=500.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="priority",
                question="What is most important to you?",
                subtext="This weights our TrustRank algorithm",
                type="single_choice",
                options=[
                    QuestionOption(value="value_for_money", label="Best Value for Money", description="Maximum features and build quality per Rupee"),
                    QuestionOption(value="highest_rated", label="Highest Customer Rating & Reliability", description="Proven long-term satisfaction and low complaint rate"),
                    QuestionOption(value="premium_features", label="Top-Tier Flagship Performance", description="Uncompromised premium specs and build")
                ],
                default_value="value_for_money",
                importance_weight=1.2,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brand_preference",
                question="Do you prefer top established brands or best-value emerging brands?",
                type="single_choice",
                options=[
                    QuestionOption(value="top_brands", label="Established Reputable Brands Only"),
                    QuestionOption(value="any_good_brand", label="Open to Any Brand with High Verified Ratings")
                ],
                default_value="any_good_brand",
                importance_weight=0.9,
                category=cat
            ))
            
        return questions
