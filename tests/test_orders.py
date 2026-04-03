def seed_product(client):
    client.post('/products', data={
        'name': 'Кирпич 1NF',
        'category': 'Кирпич',
        'unit': 'шт',
        'purchase_price': '10',
        'retail_price': '14',
        'small_opt_price': '12',
        'large_opt_price': '11',
    })


def test_create_retail_order_auto_creates_client(client):
    seed_product(client)
    response = client.post('/orders/retail', data={
        'client_name': 'Руслан',
        'client_phone': '89990000000',
        'client_source': 'Telegram',
        'client_category': 'Частник',
        'product_name': 'Кирпич 1NF',
        'product_category': 'Кирпич',
        'product_unit': 'шт',
        'quantity': '10',
        'pricing_tier': 'retail',
        'status': 'new',
        'payment_method': 'cash',
        'delivery_type': 'pickup',
        'delivery_cost': '0',
        'additional_costs': '0',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert '#1' in response.text
    detail = client.get('/clients/1')
    assert 'Розничные заявки' in detail.text
    assert 'Руслан' in detail.text


def test_wholesale_order_updates_driver_and_supplier_balances(client):
    seed_product(client)
    client.post('/suppliers', data={'name': 'Поставщик 1', 'balance': '1000'})
    client.post('/drivers', data={'name': 'Водитель 1'})
    response = client.post('/orders/wholesale', data={
        'client_name': 'Оптовик',
        'client_phone': '8123',
        'client_source': '2ГИС',
        'client_category': 'База',
        'product_name': 'Кирпич 1NF',
        'product_category': 'Кирпич',
        'product_unit': 'шт',
        'quantity': '20',
        'pricing_tier': 'small_opt',
        'status': 'new',
        'payment_method': 'driver_payment',
        'delivery_type': 'delivery',
        'delivery_cost': '100',
        'additional_costs': '50',
        'supplier_id': '1',
        'driver_id': '1',
        'use_supplier_balance': 'on',
    }, follow_redirects=True)
    assert response.status_code == 200
    drivers_page = client.get('/drivers')
    assert '340.00' in drivers_page.text
    suppliers_page = client.get('/suppliers')
    assert '800.00' in suppliers_page.text
