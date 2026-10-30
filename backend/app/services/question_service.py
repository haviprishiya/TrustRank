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
        raw_query = intent.raw_query.lower()
        
        questions = []
        
        if cat == "laptop":
            # 1. Budget
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
            default_use = "gaming" if "gaming" in raw_query else ("programming" if "code" in raw_query or "programming" in raw_query else "all_round")
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
            
            # 3. Processor
            questions.append(RequirementQuestion(
                id="processor",
                question="Preferred Processor?",
                subtext="Choose your preferred CPU family",
                type="single_choice",
                options=[
                    QuestionOption(value="intel", label="Intel Core (i5 / i7 / i9 / Ultra)", badge="Intel", description="Industry standard, great single-core speed"),
                    QuestionOption(value="ryzen", label="AMD Ryzen (Ryzen 5 / 7 / 9)", badge="AMD", description="High multi-core efficiency and thermal balance"),
                    QuestionOption(value="apple_silicon", label="Apple Silicon (M2 / M3 / M4)", badge="Apple", description="Extreme efficiency and all-day battery"),
                    QuestionOption(value="any", label="Any Powerful Processor", badge="Flexible", description="Best available within budget")
                ],
                default_value="apple_silicon" if "macbook" in raw_query or "apple" in raw_query else ("ryzen" if "ryzen" in raw_query else ("intel" if "intel" in raw_query else "any")),
                importance_weight=1.3,
                category=cat
            ))
            
            # 3. RAM
            questions.append(RequirementQuestion(
                id="ram",
                question="RAM Capacity?",
                subtext="Higher RAM ensures seamless multitasking without slowdowns",
                type="single_choice",
                options=[
                    QuestionOption(value="8GB", label="8 GB", description="Good for everyday web, study and light office work"),
                    QuestionOption(value="16GB", label="16 GB (Recommended)", badge="Sweet Spot", description="Standard for smooth coding, gaming, and multitasking"),
                    QuestionOption(value="32GB", label="32 GB+", badge="Power User", description="Heavy virtualization, 4K rendering, and AI models")
                ],
                default_value="16GB",
                importance_weight=1.4,
                category=cat
            ))
            
            # 4. Storage
            questions.append(RequirementQuestion(
                id="storage",
                question="Preferred SSD Storage?",
                subtext="Fast NVMe SSD storage capacity",
                type="single_choice",
                options=[
                    QuestionOption(value="512GB", label="512 GB SSD", description="Standard capacity for most users"),
                    QuestionOption(value="1TB", label="1 TB SSD", badge="Popular", description="Ample room for large games, projects, and media"),
                    QuestionOption(value="2TB", label="2 TB SSD", description="Massive space for offline raw media and datasets")
                ],
                default_value="512GB",
                importance_weight=1.1,
                category=cat
            ))
            
            # 5. GPU
            questions.append(RequirementQuestion(
                id="gpu",
                question="Dedicated Graphics (GPU)?",
                subtext="Dedicated GPU for gaming, 3D rendering and machine learning",
                type="single_choice",
                options=[
                    QuestionOption(value="dedicated", label="Dedicated GPU (NVIDIA RTX / Radeon)", badge="High 3D", description="Required for AAA gaming, video editing, CAD, and 3D"),
                    QuestionOption(value="integrated", label="Integrated Graphics", badge="Long Battery", description="Sufficient for coding, office, and maximum battery life"),
                    QuestionOption(value="any", label="No Preference / Any", description="Balanced for general everyday use")
                ],
                default_value="dedicated" if ("gaming" in raw_query or "rtx" in raw_query) else "integrated",
                importance_weight=1.3,
                category=cat
            ))
            
            # 6. Display
            questions.append(RequirementQuestion(
                id="display",
                question="Display Size & Quality?",
                subtext="Screen dimension and panel preference",
                type="single_choice",
                options=[
                    QuestionOption(value="14_inch", label="14 inch (Thin, Light & Portable)", badge="Portable"),
                    QuestionOption(value="15_16_inch", label="15.6 - 16 inch (Standard Work & Media)", badge="Standard"),
                    QuestionOption(value="oled_high_res", label="OLED / 2K+ High Color Accuracy", badge="Vibrant"),
                    QuestionOption(value="any", label="Any Size", description="Flexible display size")
                ],
                default_value="14_inch" if "thin" in raw_query or "light" in raw_query else "15_16_inch",
                importance_weight=1.1,
                category=cat
            ))
            
            # 7. Battery
            questions.append(RequirementQuestion(
                id="battery",
                question="Battery Endurance Priority?",
                subtext="How many hours of cord-free operation you need",
                type="single_choice",
                options=[
                    QuestionOption(value="all_day", label="All-Day Battery (8-12+ hours)", badge="Max Endurance"),
                    QuestionOption(value="balanced", label="Balanced (5-7 hours)", badge="Standard"),
                    QuestionOption(value="performance_plugged", label="Performance First (Plugged in heavy work)", badge="Max Watts")
                ],
                default_value="all_day" if "battery" in raw_query else "balanced",
                importance_weight=1.2,
                category=cat
            ))
            
                        # 9. Priority
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
                default_value="performance" if "gaming" in raw_query else "portability",
                importance_weight=1.1,
                category=cat
            ))
            
            # 10. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Laptop Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Apple", label="Apple (MacBook)"),
                    QuestionOption(value="ASUS", label="ASUS / ROG / ZenBook"),
                    QuestionOption(value="Lenovo", label="Lenovo ThinkPad / IdeaPad / Legion"),
                    QuestionOption(value="HP", label="HP Pavilion / Victus / Omen"),
                    QuestionOption(value="Dell", label="Dell Inspiron / XPS / Alienware"),
                    QuestionOption(value="Acer", label="Acer Aspire / Nitro / Predator"),
                    QuestionOption(value="Samsung", label="Samsung Galaxy Book"),
                    QuestionOption(value="MSI", label="MSI")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "phone":
            # 1. Budget
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
            
            # 2. RAM
            questions.append(RequirementQuestion(
                id="ram",
                question="RAM Capacity?",
                subtext="Smooth app switching and lag-free background tasks",
                type="single_choice",
                options=[
                    QuestionOption(value="6GB", label="6 GB", description="Standard for casual everyday use"),
                    QuestionOption(value="8GB", label="8 GB (Recommended)", badge="Sweet Spot", description="Smooth multitasking and moderate gaming"),
                    QuestionOption(value="12GB", label="12 GB - 16 GB", badge="Pro Multitasking", description="Heavy gaming, zero background app reloading")
                ],
                default_value="8GB",
                importance_weight=1.3,
                category=cat
            ))
            
            # 3. Storage
            questions.append(RequirementQuestion(
                id="storage",
                question="Internal Storage?",
                subtext="Capacity for high-res photos, 4K videos, and apps",
                type="single_choice",
                options=[
                    QuestionOption(value="128GB", label="128 GB", description="Sufficient for light app usage"),
                    QuestionOption(value="256GB", label="256 GB (Recommended)", badge="Sweet Spot", description="Plenty of space for 4K video, games and photos"),
                    QuestionOption(value="512GB", label="512 GB+", badge="Heavy Storage", description="Massive space for offline videos and files")
                ],
                default_value="256GB",
                importance_weight=1.2,
                category=cat
            ))
            
            # 4. Camera
            questions.append(RequirementQuestion(
                id="camera",
                question="Camera Quality Priority?",
                subtext="Optical Image Stabilization (OIS), high megapixel, or night mode",
                type="single_choice",
                options=[
                    QuestionOption(value="flagship_ois", label="Flagship Camera with OIS", badge="Pro Photos", description="Sharp night shots, 4K 60fps video, portrait mode"),
                    QuestionOption(value="good_casual", label="Good Daytime & Social Media", badge="Social Media", description="Vibrant Instagram-ready snaps and crisp selfies"),
                    QuestionOption(value="basic", label="Standard Everyday Camera", description="Document scanning and basic casual snaps")
                ],
                default_value="flagship_ois" if ("camera" in raw_query or "photo" in raw_query) else "good_casual",
                importance_weight=1.4,
                category=cat
            ))
            
            # 5. Battery
            questions.append(RequirementQuestion(
                id="battery",
                question="Battery & Fast Charging?",
                subtext="Endurance for all-day heavy screen-on time",
                type="single_choice",
                options=[
                    QuestionOption(value="5000mah", label="5000mAh+ (Full Day Heavy Use)", badge="Standard Flagship"),
                    QuestionOption(value="6000mah", label="6000mAh+ (2-Day Endurance)", badge="Marathon"),
                    QuestionOption(value="fast_charging", label="Superfast Charging (67W - 120W)", badge="0-100% in 25m")
                ],
                default_value="6000mah" if "battery" in raw_query else "5000mah",
                importance_weight=1.2,
                category=cat
            ))
            
            # 6. Display
            questions.append(RequirementQuestion(
                id="display",
                question="Display & Refresh Rate?",
                subtext="Screen technology and smoothness",
                type="single_choice",
                options=[
                    QuestionOption(value="amoled_120hz", label="AMOLED / OLED 120Hz", badge="Ultra Smooth", description="Deep blacks, vibrant colors, buttery scrolling"),
                    QuestionOption(value="amoled_90hz", label="AMOLED 90Hz / 60Hz", description="Vibrant display with balanced power consumption"),
                    QuestionOption(value="any", label="Standard FHD+ Display", description="Reliable clear screen")
                ],
                default_value="amoled_120hz",
                importance_weight=1.1,
                category=cat
            ))
            
            # 7. 5G Connectivity
            questions.append(RequirementQuestion(
                id="connectivity_5g",
                question="5G Network Support?",
                subtext="Future-proof high speed mobile data",
                type="single_choice",
                options=[
                    QuestionOption(value="5g_required", label="5G Connectivity Required", badge="Future Proof"),
                    QuestionOption(value="4g_ok", label="4G LTE is Sufficient")
                ],
                default_value="5g_required",
                importance_weight=1.0,
                category=cat
            ))
            
                        # 9. Priority
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
                default_value="performance" if "gaming" in raw_query else "portability",
                importance_weight=1.1,
                category=cat
            ))
            
            # 10. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Smartphone Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Apple", label="Apple (iPhone)"),
                    QuestionOption(value="Samsung", label="Samsung Galaxy"),
                    QuestionOption(value="OnePlus", label="OnePlus"),
                    QuestionOption(value="Google", label="Google Pixel"),
                    QuestionOption(value="Xiaomi", label="Xiaomi / Redmi"),
                    QuestionOption(value="iQOO", label="iQOO"),
                    QuestionOption(value="Motorola", label="Motorola"),
                    QuestionOption(value="Realme", label="Realme"),
                    QuestionOption(value="Vivo", label="Vivo"),
                    QuestionOption(value="Nothing", label="Nothing Phone")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "dress":
            # 1. Budget
            default_b = budget if budget else 2500.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for the dress",
                type="range_slider",
                min_value=400.0,
                max_value=15000.0,
                step=100.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Size
            questions.append(RequirementQuestion(
                id="size",
                question="Preferred Size?",
                subtext="Standard clothing fit size",
                type="single_choice",
                options=[
                    QuestionOption(value="XS", label="XS (Extra Small)"),
                    QuestionOption(value="S", label="S (Small)"),
                    QuestionOption(value="M", label="M (Medium / Standard)"),
                    QuestionOption(value="L", label="L (Large)"),
                    QuestionOption(value="XL", label="XL (Extra Large)"),
                    QuestionOption(value="XXL", label="XXL (Double XL)"),
                    QuestionOption(value="Free Size", label="Free Size / Semi-Stitched")
                ],
                default_value="M",
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Color
            color_default = "Black" if "black" in raw_query else ("White" if "white" in raw_query else ("Red" if "red" in raw_query else ("Blue" if "blue" in raw_query else ("Pink" if "pink" in raw_query else "Any"))))
            questions.append(RequirementQuestion(
                id="color",
                question="Preferred Color?",
                subtext="Color palette of the dress",
                type="single_choice",
                options=[
                    QuestionOption(value="Black", label="Black"),
                    QuestionOption(value="White", label="White"),
                    QuestionOption(value="Blue", label="Blue / Navy"),
                    QuestionOption(value="Red", label="Red / Maroon"),
                    QuestionOption(value="Pink", label="Pink / Peach"),
                    QuestionOption(value="Green", label="Green / Olive"),
                    QuestionOption(value="Yellow", label="Yellow / Mustard"),
                    QuestionOption(value="Any", label="Any / Multi-color")
                ],
                default_value=color_default,
                importance_weight=1.2,
                category=cat
            ))
            
            # 4. Fabric
            fabric_default = "Cotton" if "cotton" in raw_query else ("Silk" if "silk" in raw_query else ("Georgette" if "georgette" in raw_query else "Cotton"))
            questions.append(RequirementQuestion(
                id="fabric",
                question="Preferred Fabric / Material?",
                subtext="Material breathability, texture, and care",
                type="single_choice",
                options=[
                    QuestionOption(value="Cotton", label="100% Pure Cotton", badge="Breathable", description="Soft, lightweight, best for daily & summer wear"),
                    QuestionOption(value="Silk", label="Silk / Art Silk", badge="Festive", description="Rich sheen, elegant drape for occasions"),
                    QuestionOption(value="Georgette", label="Georgette", badge="Flowy", description="Lightweight crinkle texture with graceful flare"),
                    QuestionOption(value="Rayon", label="Rayon / Viscose", description="Smooth silky texture, comfortable drape"),
                    QuestionOption(value="Chiffon", label="Chiffon", description="Sheer, ethereal, elegant party wear"),
                    QuestionOption(value="Linen", label="Linen", badge="Premium Natural", description="Breathable organic luxury texture"),
                    QuestionOption(value="Any", label="Any Fabric")
                ],
                default_value=fabric_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 5. Fit
            fit_default = "Maxi" if "maxi" in raw_query else ("A-Line" if "a-line" in raw_query or "a line" in raw_query else ("Bodycon" if "bodycon" in raw_query else "A-Line"))
            questions.append(RequirementQuestion(
                id="fit",
                question="Dress Silhouette & Fit?",
                subtext="Cut and shape of the silhouette",
                type="single_choice",
                options=[
                    QuestionOption(value="A-Line", label="A-Line", badge="Flattering", description="Fitted bodice flared from waist, universally flattering"),
                    QuestionOption(value="Maxi", label="Maxi / Flowy Floor-Length", badge="Graceful", description="Long flowing dress, casual elegance"),
                    QuestionOption(value="Bodycon", label="Bodycon / Form Fitting", badge="Party", description="Figure-hugging tight silhouette"),
                    QuestionOption(value="Fit and Flare", label="Fit & Flare", description="Fitted waist with voluminous skirt"),
                    QuestionOption(value="Shift", label="Shift / Straight", description="Straight cut hanging loosely from shoulders"),
                    QuestionOption(value="Relaxed", label="Relaxed / Oversized", description="Casual comfortable loose drape")
                ],
                default_value=fit_default,
                importance_weight=1.3,
                category=cat
            ))
            
            # 6. Pattern
            questions.append(RequirementQuestion(
                id="pattern",
                question="Pattern & Print?",
                subtext="Visual styling and motifs",
                type="single_choice",
                options=[
                    QuestionOption(value="Solid", label="Solid / Plain", description="Clean monochrome aesthetic"),
                    QuestionOption(value="Floral", label="Floral Print", description="Delicate botanical & flower designs"),
                    QuestionOption(value="Printed", label="Geometric / Abstract Print", description="Modern art and dynamic prints"),
                    QuestionOption(value="Striped", label="Striped / Checked", description="Timeless linear motifs"),
                    QuestionOption(value="Embroidered", label="Embroidered / Zari Work", description="Detailed craftwork for festive wear")
                ],
                default_value="Floral" if "floral" in raw_query else "Solid",
                importance_weight=1.1,
                category=cat
            ))
            
            # 7. Occasion
            occ_default = "Party" if "party" in raw_query else ("Festive" if "festive" in raw_query or "wedding" in raw_query else ("Formal" if "formal" in raw_query or "work" in raw_query else "Casual"))
            questions.append(RequirementQuestion(
                id="occasion",
                question="Occasion / Intended Wear?",
                subtext="Where do you plan to wear this dress?",
                type="single_choice",
                options=[
                    QuestionOption(value="Casual", label="Casual & Daily Wear", badge="Everyday", description="Outings, college, cafe visits, vacations"),
                    QuestionOption(value="Party", label="Party, Dinner & Evening", badge="Glamour", description="Cocktail parties, birthdays, night events"),
                    QuestionOption(value="Festive", label="Festive, Wedding & Traditional", badge="Celebration", description="Ceremonies, festivals, ethnic gatherings"),
                    QuestionOption(value="Formal", label="Formal & Office Work", badge="Smart", description="Professional workplace, meetings, seminars")
                ],
                default_value=occ_default,
                importance_weight=1.3,
                category=cat
            ))

        elif cat == "shoes":
            # 1. Budget
            default_b = budget if budget else 3500.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for footwear",
                type="range_slider",
                min_value=600.0,
                max_value=20000.0,
                step=200.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Size
            questions.append(RequirementQuestion(
                id="size",
                question="Shoe Size (UK / India)?",
                subtext="Standard Indian/UK footwear sizing",
                type="single_choice",
                options=[
                    QuestionOption(value="UK 6", label="UK 6 (EU 39)"),
                    QuestionOption(value="UK 7", label="UK 7 (EU 40.5)"),
                    QuestionOption(value="UK 8", label="UK 8 (EU 42)"),
                    QuestionOption(value="UK 9", label="UK 9 (EU 43)"),
                    QuestionOption(value="UK 10", label="UK 10 (EU 44.5)"),
                    QuestionOption(value="UK 11", label="UK 11 (EU 45)"),
                    QuestionOption(value="Any", label="Any Size")
                ],
                default_value="UK 8",
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Type
            type_default = "Running" if "running" in raw_query else ("Sneakers" if "sneaker" in raw_query else ("Formal" if "formal" in raw_query else "Running"))
            questions.append(RequirementQuestion(
                id="type",
                question="Shoe Type & Style?",
                subtext="Footwear category",
                type="single_choice",
                options=[
                    QuestionOption(value="Running", label="Running & Sports Shoes", badge="Performance", description="High shock absorption, road grip, lightweight"),
                    QuestionOption(value="Sneakers", label="Casual Sneakers", badge="Streetwear", description="Stylish everyday footwear, versatile pairing"),
                    QuestionOption(value="Formal", label="Formal Oxfords / Derbys", badge="Office", description="Polished formal leather footwear"),
                    QuestionOption(value="Loafers", label="Loafers & Slip-Ons", description="Easy slip-on comfort, smart casual"),
                    QuestionOption(value="Boots", label="Boots & High Tops", description="Rugged ankle support and durability"),
                    QuestionOption(value="Sandals", label="Sandals & Slides", description="Open-toe breathable leisure footwear")
                ],
                default_value=type_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 4. Material
            questions.append(RequirementQuestion(
                id="material",
                question="Upper Material?",
                subtext="Breathability, flexibility, and exterior finish",
                type="single_choice",
                options=[
                    QuestionOption(value="Mesh", label="Breathable Engineered Mesh", badge="Cooling", description="Maximum airflow, sweat ventilation"),
                    QuestionOption(value="Leather", label="Genuine / Synthetic Leather", badge="Classic", description="Premium structured finish, water resistant"),
                    QuestionOption(value="Canvas", label="Canvas Fabric", description="Lightweight flexible casual textile"),
                    QuestionOption(value="Knit", label="Flyknit / Woven Textile", description="Sock-like adaptive contoured fit"),
                    QuestionOption(value="Any", label="Any Material")
                ],
                default_value="Mesh" if type_default == "Running" else "Leather",
                importance_weight=1.2,
                category=cat
            ))
            
            # 5. Color
            color_default = "Black" if "black" in raw_query else ("White" if "white" in raw_query else "Black")
            questions.append(RequirementQuestion(
                id="color",
                question="Preferred Color?",
                subtext="Primary colorway",
                type="single_choice",
                options=[
                    QuestionOption(value="Black", label="Black"),
                    QuestionOption(value="White", label="White"),
                    QuestionOption(value="Blue", label="Blue / Navy"),
                    QuestionOption(value="Grey", label="Grey / Silver"),
                    QuestionOption(value="Brown", label="Brown / Tan"),
                    QuestionOption(value="Any", label="Any / Multicolor")
                ],
                default_value=color_default,
                importance_weight=1.1,
                category=cat
            ))
            
            # 6. Sole Cushioning
            questions.append(RequirementQuestion(
                id="sole",
                question="Sole & Cushioning Technology?",
                subtext="Midsole comfort and outsole traction",
                type="single_choice",
                options=[
                    QuestionOption(value="Rubber", label="Durable Rubber Outsole (Non-Slip)", badge="High Grip"),
                    QuestionOption(value="EVA", label="EVA Lightweight Foam Midsole", badge="Featherlight"),
                    QuestionOption(value="Memory Foam", label="Memory Foam / Air Gel Cushioning", badge="Plush Comfort"),
                    QuestionOption(value="Leather", label="Formal Hard Leather Sole")
                ],
                default_value="Rubber",
                importance_weight=1.2,
                category=cat
            ))
            
            # 7. Usage
            questions.append(RequirementQuestion(
                id="usage",
                question="Primary Usage?",
                subtext="Activity level and terrain",
                type="single_choice",
                options=[
                    QuestionOption(value="Running", label="Daily Running & Marathons", badge="Active"),
                    QuestionOption(value="Walking", label="All-Day Walking & Standing", badge="Comfort"),
                    QuestionOption(value="Casual", label="Casual Everyday & Outings", badge="Lifestyle"),
                    QuestionOption(value="Gym", label="Gym, Weights & Cross-Training", badge="Stability"),
                    QuestionOption(value="Work", label="Workplace & Formal Gatherings")
                ],
                default_value="Running" if "running" in raw_query else "Walking",
                importance_weight=1.3,
                category=cat
            ))
            
                        # 9. Priority
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
                default_value="performance" if "gaming" in raw_query else "portability",
                importance_weight=1.1,
                category=cat
            ))
            
            # 10. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Footwear Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Nike", label="Nike"),
                    QuestionOption(value="Adidas", label="Adidas"),
                    QuestionOption(value="Puma", label="Puma"),
                    QuestionOption(value="Asics", label="Asics (Gel Cushioning)"),
                    QuestionOption(value="New Balance", label="New Balance"),
                    QuestionOption(value="Skechers", label="Skechers (Memory Foam)"),
                    QuestionOption(value="Reebok", label="Reebok"),
                    QuestionOption(value="Woodland", label="Woodland")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "tv":
            # 1. Budget
            default_b = budget if budget else 45000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for Smart TV",
                type="range_slider",
                min_value=10000.0,
                max_value=250000.0,
                step=2000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Screen Size
            size_default = "55 inch" if "55" in raw_query else ("65 inch+" if "65" in raw_query else ("43 inch" if "43" in raw_query else ("32 inch" if "32" in raw_query else "55 inch")))
            questions.append(RequirementQuestion(
                id="screen_size",
                question="Desired Screen Size?",
                subtext="Select based on room viewing distance",
                type="single_choice",
                options=[
                    QuestionOption(value="32 inch", label="32 inch (Bedroom / Compact space)"),
                    QuestionOption(value="43 inch", label="43 inch (Medium room 6-8 ft distance)"),
                    QuestionOption(value="50 inch", label="50 inch (Living room 8-10 ft distance)"),
                    QuestionOption(value="55 inch", label="55 inch (Most Popular Living Room Size)", badge="Sweet Spot"),
                    QuestionOption(value="65 inch+", label="65 inch+ (Cinema Hall Experience 10ft+)", badge="Cinema")
                ],
                default_value=size_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Resolution
            questions.append(RequirementQuestion(
                id="resolution",
                question="Screen Resolution?",
                subtext="Display clarity and pixel density",
                type="single_choice",
                options=[
                    QuestionOption(value="4K", label="4K Ultra HD (3840 x 2160)", badge="Standard UHD", description="Crisp details for Netflix, Prime, 4K HDR"),
                    QuestionOption(value="FHD", label="Full HD 1080p", description="Great budget clarity for smaller screens"),
                    QuestionOption(value="8K", label="8K Ultra HD", badge="Ultra High End", description="Next-generation maximum pixel density")
                ],
                default_value="4K",
                importance_weight=1.3,
                category=cat
            ))
            
            # 4. Display Type
            questions.append(RequirementQuestion(
                id="display_type",
                question="Display Panel Technology?",
                subtext="Backlight and contrast panel technology",
                type="single_choice",
                options=[
                    QuestionOption(value="OLED", label="OLED (Self-lit pixels, infinite contrast, pure black)", badge="Best Picture"),
                    QuestionOption(value="QLED", label="QLED / Mini-LED (Quantum dot, high brightness)", badge="Bright Rooms"),
                    QuestionOption(value="LED", label="4K LED / LCD (High value, reliable performance)", badge="Value")
                ],
                default_value="OLED" if "oled" in raw_query else ("QLED" if "qled" in raw_query else "QLED"),
                importance_weight=1.3,
                category=cat
            ))
            
            # 5. Refresh Rate
            questions.append(RequirementQuestion(
                id="refresh_rate",
                question="Refresh Rate?",
                subtext="Motion smoothness for sports and console gaming",
                type="single_choice",
                options=[
                    QuestionOption(value="120Hz", label="120Hz / 144Hz (PS5, Xbox, High FPS Gaming)", badge="Gaming Ready"),
                    QuestionOption(value="60Hz", label="60Hz (Standard Movies, OTT & TV Broadcasts)", badge="Standard")
                ],
                default_value="120Hz" if "120" in raw_query or "gaming" in raw_query else "60Hz",
                importance_weight=1.1,
                category=cat
            ))
            
            # 6. Smart Features
            questions.append(RequirementQuestion(
                id="smart_features",
                question="Smart OS & Audio Features?",
                subtext="Operating system and audiovisual formats",
                type="single_choice",
                options=[
                    QuestionOption(value="Google TV", label="Google TV / Android TV (Play Store apps)", badge="Most Apps"),
                    QuestionOption(value="Dolby Vision", label="Dolby Vision & Dolby Atmos Audio", badge="Cinematic"),
                    QuestionOption(value="WebOS", label="LG webOS / Samsung Tizen", badge="Smooth UI"),
                    QuestionOption(value="Standard", label="Standard Smart TV with YouTube & Netflix")
                ],
                default_value="Google TV",
                importance_weight=1.1,
                category=cat
            ))
            
            # 7. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred TV Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Sony", label="Sony Bravia (Top processing & audio)"),
                    QuestionOption(value="Samsung", label="Samsung Neo QLED / Crystal 4K"),
                    QuestionOption(value="LG", label="LG OLED / QNED"),
                    QuestionOption(value="TCL", label="TCL Mini-LED"),
                    QuestionOption(value="Xiaomi", label="Xiaomi / Mi TV"),
                    QuestionOption(value="OnePlus", label="OnePlus TV")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "refrigerator":
            # 1. Budget
            default_b = budget if budget else 32000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for refrigerator",
                type="range_slider",
                min_value=12000.0,
                max_value=150000.0,
                step=1000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Capacity
            cap_default = "200L - 299L"
            if "300" in raw_query or "350" in raw_query:
                cap_default = "300L - 450L"
            elif "190" in raw_query or "single door" in raw_query:
                cap_default = "Under 200L"
            questions.append(RequirementQuestion(
                id="capacity",
                question="Capacity (Litres)?",
                subtext="Choose based on your family size",
                type="single_choice",
                options=[
                    QuestionOption(value="Under 200L", label="Under 200 Litres (1 - 2 Persons / Bachelors)"),
                    QuestionOption(value="200L - 299L", label="200L to 299L (3 - 4 Persons / Small Family)", badge="Most Popular"),
                    QuestionOption(value="300L - 450L", label="300L to 450L (4 - 5 Persons / Medium Family)", badge="Spacious"),
                    QuestionOption(value="450L+", label="450 Litres+ (Large Family / Heavy Storage)", badge="Massive")
                ],
                default_value=cap_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Door Type
            door_default = "Double Door"
            if "side by side" in raw_query:
                door_default = "Side by Side"
            elif "single door" in raw_query:
                door_default = "Single Door"
            questions.append(RequirementQuestion(
                id="door_type",
                question="Door Configuration?",
                subtext="Body style and layout",
                type="single_choice",
                options=[
                    QuestionOption(value="Double Door", label="Double Door (Frost Free, Separate Freezer)", badge="Recommended"),
                    QuestionOption(value="Single Door", label="Single Door (Compact, Direct Cool, Economical)"),
                    QuestionOption(value="Side by Side", label="Side by Side (American Style, Premium)", badge="Luxury"),
                    QuestionOption(value="Multi Door", label="French Door / Multi-Door (Flexible cooling zones)"),
                    QuestionOption(value="Triple Door", label="Triple Door (Dedicated vegetable drawer)")
                ],
                default_value=door_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 4. Energy Rating
            questions.append(RequirementQuestion(
                id="energy_rating",
                question="Energy Star Rating?",
                subtext="BEE electricity efficiency rating",
                type="single_choice",
                options=[
                    QuestionOption(value="5 Star", label="5 Star (Maximum Electricity Savings)", badge="Eco Saver"),
                    QuestionOption(value="4 Star", label="4 Star (High Energy Efficiency)"),
                    QuestionOption(value="3 Star", label="3 Star (Standard Balance)", badge="Popular"),
                    QuestionOption(value="Any", label="Any Energy Rating")
                ],
                default_value="3 Star",
                importance_weight=1.3,
                category=cat
            ))
            
            # 5. Inverter Compressor
            questions.append(RequirementQuestion(
                id="inverter",
                question="Inverter Technology?",
                subtext="Variable speed compressor for durability and silent cooling",
                type="single_choice",
                options=[
                    QuestionOption(value="Inverter", label="Digital Inverter Compressor (Quiet & 10-20yr warranty)", badge="Recommended"),
                    QuestionOption(value="Standard", label="Standard Reciprocating Compressor"),
                    QuestionOption(value="Any", label="Any Compressor Type")
                ],
                default_value="Inverter",
                importance_weight=1.2,
                category=cat
            ))
            
            # 6. Frost Free
            questions.append(RequirementQuestion(
                id="frost_free",
                question="Defrosting System?",
                subtext="Ice buildup prevention",
                type="single_choice",
                options=[
                    QuestionOption(value="Frost Free", label="Frost Free (Auto Defrost, No Ice Buildup)", badge="Convenient"),
                    QuestionOption(value="Direct Cool", label="Direct Cool (Manual Defrosting Button, Economical)")
                ],
                default_value="Frost Free",
                importance_weight=1.3,
                category=cat
            ))
            
            # 7. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Refrigerator Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="LG", label="LG Smart Inverter"),
                    QuestionOption(value="Samsung", label="Samsung Digital Inverter"),
                    QuestionOption(value="Whirlpool", label="Whirlpool Intellifresh"),
                    QuestionOption(value="Haier", label="Haier Bottom Mounted"),
                    QuestionOption(value="Godrej", label="Godrej Eon"),
                    QuestionOption(value="Bosch", label="Bosch German Build")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "headphones":
            # 1. Budget
            default_b = budget if budget else 6000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for audio gear",
                type="range_slider",
                min_value=800.0,
                max_value=40000.0,
                step=500.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Type
            type_default = "Over-Ear" if "over ear" in raw_query or "headphone" in raw_query else "TWS"
            questions.append(RequirementQuestion(
                id="type",
                question="Audio Form Factor / Type?",
                subtext="Choose how you prefer to wear them",
                type="single_choice",
                options=[
                    QuestionOption(value="TWS", label="True Wireless Earbuds (TWS)", badge="Pocketable", description="Compact charging case, in-ear comfort"),
                    QuestionOption(value="Over-Ear", label="Over-Ear Headphones", badge="Max ANC & Bass", description="Plush earcups, deep immersive soundstage"),
                    QuestionOption(value="Neckband", label="Wireless Neckband", badge="Workout", description="Magnetic earbuds, stays secure around neck"),
                    QuestionOption(value="Wired", label="Audiophile Wired IEMs", badge="Hi-Res Lossless", description="Zero latency, studio monitoring DAC fidelity")
                ],
                default_value=type_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. ANC
            anc_default = "ANC Required" if "anc" in raw_query or "noise cancelling" in raw_query else "ANC Required"
            questions.append(RequirementQuestion(
                id="anc",
                question="Active Noise Cancellation (ANC)?",
                subtext="Blocks out ambient engine rumble, traffic and chatter",
                type="single_choice",
                options=[
                    QuestionOption(value="ANC Required", label="Active Noise Cancellation (ANC)", badge="Quiet Commute", description="Silence outside noise for travel and study"),
                    QuestionOption(value="Passive Isolation", label="Passive Noise Isolation", description="Tight ear seal is sufficient, saves battery")
                ],
                default_value=anc_default,
                importance_weight=1.3,
                category=cat
            ))
            
            # 4. Battery Life
            questions.append(RequirementQuestion(
                id="battery_life",
                question="Battery Endurance?",
                subtext="Playback hours with charging case or single charge",
                type="single_choice",
                options=[
                    QuestionOption(value="30h+", label="30+ Hours Total Playtime", badge="Heavy User"),
                    QuestionOption(value="20-30h", label="20 to 30 Hours Playtime", badge="Standard"),
                    QuestionOption(value="Any", label="Any Battery Life")
                ],
                default_value="30h+",
                importance_weight=1.2,
                category=cat
            ))
            
            # 5. Bluetooth
            questions.append(RequirementQuestion(
                id="bluetooth",
                question="Bluetooth & Multipoint Pairing?",
                subtext="Dual-device connection and codec support",
                type="single_choice",
                options=[
                    QuestionOption(value="Multipoint", label="Multipoint Dual Pairing (Laptop + Phone)", badge="Productivity"),
                    QuestionOption(value="Latest Codecs", label="Hi-Res LDAC / aptX Support", badge="Audiophile"),
                    QuestionOption(value="Standard", label="Standard Bluetooth 5.0+")
                ],
                default_value="Multipoint",
                importance_weight=1.1,
                category=cat
            ))
            
            # 6. Microphone
            questions.append(RequirementQuestion(
                id="microphone",
                question="Microphone Call Quality?",
                subtext="Voice clarity for Zoom meetings and phone calls",
                type="single_choice",
                options=[
                    QuestionOption(value="AI Mic", label="AI ENC Noise-Cancelling Mic (Clear Calls)", badge="Work & Calls"),
                    QuestionOption(value="Standard Mic", label="Standard Built-in Mic")
                ],
                default_value="AI Mic",
                importance_weight=1.2,
                category=cat
            ))
            
            # 7. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Audio Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Sony", label="Sony (Top ANC & Sound)"),
                    QuestionOption(value="Bose", label="Bose (Maximum Comfort)"),
                    QuestionOption(value="Sennheiser", label="Sennheiser (Acoustic Fidelity)"),
                    QuestionOption(value="JBL", label="JBL (Deep Bass)"),
                    QuestionOption(value="OnePlus", label="OnePlus Bullets / Buds"),
                    QuestionOption(value="Realme", label="Realme Buds"),
                    QuestionOption(value="boAt", label="boAt (Budget Bass)"),
                    QuestionOption(value="Apple", label="Apple AirPods")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "camera":
            # 1. Budget
            default_b = budget if budget else 65000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Budget in INR for camera body or kit combo",
                type="range_slider",
                min_value=20000.0,
                max_value=300000.0,
                step=5000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Sensor
            sensor_default = "Full Frame" if "full frame" in raw_query else "APS-C"
            questions.append(RequirementQuestion(
                id="sensor",
                question="Sensor Format?",
                subtext="Determines dynamic range and low-light gathering",
                type="single_choice",
                options=[
                    QuestionOption(value="Full Frame", label="Full Frame (35mm)", badge="Pro Dynamic Range", description="Superior low light, shallow depth of field"),
                    QuestionOption(value="APS-C", label="APS-C Cropped Sensor", badge="Sweet Spot", description="Compact bodies, affordable lenses, sharp detail"),
                    QuestionOption(value="Micro Four Thirds", label="Micro Four Thirds / 1-inch", description="Ultra compact, extreme telephoto reach")
                ],
                default_value=sensor_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Megapixel
            questions.append(RequirementQuestion(
                id="megapixel",
                question="Megapixel Count?",
                subtext="Image resolution for cropping and printing",
                type="single_choice",
                options=[
                    QuestionOption(value="24MP - 33MP", label="24MP to 33MP (Standard Balance)", badge="Versatile"),
                    QuestionOption(value="40MP+", label="40MP+ Ultra High Resolution (Studio & Landscape)", badge="Fine Detail"),
                    QuestionOption(value="12MP - 20MP", label="12MP to 20MP (Optimized for 4K Video & Low Light)")
                ],
                default_value="24MP - 33MP",
                importance_weight=1.2,
                category=cat
            ))
            
            # 4. Lens
            questions.append(RequirementQuestion(
                id="lens",
                question="Lens Configuration?",
                subtext="Kit lens or interchangeable mount",
                type="single_choice",
                options=[
                    QuestionOption(value="Kit Lens", label="Camera Body + Kit Zoom Lens (Ready to shoot)", badge="Starter Combo"),
                    QuestionOption(value="Body Only", label="Body Only (Interchangeable lens enthusiast)"),
                    QuestionOption(value="Fixed Lens", label="Fixed Lens / Action Vlogging Camera")
                ],
                default_value="Kit Lens",
                importance_weight=1.3,
                category=cat
            ))
            
            # 5. Video Resolution
            questions.append(RequirementQuestion(
                id="video_resolution",
                question="Video Recording Capabilities?",
                subtext="Cinematography and vlogging frame rates",
                type="single_choice",
                options=[
                    QuestionOption(value="4K 60fps", label="4K at 60fps / 120fps (Slow motion cinema)", badge="Pro Video"),
                    QuestionOption(value="4K 30fps", label="4K at 24/30fps (Standard Cinematic)", badge="Standard 4K"),
                    QuestionOption(value="1080p", label="Full HD 1080p (Basic casual video)")
                ],
                default_value="4K 60fps" if "video" in raw_query or "vlog" in raw_query else "4K 30fps",
                importance_weight=1.3,
                category=cat
            ))
            
            # 6. Stabilization
            questions.append(RequirementQuestion(
                id="stabilization",
                question="Image Stabilization?",
                subtext="Camera shake reduction for handheld shooting",
                type="single_choice",
                options=[
                    QuestionOption(value="IBIS", label="In-Body 5-Axis Image Stabilization (IBIS)", badge="Handheld Steady"),
                    QuestionOption(value="Optical", label="Lens Optical Image Stabilization (OIS)"),
                    QuestionOption(value="Electronic", label="Electronic / Gyro Stabilization")
                ],
                default_value="IBIS",
                importance_weight=1.2,
                category=cat
            ))
            
            # 7. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Camera Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Sony", label="Sony Alpha"),
                    QuestionOption(value="Canon", label="Canon EOS"),
                    QuestionOption(value="Nikon", label="Nikon Z"),
                    QuestionOption(value="Fujifilm", label="Fujifilm X"),
                    QuestionOption(value="GoPro", label="GoPro Action"),
                    QuestionOption(value="DJI", label="DJI Osmo")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "smartwatch":
            # 1. Budget
            default_b = budget if budget else 5000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for smartwatch",
                type="range_slider",
                min_value=1500.0,
                max_value=60000.0,
                step=500.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Display
            questions.append(RequirementQuestion(
                id="display",
                question="Display Panel?",
                subtext="Screen brightness and always-on capability",
                type="single_choice",
                options=[
                    QuestionOption(value="AMOLED", label="AMOLED with Always-On Display (AOD)", badge="Vibrant", description="Deep blacks, bright outdoor sunlight visibility"),
                    QuestionOption(value="TFT LCD", label="HD TFT / LCD Display", description="Reliable clear display at budget friendly price"),
                    QuestionOption(value="Any", label="Any Display Type")
                ],
                default_value="AMOLED",
                importance_weight=1.3,
                category=cat
            ))
            
            # 3. Battery
            questions.append(RequirementQuestion(
                id="battery",
                question="Battery Endurance?",
                subtext="Days between charges",
                type="single_choice",
                options=[
                    QuestionOption(value="7+ Days", label="7 to 14 Days (Extended Battery)", badge="Long Life"),
                    QuestionOption(value="2-4 Days", label="2 to 4 Days (Balanced Usage)"),
                    QuestionOption(value="1-2 Days", label="1 to 2 Days (Full WearOS / Apple Watch OS with Apps)")
                ],
                default_value="7+ Days",
                importance_weight=1.3,
                category=cat
            ))
            
            # 4. GPS
            gps_default = "Built-in GPS" if "gps" in raw_query or "running" in raw_query else "Connected GPS"
            questions.append(RequirementQuestion(
                id="gps",
                question="GPS Navigation & Tracking?",
                subtext="Outdoor workout map recording",
                type="single_choice",
                options=[
                    QuestionOption(value="Built-in GPS", label="Built-in Standalone GPS (Leave phone at home)", badge="Runner's Choice"),
                    QuestionOption(value="Connected GPS", label="Connected GPS (Uses smartphone GPS)"),
                    QuestionOption(value="Not Needed", label="GPS Not Required")
                ],
                default_value=gps_default,
                importance_weight=1.2,
                category=cat
            ))
            
            # 5. Calling
            calling_default = "BT Calling" if "calling" in raw_query or "call" in raw_query else "BT Calling"
            questions.append(RequirementQuestion(
                id="calling",
                question="Bluetooth Calling?",
                subtext="Dial and answer calls directly on watch",
                type="single_choice",
                options=[
                    QuestionOption(value="BT Calling", label="Bluetooth Calling with Mic & Speaker", badge="Hands-Free"),
                    QuestionOption(value="Notifications", label="Smart Notifications Only (Vibration alerts)")
                ],
                default_value=calling_default,
                importance_weight=1.3,
                category=cat
            ))
            
            # 6. Health Features
            questions.append(RequirementQuestion(
                id="health_features",
                question="Health & Fitness Tracking?",
                subtext="Sensors for wellness monitoring",
                type="single_choice",
                options=[
                    QuestionOption(value="Standard Health", label="Heart Rate + SpO2 + Sleep + Step Tracking", badge="Essential"),
                    QuestionOption(value="Advanced Health", label="Advanced (ECG, Stress, Body Temp, Menstrual)", badge="Medical Grade"),
                    QuestionOption(value="Basic Tracker", label="Basic Pedometer & Calorie Counter")
                ],
                default_value="Standard Health",
                importance_weight=1.3,
                category=cat
            ))
            
            # 7. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Smartwatch Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Apple", label="Apple Watch"),
                    QuestionOption(value="Samsung", label="Samsung Galaxy Watch"),
                    QuestionOption(value="Amazfit", label="Amazfit"),
                    QuestionOption(value="Garmin", label="Garmin (Pro Sports)"),
                    QuestionOption(value="Noise", label="Noise"),
                    QuestionOption(value="Fire-Boltt", label="Fire-Boltt"),
                    QuestionOption(value="boAt", label="boAt"),
                    QuestionOption(value="OnePlus", label="OnePlus Watch")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "furniture":
            # 1. Budget
            default_b = budget if budget else 12000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for furniture",
                type="range_slider",
                min_value=1500.0,
                max_value=100000.0,
                step=500.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
                        # 2. Furniture / Chair Use
            chair_use_default = "office" if ("office" in raw_query or "chair" in raw_query) else "general"
            questions.append(RequirementQuestion(
                id="furniture_use",
                question="How will you primarily use the chair or furniture?",
                subtext="Helps match ergonomic support and material durability",
                type="single_choice",
                options=[
                    QuestionOption(value="office", label="Office Work & Long Sitting (Lumbar Support)", badge="Ergonomic"),
                    QuestionOption(value="study", label="Student Study & Desk Work"),
                    QuestionOption(value="living", label="Living Room / Lounge Seating"),
                    QuestionOption(value="general", label="General Home Use")
                ],
                default_value=chair_use_default,
                importance_weight=1.3,
                category=cat
            ))
            
            # 3. Size
            questions.append(RequirementQuestion(
                id="size",
                question="Room Size & Dimensions?",
                subtext="Space profile in your living or office space",
                type="single_choice",
                options=[
                    QuestionOption(value="Compact", label="Compact / Small Space Friendly", badge="Space Saver"),
                    QuestionOption(value="Medium", label="Medium / Standard Dimensions", badge="Standard"),
                    QuestionOption(value="Large", label="Large / Spacious Family Size", badge="Spacious"),
                    QuestionOption(value="Adjustable", label="Ergonomic & Adjustable Height", badge="Ergonomic")
                ],
                default_value="Adjustable" if "chair" in raw_query or "desk" in raw_query else "Medium",
                importance_weight=1.3,
                category=cat
            ))
            
            # 3. Material
            mat_default = "Solid Wood" if "wood" in raw_query or "sheesham" in raw_query else ("Mesh" if "chair" in raw_query else "Solid Wood")
            questions.append(RequirementQuestion(
                id="material",
                question="Primary Material?",
                subtext="Frame and upholstery composition",
                type="single_choice",
                options=[
                    QuestionOption(value="Solid Wood", label="Solid Wood (Sheesham / Teak / Oak)", badge="Durable Classic"),
                    QuestionOption(value="Engineered Wood", label="Engineered Wood (MDF / Particle Board)", badge="Modern Value"),
                    QuestionOption(value="Metal", label="Metal / Steel Frame", badge="Heavy Duty"),
                    QuestionOption(value="Leatherette", label="Leatherette / Fabric Upholstery", badge="Comfort"),
                    QuestionOption(value="Mesh", label="Breathable Mesh (Ergonomic Chairs)", badge="Breathable")
                ],
                default_value=mat_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 4. Color
            questions.append(RequirementQuestion(
                id="color",
                question="Color / Finish?",
                subtext="Finish matching your room interior",
                type="single_choice",
                options=[
                    QuestionOption(value="Brown", label="Brown / Natural Wooden Polish"),
                    QuestionOption(value="Black", label="Black / Matte Black"),
                    QuestionOption(value="Grey", label="Grey / Slate"),
                    QuestionOption(value="White", label="White / Ivory Light Finish"),
                    QuestionOption(value="Any", label="Any Color / Finish")
                ],
                default_value="Black" if "chair" in raw_query else "Brown",
                importance_weight=1.1,
                category=cat
            ))
            
            # 5. Style
            questions.append(RequirementQuestion(
                id="style",
                question="Design Style?",
                subtext="Aesthetic concept",
                type="single_choice",
                options=[
                    QuestionOption(value="Modern", label="Modern / Contemporary", badge="Sleek"),
                    QuestionOption(value="Ergonomic", label="Ergonomic & Functional (Lumbar Support)", badge="Back Health"),
                    QuestionOption(value="Traditional", label="Traditional & Royal Indian Classic"),
                    QuestionOption(value="Minimalist", label="Minimalist Nordic / Scandinavian")
                ],
                default_value="Ergonomic" if "chair" in raw_query else "Modern",
                importance_weight=1.2,
                category=cat
            ))
            
            # 6. Storage
            questions.append(RequirementQuestion(
                id="storage",
                question="Storage Compartments?",
                subtext="Built-in drawers or box storage",
                type="single_choice",
                options=[
                    QuestionOption(value="With Storage", label="With Storage / Drawers / Hydraulic Lift", badge="Storage"),
                    QuestionOption(value="Without Storage", label="Clean Open Design / Without Storage"),
                    QuestionOption(value="Not Applicable", label="Not Applicable")
                ],
                default_value="With Storage" if "desk" in raw_query or "bed" in raw_query or "table" in raw_query else "Not Applicable",
                importance_weight=1.2,
                category=cat
            ))

        elif cat == "kitchen_appliances":
            # 1. Budget
            default_b = budget if budget else 6000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for kitchen appliance",
                type="range_slider",
                min_value=1000.0,
                max_value=50000.0,
                step=500.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Type
            type_default = "Air Fryer" if "fryer" in raw_query else ("Mixer Grinder" if "mixer" in raw_query or "grinder" in raw_query else ("Microwave" if "microwave" in raw_query or "otg" in raw_query else ("Coffee Maker" if "coffee" in raw_query else "Air Fryer")))
            questions.append(RequirementQuestion(
                id="type",
                question="Appliance Type?",
                subtext="Specific kitchen device",
                type="single_choice",
                options=[
                    QuestionOption(value="Air Fryer", label="Digital Air Fryer (Crispy, 90% Less Oil)", badge="Healthy Cooking"),
                    QuestionOption(value="Mixer Grinder", label="Mixer Grinder / Blender (750W - 1000W)", badge="Daily Indian Cooking"),
                    QuestionOption(value="Microwave", label="Microwave Oven / OTG (Baking & Reheating)", badge="Baking & Grill"),
                    QuestionOption(value="Coffee Maker", label="Espresso / Drip Coffee Maker"),
                    QuestionOption(value="Dishwasher", label="Automatic Dishwasher"),
                    QuestionOption(value="Induction", label="Electric Kettle / Induction Cooktop")
                ],
                default_value=type_default,
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Capacity
            questions.append(RequirementQuestion(
                id="capacity",
                question="Capacity / Size?",
                subtext="Volume for single or family meals",
                type="single_choice",
                options=[
                    QuestionOption(value="Small", label="Small (1 - 2 Litres / Compact)", description="Single person or couple"),
                    QuestionOption(value="Medium", label="Medium (3 - 5 Litres / Standard Family)", badge="Sweet Spot", description="Standard 3-5 member household"),
                    QuestionOption(value="Large", label="Large (6+ Litres / Heavy Duty)", badge="Large Batches", description="Large families or dinner gatherings")
                ],
                default_value="Medium",
                importance_weight=1.3,
                category=cat
            ))
            
            # 4. Power
            questions.append(RequirementQuestion(
                id="power",
                question="Power & Motor Wattage?",
                subtext="Fast heating and heavy grinding power",
                type="single_choice",
                options=[
                    QuestionOption(value="1500W+", label="1500W+ (Fast Cooking & Heavy Grinding)", badge="High Power"),
                    QuestionOption(value="1000W - 1400W", label="1000W - 1400W (Balanced Performance)"),
                    QuestionOption(value="500W - 900W", label="500W - 900W (Standard Household)")
                ],
                default_value="1500W+" if type_default == "Air Fryer" else "500W - 900W",
                importance_weight=1.2,
                category=cat
            ))
            
            # 5. Features
            questions.append(RequirementQuestion(
                id="features",
                question="Key Appliance Features?",
                subtext="Convenience and smart cooking programs",
                type="single_choice",
                options=[
                    QuestionOption(value="Digital Touchscreen", label="Digital Touchscreen & One-Touch Presets", badge="Smart Controls"),
                    QuestionOption(value="Auto Shut-Off", label="Auto Shut-Off & Overheat Protection", badge="Safety"),
                    QuestionOption(value="Easy Clean", label="Dishwasher Safe Basket / Easy Clean", badge="Convenience"),
                    QuestionOption(value="Multi-Cooking", label="Multi-Cooking & Temperature Control Dial")
                ],
                default_value="Digital Touchscreen",
                importance_weight=1.2,
                category=cat
            ))
            
            # 6. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Kitchen Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="Philips", label="Philips"),
                    QuestionOption(value="Prestige", label="Prestige"),
                    QuestionOption(value="Bajaj", label="Bajaj"),
                    QuestionOption(value="Bosch", label="Bosch"),
                    QuestionOption(value="Morphy Richards", label="Morphy Richards"),
                    QuestionOption(value="Havells", label="Havells"),
                    QuestionOption(value="Pigeon", label="Pigeon")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "washing_machine":
            # 1. Budget
            default_b = budget if budget else 28000.0
            questions.append(RequirementQuestion(
                id="budget",
                question="What is your budget?",
                subtext="Price in INR for washing machine",
                type="range_slider",
                min_value=10000.0,
                max_value=70000.0,
                step=1000.0,
                default_value=default_b,
                unit="₹",
                importance_weight=1.5,
                category=cat
            ))
            
            # 2. Machine Type
            questions.append(RequirementQuestion(
                id="machine_type",
                question="Washing Machine Type?",
                subtext="Load design and automation",
                type="single_choice",
                options=[
                    QuestionOption(value="front_load", label="Front Load (Best Fabric Care, Water Saving & Inverter)", badge="Recommended"),
                    QuestionOption(value="top_load_auto", label="Top Load Fully Automatic (Ergonomic & Value)", badge="Popular"),
                    QuestionOption(value="semi_auto", label="Semi-Automatic (Economical, Manual Drain)")
                ],
                default_value="front_load",
                importance_weight=1.4,
                category=cat
            ))
            
            # 3. Capacity
            questions.append(RequirementQuestion(
                id="capacity",
                question="Load Capacity (kg)?",
                subtext="Selected for your household size",
                type="single_choice",
                options=[
                    QuestionOption(value="6-7kg", label="6 to 7 kg (1 - 3 Persons)"),
                    QuestionOption(value="7-8kg", label="7 to 8 kg (3 - 5 Persons / Recommended)", badge="Popular"),
                    QuestionOption(value="8kg+", label="8.5 kg+ (Large Family 5+ Persons)", badge="Heavy Load")
                ],
                default_value="7-8kg",
                importance_weight=1.3,
                category=cat
            ))
            
            # 4. Inverter Motor
            questions.append(RequirementQuestion(
                id="inverter",
                question="Inverter Motor?",
                subtext="Quiet direct drive motor with long durability",
                type="single_choice",
                options=[
                    QuestionOption(value="inverter", label="Inverter Direct Drive (Quiet, 10yr warranty)", badge="Energy Efficient"),
                    QuestionOption(value="standard", label="Standard Belt Motor"),
                    QuestionOption(value="any", label="Any Motor Type")
                ],
                default_value="inverter",
                importance_weight=1.2,
                category=cat
            ))
            
            # 5. Brands
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred Brands?",
                type="chip_select",
                options=[
                    QuestionOption(value="LG", label="LG Direct Drive Inverter"),
                    QuestionOption(value="Bosch", label="Bosch German Engineering"),
                    QuestionOption(value="Samsung", label="Samsung EcoBubble"),
                    QuestionOption(value="IFB", label="IFB Aqua Energie"),
                    QuestionOption(value="Whirlpool", label="Whirlpool 6th Sense")
                ],
                default_value=brands if brands else [],
                importance_weight=0.9,
                category=cat
            ))

        elif cat == "skincare":
            # Retain high quality skincare questions
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
                default_value="face_wash" if "face wash" in raw_query else "serum",
                importance_weight=1.4,
                category=cat
            ))
            
            default_concern = "oily_acne" if ("oily" in raw_query or "acne" in raw_query) else "general_glow"
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
            
            questions.append(RequirementQuestion(
                id="brands",
                question="Preferred skincare brands?",
                subtext="Select trusted dermatology or science-backed brands",
                type="chip_select",
                options=[
                    QuestionOption(value="Minimalist", label="Minimalist (Be Minimalist)"),
                    QuestionOption(value="Cetaphil", label="Cetaphil"),
                    QuestionOption(value="The Ordinary", label="The Ordinary"),
                    QuestionOption(value="Plum", label="Plum"),
                    QuestionOption(value="Neutrogena", label="Neutrogena"),
                    QuestionOption(value="CeraVe", label="CeraVe"),
                    QuestionOption(value="Derma Co", label="The Derma Co"),
                    QuestionOption(value="Bioderma", label="Bioderma")
                ],
                default_value=brands if brands else [],
                importance_weight=0.8,
                category=cat
            ))

        elif cat == "hair_care":
            default_b = budget if budget else 800.0
            default_concern = (
                "dandruff" if "dandruff" in raw_query else
                "dryness" if "dry" in raw_query else
                "hair_fall" if "hair fall" in raw_query or "hair growth" in raw_query else
                "oily_scalp" if "oily" in raw_query else "general"
            )
            questions.extend([
                RequirementQuestion(
                    id="hair_concern",
                    question="What is your primary hair concern?",
                    subtext="Choose the hair or scalp need that matters most",
                    type="single_choice",
                    options=[
                        QuestionOption(value="dandruff", label="Dandruff / Flakes"),
                        QuestionOption(value="hair_fall", label="Hair Fall / Strengthening"),
                        QuestionOption(value="dryness", label="Dry Hair"),
                        QuestionOption(value="oily_scalp", label="Oily Scalp / Oil Control"),
                        QuestionOption(value="frizz", label="Frizz / Smoothness"),
                        QuestionOption(value="general", label="General Hair Care"),
                    ],
                    default_value=default_concern,
                    importance_weight=1.5,
                    category=cat,
                ),
                RequirementQuestion(
                    id="budget",
                    question="What is your budget?",
                    subtext="Price in INR for hair-care product",
                    type="range_slider",
                    min_value=200.0,
                    max_value=5000.0,
                    step=50.0,
                    default_value=default_b,
                    unit="₹",
                    importance_weight=1.2,
                    category=cat,
                ),
            ])

        elif cat == "makeup":
            questions.extend([
                RequirementQuestion(
                    id="makeup_goal",
                    question="What is your primary makeup need?",
                    type="single_choice",
                    options=[
                        QuestionOption(value="everyday", label="Everyday Wear"),
                        QuestionOption(value="long_wear", label="Long-Lasting Wear"),
                        QuestionOption(value="sensitive", label="Sensitive Skin"),
                        QuestionOption(value="coverage", label="Coverage / Finish"),
                    ],
                    default_value="everyday",
                    importance_weight=1.3,
                    category=cat,
                ),
                RequirementQuestion(
                    id="budget",
                    question="What is your budget?",
                    type="range_slider",
                    min_value=200.0,
                    max_value=10000.0,
                    step=100.0,
                    default_value=budget if budget else 1500.0,
                    unit="₹",
                    importance_weight=1.2,
                    category=cat,
                ),
            ])

        else:
            # Universal Generic Fallback for any product category
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
                id="primary_use",
                question="What is your primary intended use?",
                subtext="Helps us filter the most suitable specifications",
                type="single_choice",
                options=[
                    QuestionOption(value="everyday", label="Everyday Regular Use", badge="Daily"),
                    QuestionOption(value="heavy_duty", label="Heavy Duty / Professional Grade", badge="Pro"),
                    QuestionOption(value="portable", label="Compact / Travel & Portable", badge="Travel"),
                    QuestionOption(value="special", label="Specialized Purpose / Enthusiast", badge="Enthusiast")
                ],
                default_value="everyday",
                importance_weight=1.3,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="priority",
                question="What is your top priority?",
                subtext="Weights our TrustRank algorithm",
                type="single_choice",
                options=[
                    QuestionOption(value="value_for_money", label="Best Value for Money", description="Maximum features and build quality per Rupee"),
                    QuestionOption(value="highest_rated", label="Highest Customer Rating & Reliability", description="Proven satisfaction and lowest return rate"),
                    QuestionOption(value="premium_quality", label="Top-Tier Premium Build & Specs", description="Uncompromised durability and materials")
                ],
                default_value="value_for_money",
                importance_weight=1.2,
                category=cat
            ))
            
            questions.append(RequirementQuestion(
                id="brand_preference",
                question="Brand Preference?",
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
