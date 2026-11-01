import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.alert_service import AlertService
from app.services.email_service import EmailService
from app.models.alert_schemas import PriceAlertCreate

class MockMarketplaceProduct:
    def __init__(self, id, title, current_price, product_url="https://amazon.in/dp/B0EXAMPLE1", asin=None):
        self.id = id
        self.asin = asin
        self.title = title
        self.current_price = current_price
        self.product_url = product_url

def cleanup_user_alerts(user_id: str):
    AlertService.initialize_db()
    existing = AlertService.get_user_alerts(user_id)
    for a in existing.alerts:
        AlertService.delete_alert(user_id, a.id)

def test_price_alert_full_lifecycle():
    user_id = "test_alert_user_99"
    cleanup_user_alerts(user_id)

    # 1. Create alert with valid target price
    alert_in = PriceAlertCreate(
        product_id="test_prod_100",
        product_title="Sony WH-1000XM5 Wireless Headphones",
        marketplace="Amazon India",
        current_price=26990.0,
        target_price=22000.0,
        product_url="https://amazon.in/dp/example",
        user_email="buyer@example.com"
    )
    alert = AlertService.create_alert(user_id=user_id, data=alert_in)
    assert alert.product_id == "test_prod_100"
    assert alert.current_price == 26990.0
    assert alert.target_price == 22000.0
    assert alert.price_difference == 4990.0
    assert alert.status == "active"
    assert alert.notified is False
    assert alert.user_email_masked == "b***r@example.com"
    assert alert.email_status == "pending"

    # 2. Duplicate prevention (updating target price for same product)
    alert_updated_in = PriceAlertCreate(
        product_id="test_prod_100",
        product_title="Sony WH-1000XM5 Wireless Headphones",
        marketplace="Amazon India",
        current_price=26990.0,
        target_price=24000.0,
        user_email="buyer@example.com"
    )
    alert2 = AlertService.create_alert(user_id=user_id, data=alert_updated_in)
    assert alert2.id == alert.id
    assert alert2.target_price == 24000.0

    # 3. List alerts
    list_res = AlertService.get_user_alerts(user_id)
    assert list_res.total_alerts == 1
    assert list_res.active_alerts == 1
    assert list_res.alerts[0].user_email_masked == "b***r@example.com"

    # 4. Update status: disable and re-enable
    AlertService.update_alert_status(user_id=user_id, alert_id=alert.id, new_status="disabled")
    dis_res = AlertService.get_user_alerts(user_id)
    assert dis_res.alerts[0].status == "disabled"
    assert dis_res.active_alerts == 0

    AlertService.update_alert_status(user_id=user_id, alert_id=alert.id, new_status="active")
    act_res = AlertService.get_user_alerts(user_id)
    assert act_res.alerts[0].status == "active"

    # 5. Delete alert
    deleted = AlertService.delete_alert(user_id=user_id, alert_id=alert.id)
    assert deleted is True
    assert AlertService.get_user_alerts(user_id).total_alerts == 0

