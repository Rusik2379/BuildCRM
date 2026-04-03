def test_finance_page_with_data(client):
    client.post('/products', data={
        'name': 'Цемент М500', 'category': 'Цемент', 'unit': 'мешок',
        'purchase_price': '300', 'retail_price': '342', 'small_opt_price': '330', 'large_opt_price': '315'
    })
    client.post('/orders/retail', data={
        'client_name': 'Клиент А', 'client_phone': '7000', 'product_name': 'Цемент М500',
        'product_category': 'Цемент', 'product_unit': 'мешок', 'quantity': '2',
        'pricing_tier': 'retail', 'status': 'done', 'payment_method': 'cash',
        'delivery_type': 'pickup', 'delivery_cost': '0', 'additional_costs': '10'
    })
    response = client.get('/finances')
    assert response.status_code == 200
    assert '684.00' in response.text
    assert '74.00' in response.text
