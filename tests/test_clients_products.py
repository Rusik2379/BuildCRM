def test_create_client_and_view_detail(client):
    response = client.post('/clients', data={
        'name': 'Иван Петров',
        'phone': '+7 (999) 111-22-33',
        'address': 'Барнаул',
        'source': 'Авито',
        'category': 'Частник',
        'notes': 'Тестовый клиент',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Иван Петров' in response.text

    detail = client.get('/clients/1')
    assert detail.status_code == 200
    assert 'Авито' in detail.text
    assert 'Частник' in detail.text


def test_create_product_and_stock(client):
    product_resp = client.post('/products', data={
        'name': 'Газоблок D500',
        'category': 'Газоблок',
        'unit': 'шт',
        'description': 'Серый',
        'purchase_price': '100',
        'retail_price': '114',
        'small_opt_price': '110',
        'large_opt_price': '105',
    }, follow_redirects=True)
    assert product_resp.status_code == 200
    assert 'Газоблок D500' in product_resp.text

    stock_resp = client.post('/stock', data={
        'product_id': '1',
        'warehouse_name': 'Основной склад',
        'city': 'Барнаул',
        'quantity': '25',
        'notes': 'Партия 1',
    }, follow_redirects=True)
    assert stock_resp.status_code == 200
    assert 'Основной склад' in stock_resp.text
    assert '25.00' in stock_resp.text
