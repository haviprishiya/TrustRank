import pytest
from app.services.report_service import ReportService
from app.services.coupon_service import CouponService
from app.models.report_schemas import (
    CouponReportCreate,
    GeneralReportCreate,
    ReportStatusUpdate,
    VALID_COUPON_REPORT_REASONS
)
from app.models.schemas import NormalizedProduct

@pytest.fixture(autouse=True)
def setup_reports_db():
    ReportService.initialize_db()
    conn = ReportService.get_db_connection()
    with conn:
        conn.execute("DELETE FROM reports WHERE target_id LIKE 'test_coupon_%' OR target_id LIKE 'test_prod_%'")
        conn.execute("DELETE FROM disabled_coupons WHERE coupon_id LIKE 'test_coupon_%'")
    conn.close()

def test_scenario_1_reporting_non_working_coupon():
    """Test reporting a coupon code that is not working."""
    user_id = "test_user_rep_1"
    report_in = CouponReportCreate(
        coupon_id="test_coupon_101",
        coupon_code="SAVE500",
        marketplace="Amazon India",
        item_title="Sony WH-1000XM5 Headphones",
        reason="Coupon code is not working.",
        description="The coupon code SAVE500 returned 'Invalid promotional code' on Amazon checkout.",
        product_url="https://amazon.in/dp/example101"
    )

    res = ReportService.submit_coupon_report(user_id=user_id, data=report_in)
    assert res.id.startswith("rep_")
    assert res.report_type == "coupon"
    assert res.target_id == "test_coupon_101"
    assert res.coupon_code == "SAVE500"
    assert res.reason == "Coupon code is not working."
    assert res.status == "Pending"
    assert res.user_id == user_id

def test_scenario_2_reporting_expired_coupon():
    """Test reporting an expired coupon."""
    user_id = "test_user_rep_2"
    report_in = CouponReportCreate(
        coupon_id="test_coupon_102",
        coupon_code="DIWALI2024",
        marketplace="Flipkart",
        item_title="Apple iPad 10th Gen",
        reason="Coupon has expired.",
        description="Expired on October 31st.",
        product_url="https://flipkart.com/p/example102"
    )

    res = ReportService.submit_coupon_report(user_id=user_id, data=report_in)
    assert res.reason == "Coupon has expired."
    assert res.status == "Pending"
    assert res.marketplace == "Flipkart"

def test_scenario_3_reporting_incorrect_discount():
    """Test reporting an incorrect discount amount."""
    user_id = "test_user_rep_3"
    report_in = CouponReportCreate(
        coupon_id="test_coupon_103",
        coupon_code="FLAT20",
        marketplace="Amazon India",
        item_title="Logitech MX Master 3S Mouse",
        reason="Incorrect discount amount.",
        description="Listing shows 20% off but coupon only gives 5% at payment page.",
        product_url="https://amazon.in/dp/example103"
    )

    res = ReportService.submit_coupon_report(user_id=user_id, data=report_in)
    assert res.reason == "Incorrect discount amount."
    assert "20% off" in res.description

def test_scenario_4_submitting_optional_description():
    """Test submitting report with and without optional description."""
    user_id = "test_user_rep_4"

    # With description
    res_with = ReportService.submit_coupon_report(
        user_id=user_id,
        data=CouponReportCreate(
            coupon_id="test_coupon_104a",
            coupon_code="TECH10",
            marketplace="Amazon India",
            item_title="Anker Power Bank",
            reason="Misleading offer.",
            description="Offer specifies free shipping but shipping cost ₹150 was added."
        )
    )
    assert res_with.description == "Offer specifies free shipping but shipping cost ₹150 was added."

    # Without description (None)
    res_without = ReportService.submit_coupon_report(
        user_id=user_id,
        data=CouponReportCreate(
            coupon_id="test_coupon_104b",
            coupon_code="TECH20",
            marketplace="Amazon India",
            item_title="Anker Power Bank",
            reason="Invalid coupon code.",
            description=None
        )
    )
    assert res_without.description is None

def test_scenario_5_preventing_duplicate_reports():
    """Test preventing duplicate reports from the same user for the same coupon."""
    user_id = "test_user_rep_5"
    report_in = CouponReportCreate(
        coupon_id="test_coupon_105",
        coupon_code="DUPTEST",
        marketplace="Amazon India",
        item_title="Samsung S24 Ultra",
        reason="Coupon code is not working.",
        description="First submission"
    )

    # First submission should succeed
    res1 = ReportService.submit_coupon_report(user_id=user_id, data=report_in)
    assert res1.id is not None

    # Immediate second submission by same user for same coupon should be rejected
    with pytest.raises(ValueError, match="already submitted an active report"):
        ReportService.submit_coupon_report(user_id=user_id, data=report_in)

    # Another user reporting same coupon should be allowed
    res_other_user = ReportService.submit_coupon_report(
        user_id="different_user_99",
        data=report_in
    )
    assert res_other_user.id != res1.id