@pytest.mark.asyncio
async def test_scenario_1_price_above_target_no_email():
    """Scenario 1: Verified price is above target -> Alert remains active, no email sent."""
    user_id = "test_user_scen1"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen1",
        product_title="Apple iPad 10th Gen WiFi 64GB",
        marketplace="Amazon India",
        current_price=34900.0,
        target_price=30000.0,
        product_url="https://amazon.in/dp/IPAD10",
        user_email="ipadlover@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen1",
        title="Apple iPad 10th Gen WiFi 64GB",
        current_price=32000.0, # still > 30000
        product_url="https://amazon.in/dp/IPAD10"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        res = await AlertService.check_alerts(user_id=user_id)

        assert res.checked_count == 1
        assert res.triggered_count == 0
        mock_email.assert_not_called()

        alerts = AlertService.get_user_alerts(user_id)
        assert alerts.alerts[0].status == "active"
        assert alerts.alerts[0].current_price == 32000.0
        assert alerts.alerts[0].email_status == "pending"

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_2_price_equals_target_triggers_email():
    """Scenario 2: Verified price equals target -> Alert triggers, email sent once."""
    user_id = "test_user_scen2"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen2",
        product_title="Logitech MX Master 3S Wireless Mouse",
        marketplace="Amazon India",
        current_price=8999.0,
        target_price=7999.0,
        product_url="https://amazon.in/dp/MXMASTER",
        user_email="developer@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen2",
        title="Logitech MX Master 3S Wireless Mouse",
        current_price=7999.0, # exact match with target
        product_url="https://amazon.in/dp/MXMASTER"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        mock_email.return_value = {"status": "sent", "recipient": "d***r@example.com", "error": None}

        res = await AlertService.check_alerts(user_id=user_id)

        assert res.checked_count == 1
        assert res.triggered_count == 1
        assert mock_email.call_count == 1

        alerts = AlertService.get_user_alerts(user_id)
        assert alerts.alerts[0].status == "target_reached"
        assert alerts.alerts[0].current_price == 7999.0
        assert alerts.alerts[0].notified is True
        assert alerts.alerts[0].email_status == "sent"
        assert alerts.alerts[0].email_sent_at is not None

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_3_price_below_target_triggers_email():
    """Scenario 3: Verified price drops below target -> Alert triggers with savings details."""
    user_id = "test_user_scen3"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen3",
        product_title="Samsung Galaxy S24 Ultra 5G",
        marketplace="Amazon India",
        current_price=129999.0,
        target_price=110000.0,
        product_url="https://amazon.in/dp/S24ULTRA",
        user_email="shopper@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen3",
        title="Samsung Galaxy S24 Ultra 5G",
        current_price=104999.0, # below target
        product_url="https://amazon.in/dp/S24ULTRA"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        mock_email.return_value = {"status": "sent", "recipient": "s***r@example.com", "error": None}

        res = await AlertService.check_alerts(user_id=user_id)

        assert res.checked_count == 1
        assert res.triggered_count == 1
        assert mock_email.call_count == 1

        args, kwargs = mock_email.call_args
        assert kwargs["current_price"] == 104999.0
        assert kwargs["target_price"] == 110000.0

        alerts = AlertService.get_user_alerts(user_id)
        assert alerts.alerts[0].status == "target_reached"
        assert alerts.alerts[0].email_status == "sent"

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_4_repeated_checks_no_duplicate_email():
    """Scenario 4: Periodic worker running repeatedly -> Dispatches email only once."""
    user_id = "test_user_scen4"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen4",
        product_title="Kindle Paperwhite 16GB",
        marketplace="Amazon India",
        current_price=14999.0,
        target_price=12999.0,
        product_url="https://amazon.in/dp/KINDLE",
        user_email="reader@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen4",
        title="Kindle Paperwhite 16GB",
        current_price=11999.0,
        product_url="https://amazon.in/dp/KINDLE"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        mock_email.return_value = {"status": "sent", "recipient": "r***r@example.com", "error": None}

        # First run: triggers alert and sends email
        res1 = await AlertService.check_alerts(user_id=user_id)
        assert res1.triggered_count == 1
        assert mock_email.call_count == 1

        # Second run: alert already reached target, should NOT be queried or notified again
        res2 = await AlertService.check_alerts(user_id=user_id)
        assert res2.checked_count == 0
        assert res2.triggered_count == 0
        # Call count must strictly remain 1 (no duplicates)
        assert mock_email.call_count == 1

    cleanup_user_alerts(user_id)

