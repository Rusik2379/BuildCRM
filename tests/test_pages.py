def test_dashboard_page(client):
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Дашборд' in response.text


def test_documents_page(client):
    response = client.get('/documents')
    assert response.status_code == 200
    assert 'Документы' in response.text