def test_scenario_6_admin_viewing_and_updating_status():
    """Test admin fetching reports and updating status with resolution notes."""
    user_id = "test_user_rep_6"
    rep = ReportService.submit_coupon_report(
        user_id=user_id,
        data=CouponReportCreate(
            coupon_id="test_coupon_106",
            coupon_code="EXPIRED50",
            marketplace="Amazon India",
            item_title="Dell XPS 15 Laptop",
            reason="Coupon has expired.",
            description="Expired yesterday"
        )
    )

    # Admin lists reports
    reports_res = ReportService.get_reports(report_type="coupon", status="Pending")
    found = any(r.id == rep.id for r in reports_res.reports)
    assert found is True
    assert reports_res.pending_count >= 1

    # Admin marks as Reviewed
    reviewed = ReportService.update_report_status(
        report_id=rep.id,
        data=ReportStatusUpdate(status="Reviewed", admin_notes="Checking with marketplace API"),
        admin_user="moderator_alice"
    )
    assert reviewed.status == "Reviewed"
    assert reviewed.admin_notes == "Checking with marketplace API"

    # Admin investigates and disables the expired coupon
    resolved = ReportService.update_report_status(
        report_id=rep.id,
        data=ReportStatusUpdate(status="Resolved", admin_notes="Verified expired on Amazon. Deactivated coupon.", disable_coupon=True),
        admin_user="moderator_alice"
    )
    assert resolved.status == "Resolved"
    assert resolved.action_taken == "coupon_disabled"

    # Verify coupon is recorded in disabled_coupons
    disabled_ids = ReportService.get_disabled_coupon_ids()
    assert "test_coupon_106" in disabled_ids
    assert "EXPIRED50" in disabled_ids

def test_scenario_7_existing_product_reports_continue_working():
    """Test ensuring general product reports work concurrently with coupon reports."""
    user_id = "test_user_rep_7"
    prod_report = GeneralReportCreate(
        report_type="product",
        target_id="test_prod_777",
        item_title="Inaccurate Spec Smartphone",
        marketplace="Amazon India",
        reason="Incorrect specifications listed",
        description="Camera is listed as 108MP but box says 50MP"
    )

    res = ReportService.submit_general_report(user_id=user_id, data=prod_report)
    assert res.report_type == "product"
    assert res.target_id == "test_prod_777"
    assert res.status == "Pending"

    # Verify filtered listing retrieves both appropriately
    all_reports = ReportService.get_reports(report_type="all")
    assert any(r.target_id == "test_prod_777" for r in all_reports.reports)

    coupon_only = ReportService.get_reports(report_type="coupon")
    assert not any(r.target_id == "test_prod_777" for r in coupon_only.reports)

def test_scenario_8_disabled_coupon_is_filtered_from_offers():
    """Test that once a coupon is disabled by admin, it is excluded from CouponService listings."""
    # Create mock product with coupon code
    mock_prod = NormalizedProduct(
        id="test_prod_offer_8",
        title="Gaming Laptop 16GB RAM",
        brand="ASUS",
        current_price=65000.0,
        original_price=75000.0,
        marketplace="Amazon India",
        features=["Use coupon GAMER10 for instant discount"],
        category="laptop",
        image_url=None,
        rating=4.5,
        review_count=100,
        availability="In Stock",
        product_url="https://amazon.in/dp/laptop8",
        provider="amazon"
    )

    offers = CouponService.extract_offers_from_product(mock_prod)
    assert len(offers) > 0
    test_offer = offers[0]

    # Submit report and disable coupon
    rep = ReportService.submit_coupon_report(
        user_id="test_user_8",
        data=CouponReportCreate(
            coupon_id=test_offer.id,
            coupon_code=test_offer.coupon_code,
            marketplace=test_offer.marketplace,
            item_title=test_offer.title,
            reason="Coupon has expired."
        )
    )
    ReportService.update_report_status(
        report_id=rep.id,
        data=ReportStatusUpdate(status="Resolved", disable_coupon=True)
    )

    # Verify disabled set
    disabled = ReportService.get_disabled_coupon_ids()
    assert test_offer.id in disabled or (test_offer.coupon_code and test_offer.coupon_code.upper() in disabled)
