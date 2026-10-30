import pytest
from app.services.alert_service import AlertService
from app.models.alert_schemas import PriceAlertCreate

def test_price_alert_full_lifecycle():
    AlertService.initialize_db()
    user_id = "test_alert_user_99"

    # Clean existing
    existing = AlertService.get_user_alerts(user_id)
    for a in existing.alerts:
        AlertService.delete_alert(user_id, a.id)

    # 1. Create alert with valid target price
    alert_in = PriceAlertCreate(
        product_id="test_prod_100",
        product_title="Sony WH-1000XM5 Wireless Headphones",
        marketplace="Amazon India",
        current_price=26990.0,
        target_price=22000.0,
        product_url="https://amazon.in/dp/example"
    )
    alert = AlertService.create_alert(user_id=user_id, data=alert_in)
    assert alert.product_id == "test_prod_100"
    assert alert.current_price == 26990.0
    assert alert.target_price == 22000.0
    assert alert.price_difference == 4990.0
    assert alert.status == "active"
    assert alert.notified is False

    # 2. Duplicate prevention (updating target price for same product)
    alert_updated_in = PriceAlertCreate(
        product_id="test_prod_100",
        product_title="Sony WH-1000XM5 Wireless Headphones",
        marketplace="Amazon India",
        current_price=26990.0,
        target_price=24000.0
    )
    alert2 = AlertService.create_alert(user_id=user_id, data=alert_updated_in)
    assert alert2.id == alert.id
    assert alert2.target_price == 24000.0

    # 3. List alerts
    list_res = AlertService.get_user_alerts(user_id)
    assert list_res.total_alerts == 1
    assert list_res.active_alerts == 1

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