def test_scenario_5_invalid_email_format_rejected():
    """Scenario 5: Invalid email formats are rejected before saving."""
    user_id = "test_user_scen5"
    cleanup_user_alerts(user_id)

    # 1. Invalid email in create_alert
    with pytest.raises(ValueError, match="Invalid email address format"):
        AlertService.create_alert(
            user_id=user_id,
            data=PriceAlertCreate(
                product_id="prod_scen5",
                product_title="Test Product",
                marketplace="Amazon India",
                current_price=1000.0,
                target_price=800.0,
                user_email="not-an-email"
            )
        )

    # 2. Invalid email in update_user_email
    with pytest.raises(ValueError, match="Invalid email address format"):
        AlertService.update_user_email(user_id=user_id, email="missing-domain@")

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_6_missing_smtp_credentials_recorded_safely():
    """Scenario 6: Missing SMTP credentials sets status 'not_configured' without crashing."""
    user_id = "test_user_scen6"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen6",
        product_title="Bose QuietComfort Headphones",
        marketplace="Amazon India",
        current_price=29900.0,
        target_price=25000.0,
        product_url="https://amazon.in/dp/BOSEQC",
        user_email="audiophile@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen6",
        title="Bose QuietComfort Headphones",
        current_price=24500.0,
        product_url="https://amazon.in/dp/BOSEQC"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        # Simulating unconfigured SMTP response
        mock_email.return_value = {
            "status": "not_configured",
            "recipient": "a***e@example.com",
            "error": "SMTP server not configured. Please set SMTP_HOST in backend/.env."
        }

        res = await AlertService.check_alerts(user_id=user_id)
        assert res.triggered_count == 1

        alerts = AlertService.get_user_alerts(user_id)
        assert alerts.alerts[0].status == "target_reached"
        assert alerts.alerts[0].email_status == "not_configured"
        assert alerts.alerts[0].email_sent_at is None
        assert "SMTP server not configured" in alerts.alerts[0].email_error

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_7_smtp_failure_handled_safely():
    """Scenario 7: SMTP delivery failure is caught and recorded cleanly as 'failed'."""
    user_id = "test_user_scen7"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen7",
        product_title="Dell XPS 15 Laptop",
        marketplace="Amazon India",
        current_price=149990.0,
        target_price=130000.0,
        product_url="https://amazon.in/dp/DELLXPS",
        user_email="coder@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen7",
        title="Dell XPS 15 Laptop",
        current_price=125000.0,
        product_url="https://amazon.in/dp/DELLXPS"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        # Simulating SMTP delivery failure
        mock_email.return_value = {
            "status": "failed",
            "recipient": "c***r@example.com",
            "error": "ConnectionRefusedError: [Errno 111] Connection refused"
        }

        res = await AlertService.check_alerts(user_id=user_id)
        assert res.triggered_count == 1

        alerts = AlertService.get_user_alerts(user_id)
        assert alerts.alerts[0].status == "target_reached"
        assert alerts.alerts[0].email_status == "failed"
        assert alerts.alerts[0].email_sent_at is None
        assert "Connection refused" in alerts.alerts[0].email_error

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_8_disabled_or_deleted_no_email():
    """Scenario 8: Disabled or deleted alerts are never emailed; reactivating resets trigger."""
    user_id = "test_user_scen8"
    cleanup_user_alerts(user_id)

    alert_in = PriceAlertCreate(
        product_id="prod_scen8",
        product_title="Anker 737 Power Bank",
        marketplace="Amazon India",
        current_price=12999.0,
        target_price=10000.0,
        product_url="https://amazon.in/dp/ANKER737",
        user_email="techie@example.com"
    )
    alert = AlertService.create_alert(user_id=user_id, data=alert_in)

    # Disable alert
    AlertService.update_alert_status(user_id=user_id, alert_id=alert.id, new_status="disabled")

    mock_live = MockMarketplaceProduct(
        id="prod_scen8",
        title="Anker 737 Power Bank",
        current_price=8999.0, # well below target
        product_url="https://amazon.in/dp/ANKER737"
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]

        # Disabled alert should NOT be checked or emailed
        res = await AlertService.check_alerts(user_id=user_id)
        assert res.checked_count == 0
        mock_email.assert_not_called()

        # Reactivate alert
        AlertService.update_alert_status(user_id=user_id, alert_id=alert.id, new_status="active")
        reactivated = AlertService.get_user_alerts(user_id).alerts[0]
        assert reactivated.status == "active"
        assert reactivated.notified is False
        assert reactivated.email_status == "pending"

        # Now checking it sends email
        mock_email.return_value = {"status": "sent", "recipient": "t***e@example.com", "error": None}
        res2 = await AlertService.check_alerts(user_id=user_id)
        assert res2.triggered_count == 1
        assert mock_email.call_count == 1

    cleanup_user_alerts(user_id)

@pytest.mark.asyncio
async def test_scenario_9_genuine_product_link_verified():
    """Scenario 9: Verified genuine product link is passed to email dispatch and preserved."""
    user_id = "test_user_scen9"
    cleanup_user_alerts(user_id)

    genuine_url = "https://www.amazon.in/dp/B0CX2100XX?tag=trustrank-21"
    alert_in = PriceAlertCreate(
        product_id="prod_scen9",
        product_title="Apple Watch Series 9 GPS 45mm",
        marketplace="Amazon India",
        current_price=44900.0,
        target_price=39900.0,
        product_url=genuine_url,
        user_email="fitness@example.com"
    )
    AlertService.create_alert(user_id=user_id, data=alert_in)

    mock_live = MockMarketplaceProduct(
        id="prod_scen9",
        title="Apple Watch Series 9 GPS 45mm",
        current_price=38900.0,
        product_url=genuine_url
    )

    with patch("app.services.alert_service.provider_registry.search_all", new_callable=AsyncMock) as mock_search, \
         patch("app.services.alert_service.EmailService.send_price_drop_email", new_callable=AsyncMock) as mock_email:
        mock_search.return_value = [mock_live]
        mock_email.return_value = {"status": "sent", "recipient": "f***s@example.com", "error": None}

        await AlertService.check_alerts(user_id=user_id)

        assert mock_email.call_count == 1
        _, kwargs = mock_email.call_args
        assert kwargs["product_url"] == genuine_url
        assert kwargs["product_title"] == "Apple Watch Series 9 GPS 45mm"

        alerts = AlertService.get_user_alerts(user_id)
        assert alerts.alerts[0].product_url == genuine_url

    cleanup_user_alerts(user_id)
