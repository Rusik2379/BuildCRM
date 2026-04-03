from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from app.db import build_session_factory, init_db
from app.models import (
    Client,
    Driver,
    DriverCashMovement,
    GeneralExpense,
    Order,
    OrderItem,
    Product,
    StockItem,
    Supplier,
    SupplierBalanceMovement,
    Warehouse,
)
from app.services import product_price_for_tier, recalculate_order

ROOT = Path(__file__).resolve().parent


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def dec(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value)).quantize(Decimal('0.01'))


def seed_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()

    engine, SessionLocal = build_session_factory(f"sqlite:///{db_path}")
    init_db(engine)
    session = SessionLocal()

    try:
        warehouses = {
            'Основной склад': Warehouse(name='Основной склад', location='Барнаул, Попова 14', created_at=dt('2025-09-01T10:00:00')),
            'Северный склад': Warehouse(name='Северный склад', location='Барнаул, Павловский тракт 63', created_at=dt('2025-10-05T10:00:00')),
        }
        session.add_all(warehouses.values())

        suppliers = {
            'МеталлТорг': Supplier(name='МеталлТорг', city='Барнаул', phone='8 923 700-11-22', notes='Профлист, арматура, крепёж', created_at=dt('2025-09-02T10:00:00')),
            'СибЦемент': Supplier(name='СибЦемент', city='Новоалтайск', phone='8 913 555-20-20', notes='Цемент и сухие смеси', created_at=dt('2025-09-03T10:00:00')),
            'ЛесСнаб': Supplier(name='ЛесСнаб', city='Барнаул', phone='8 905 111-33-77', notes='Пиломатериалы, OSB', created_at=dt('2025-09-04T10:00:00')),
            'ТеплоСтрой': Supplier(name='ТеплоСтрой', city='Барнаул', phone='8 923 444-55-66', notes='Утеплитель и плёнки', created_at=dt('2025-09-05T10:00:00')),
            'Газоблок Сибирь': Supplier(name='Газоблок Сибирь', city='Бийск', phone='8 913 900-00-12', notes='Газоблок и кирпич', created_at=dt('2025-09-06T10:00:00')),
        }
        session.add_all(suppliers.values())

        drivers = {
            'Иван Шишкин': Driver(name='Иван Шишкин', phone='8 923 010-10-10', vehicle='Газель 4м', notes='Город/межгород', created_at=dt('2025-09-10T10:00:00')),
            'Павел Романов': Driver(name='Павел Романов', phone='8 913 020-20-20', vehicle='Манипулятор', notes='Для тяжёлых грузов', created_at=dt('2025-09-11T10:00:00')),
            'Олег Ермаков': Driver(name='Олег Ермаков', phone='8 905 030-30-30', vehicle='Самосвал', notes='Сыпучка и поддоны', created_at=dt('2025-09-12T10:00:00')),
        }
        session.add_all(drivers.values())
        session.flush()

        initial_supplier_balances = [
            ('МеталлТорг', '85000', 'Стартовый депозит у поставщика', '2025-10-01T09:00:00'),
            ('СибЦемент', '60000', 'Предоплата на сезон', '2025-10-02T09:30:00'),
            ('ЛесСнаб', '35000', 'Депозит под пиломатериалы', '2025-10-03T09:45:00'),
        ]
        for supplier_name, amount, reason, created_at in initial_supplier_balances:
            supplier = suppliers[supplier_name]
            supplier.balance = dec(supplier.balance or 0) + dec(amount)
            session.add(
                SupplierBalanceMovement(
                    supplier=supplier,
                    amount=dec(amount),
                    reason=reason,
                    created_at=dt(created_at),
                )
            )

        initial_driver_cash = [
            ('Иван Шишкин', '12000', 'Размен и стартовая касса на доставку', '2025-10-01T11:00:00'),
            ('Павел Романов', '8000', 'Стартовая касса манипулятора', '2025-10-04T11:00:00'),
        ]
        for driver_name, amount, reason, created_at in initial_driver_cash:
            driver = drivers[driver_name]
            driver.cash_on_hand = dec(driver.cash_on_hand or 0) + dec(amount)
            session.add(
                DriverCashMovement(
                    driver=driver,
                    amount=dec(amount),
                    reason=reason,
                    created_at=dt(created_at),
                )
            )

        product_rows = [
            ('Профлист С8 0.45', 'Профлист', 'лист', 'МеталлТорг', '620', '760', '740', '720', True),
            ('Арматура 12мм', 'Крепёж', 'т', 'МеталлТорг', '46500', '51900', '50500', '49200', True),
            ('Саморез кровельный 5.5x19', 'Крепёж', 'шт', 'МеталлТорг', '3.80', '5.20', '4.90', '4.70', True),
            ('Цемент М500 50кг', 'Цемент', 'мешок', 'СибЦемент', '350', '430', '415', '405', True),
            ('Клей для газоблока 25кг', 'Сухие смеси', 'мешок', 'СибЦемент', '220', '285', '275', '268', True),
            ('Доска обрезная 50x150x6000', 'Пиломатериалы', 'м3', 'ЛесСнаб', '14200', '16450', '15900', '15400', True),
            ('Брус 100x100x6000', 'Пиломатериалы', 'м3', 'ЛесСнаб', '14800', '17200', '16650', '16100', True),
            ('OSB-3 9мм', 'Пиломатериалы', 'лист', 'ЛесСнаб', '730', '910', '885', '860', True),
            ('Минвата 50мм', 'Утеплитель', 'паллета', 'ТеплоСтрой', '12800', '14900', '14450', '14000', True),
            ('Пароизоляция 70м2', 'Утеплитель', 'рулон', 'ТеплоСтрой', '850', '1070', '1035', '1000', False),
            ('Газоблок D500 600x300x200', 'Газоблок', 'шт', 'Газоблок Сибирь', '132', '165', '160', '155', True),
            ('Кирпич облицовочный', 'Кирпич', 'шт', 'Газоблок Сибирь', '24', '31', '29.5', '28', True),
        ]

        products: dict[str, Product] = {}
        for name, category, unit, supplier_name, purchase, retail, small_opt, large_opt, is_wholesale in product_rows:
            product = Product(
                name=name,
                category=category,
                unit=unit,
                supplier=suppliers[supplier_name],
                purchase_price=dec(purchase),
                retail_price=dec(retail),
                small_opt_price=dec(small_opt),
                large_opt_price=dec(large_opt),
                is_wholesale=is_wholesale,
                created_at=dt('2025-10-10T10:00:00'),
            )
            products[name] = product
            session.add(product)
        session.flush()

        stock_rows = [
            ('Профлист С8 0.45', 'Основной склад', '180', 'Остаток по ходовой позиции'),
            ('Арматура 12мм', 'Основной склад', '14.5', 'Тонны на уличном складе'),
            ('Саморез кровельный 5.5x19', 'Основной склад', '12000', 'Коробами'),
            ('Цемент М500 50кг', 'Основной склад', '340', 'В мешках, сухой склад'),
            ('Клей для газоблока 25кг', 'Северный склад', '210', 'Под зимние объекты'),
            ('Доска обрезная 50x150x6000', 'Северный склад', '22.4', 'Под навесом'),
            ('Брус 100x100x6000', 'Северный склад', '9.8', 'Под навесом'),
            ('OSB-3 9мм', 'Основной склад', '130', 'Листовой материал'),
            ('Минвата 50мм', 'Северный склад', '18', 'Паллеты'),
            ('Пароизоляция 70м2', 'Основной склад', '65', 'Рулоны'),
            ('Газоблок D500 600x300x200', 'Основной склад', '2400', 'Поддоны на площадке'),
            ('Кирпич облицовочный', 'Северный склад', '5600', 'Поддонный остаток'),
        ]
        for product_name, warehouse_name, quantity, notes in stock_rows:
            session.add(
                StockItem(
                    product=products[product_name],
                    warehouse=warehouses[warehouse_name],
                    supplier=products[product_name].supplier,
                    quantity=dec(quantity),
                    notes=notes,
                    updated_at=dt('2026-03-28T16:00:00'),
                )
            )

        clients = {
            'Никита Соколов': Client(name='Никита Соколов', phone='79130001122', client_type='retail', address='Барнаул, Взлётная 34', source='Авито', category='Частник', notes='Коттедж, повторный звонок', created_at=dt('2025-10-20T10:00:00')),
            'Алексей Панов': Client(name='Алексей Панов', phone='79135552211', client_type='retail', address='Барнаул, Шумакова 18', source='2ГИС', category='Частник', notes='Нужна доставка день в день', created_at=dt('2025-11-01T09:00:00')),
            'ИП Кузнецов': Client(name='ИП Кузнецов', phone='79039112233', client_type='wholesale', address='Барнаул, Попова 171', source='Сайт', category='Подрядчик', notes='Берут газоблок и клей', created_at=dt('2025-11-05T11:00:00')),
            'ООО АлтайФасад': Client(name='ООО АлтайФасад', phone='79001230045', client_type='wholesale', address='Новоалтайск, Промышленная 7', source='Telegram', category='Подрядчик', notes='Безнал, пакет документов', created_at=dt('2025-11-07T11:00:00')),
            'Сергей Громов': Client(name='Сергей Громов', phone='79139870011', client_type='retail', address='Барнаул, Лазурная 41', source='Сарафанка', category='Частник', notes='Строит баню', created_at=dt('2025-11-10T15:00:00')),
            'База Север': Client(name='База Север', phone='79009994411', client_type='wholesale', address='Барнаул, Северный Власихинский проезд 49', source='Повторный клиент', category='База', notes='Крупный опт по пиломатериалу', created_at=dt('2025-12-01T10:00:00')),
            'Максим Юдин': Client(name='Максим Юдин', phone='79130151515', client_type='retail', address='Барнаул, Энтузиастов 52', source='ВК', category='Частник', notes='Интересует утепление кровли', created_at=dt('2025-12-14T12:00:00')),
            'Прораб Плюс': Client(name='Прораб Плюс', phone='79038887766', client_type='wholesale', address='Барнаул, Калинина 24', source='Авито', category='Прораб', notes='Нужны счета и ТОРГ-12', created_at=dt('2026-01-05T12:00:00')),
            'Елена Фадеева': Client(name='Елена Фадеева', phone='79131113377', client_type='retail', address='Барнаул, Балтийская 88', source='Другое', category='Частник', notes='Покупает по мелочи', created_at=dt('2026-01-20T14:00:00')),
            'ООО Монолит': Client(name='ООО Монолит', phone='79047778811', client_type='wholesale', address='Барнаул, Павловский тракт 305г', source='2ГИС', category='Подрядчик', notes='Берут цемент и арматуру', created_at=dt('2026-02-10T09:30:00')),
            'Роман Киселёв': Client(name='Роман Киселёв', phone='79132224455', client_type='retail', address='Барнаул, Георгиева 23', source='Telegram', category='Частник', notes='Нужен самовывоз', created_at=dt('2026-02-16T09:00:00')),
        }
        session.add_all(clients.values())
        session.flush()

        order_rows = [
            {
                'created_at': '2025-10-25T10:30:00',
                'kind': 'retail',
                'status': 'done',
                'client': 'Никита Соколов',
                'payment_method': 'cash_us',
                'delivery_type': 'pickup',
                'delivery_cost': '0',
                'additional_costs': '0',
                'notes': 'Самовывоз со склада, быстрое закрытие',
                'supplier': None,
                'driver': None,
                'use_supplier_balance': False,
                'document_issued': False,
                'document_name': '',
                'pricing_tier': 'retail',
                'items': [
                    ('Цемент М500 50кг', '20', None),
                    ('Пароизоляция 70м2', '2', None),
                ],
            },
            {
                'created_at': '2025-11-12T13:00:00',
                'kind': 'retail',
                'status': 'delivered',
                'client': 'Алексей Панов',
                'payment_method': 'cash_driver',
                'delivery_type': 'delivery',
                'delivery_cost': '1800',
                'additional_costs': '600',
                'notes': 'Доставка на участок в тот же день',
                'supplier': 'ЛесСнаб',
                'driver': 'Иван Шишкин',
                'use_supplier_balance': False,
                'document_issued': True,
                'document_name': 'Товарный чек',
                'pricing_tier': 'retail',
                'items': [
                    ('Доска обрезная 50x150x6000', '1.5', None),
                    ('OSB-3 9мм', '10', None),
                ],
            },
            {
                'created_at': '2025-11-28T09:40:00',
                'kind': 'wholesale',
                'status': 'done',
                'client': 'ИП Кузнецов',
                'payment_method': 'invoice_no_vat',
                'delivery_type': 'delivery',
                'delivery_cost': '3200',
                'additional_costs': '1500',
                'notes': 'Первый крупный безнал по газоблоку',
                'supplier': 'Газоблок Сибирь',
                'driver': 'Павел Романов',
                'use_supplier_balance': True,
                'document_issued': True,
                'document_name': 'Счёт + УПД',
                'pricing_tier': 'small_opt_non_cash',
                'items': [
                    ('Газоблок D500 600x300x200', '480', None),
                    ('Клей для газоблока 25кг', '40', None),
                ],
            },
            {
                'created_at': '2025-12-10T15:20:00',
                'kind': 'wholesale',
                'status': 'in_work',
                'client': 'ООО АлтайФасад',
                'payment_method': 'transfer_us',
                'delivery_type': 'delivery',
                'delivery_cost': '5000',
                'additional_costs': '2200',
                'notes': 'Отгрузка частями, ждут второй рейс',
                'supplier': 'МеталлТорг',
                'driver': 'Павел Романов',
                'use_supplier_balance': True,
                'document_issued': True,
                'document_name': 'Счёт + накладная',
                'pricing_tier': 'medium_opt_non_cash',
                'items': [
                    ('Профлист С8 0.45', '150', None),
                    ('Саморез кровельный 5.5x19', '800', None),
                ],
            },
            {
                'created_at': '2025-12-22T11:05:00',
                'kind': 'retail',
                'status': 'done',
                'client': 'Сергей Громов',
                'payment_method': 'transfer_us',
                'delivery_type': 'pickup',
                'delivery_cost': '0',
                'additional_costs': '250',
                'notes': 'Забрал со второго склада',
                'supplier': None,
                'driver': None,
                'use_supplier_balance': False,
                'document_issued': False,
                'document_name': '',
                'pricing_tier': 'retail',
                'items': [
                    ('Минвата 50мм', '1', None),
                    ('Пароизоляция 70м2', '2', None),
                ],
            },
            {
                'created_at': '2026-01-09T10:10:00',
                'kind': 'wholesale',
                'status': 'delivered',
                'client': 'База Север',
                'payment_method': 'transfer_supplier',
                'delivery_type': 'delivery',
                'delivery_cost': '4200',
                'additional_costs': '1800',
                'notes': 'Оплата прошла напрямую поставщику',
                'supplier': 'ЛесСнаб',
                'driver': 'Олег Ермаков',
                'use_supplier_balance': False,
                'document_issued': True,
                'document_name': 'УПД',
                'pricing_tier': 'large_opt',
                'items': [
                    ('Доска обрезная 50x150x6000', '6', None),
                    ('Брус 100x100x6000', '3', None),
                ],
            },
            {
                'created_at': '2026-01-27T16:15:00',
                'kind': 'retail',
                'status': 'new',
                'client': 'Максим Юдин',
                'payment_method': 'transfer_us',
                'delivery_type': 'delivery',
                'delivery_cost': '1200',
                'additional_costs': '0',
                'notes': 'Ожидает подтверждение утеплителя',
                'supplier': 'ТеплоСтрой',
                'driver': 'Иван Шишкин',
                'use_supplier_balance': False,
                'document_issued': False,
                'document_name': '',
                'pricing_tier': 'retail',
                'items': [
                    ('Минвата 50мм', '2', None),
                    ('Пароизоляция 70м2', '3', None),
                ],
            },
            {
                'created_at': '2026-02-03T14:25:00',
                'kind': 'wholesale',
                'status': 'done',
                'client': 'Прораб Плюс',
                'payment_method': 'small_opt_non_cash',
                'delivery_type': 'pickup',
                'delivery_cost': '0',
                'additional_costs': '950',
                'notes': 'Самовывоз, счёт закрыт',
                'supplier': 'СибЦемент',
                'driver': None,
                'use_supplier_balance': True,
                'document_issued': True,
                'document_name': 'Счёт + ТОРГ-12',
                'pricing_tier': 'small_opt_non_cash',
                'items': [
                    ('Цемент М500 50кг', '120', None),
                    ('Клей для газоблока 25кг', '35', None),
                ],
            },
            {
                'created_at': '2026-02-18T12:40:00',
                'kind': 'retail',
                'status': 'canceled',
                'client': 'Елена Фадеева',
                'payment_method': 'cash_us',
                'delivery_type': 'pickup',
                'delivery_cost': '0',
                'additional_costs': '0',
                'notes': 'Клиент отменил после брони',
                'supplier': None,
                'driver': None,
                'use_supplier_balance': False,
                'document_issued': False,
                'document_name': '',
                'pricing_tier': 'retail',
                'items': [
                    ('OSB-3 9мм', '5', None),
                ],
            },
            {
                'created_at': '2026-03-02T09:50:00',
                'kind': 'wholesale',
                'status': 'done',
                'client': 'ООО Монолит',
                'payment_method': 'invoice_no_vat',
                'delivery_type': 'delivery',
                'delivery_cost': '6100',
                'additional_costs': '2750',
                'notes': 'Арматура + цемент на плиту',
                'supplier': 'МеталлТорг',
                'driver': 'Олег Ермаков',
                'use_supplier_balance': True,
                'document_issued': True,
                'document_name': 'Счёт + УПД',
                'pricing_tier': 'large_opt_non_cash',
                'items': [
                    ('Арматура 12мм', '2.2', None),
                    ('Цемент М500 50кг', '180', None),
                ],
            },
            {
                'created_at': '2026-03-15T13:30:00',
                'kind': 'retail',
                'status': 'in_work',
                'client': 'Роман Киселёв',
                'payment_method': 'cash_us',
                'delivery_type': 'pickup',
                'delivery_cost': '0',
                'additional_costs': '0',
                'notes': 'Бронь на сегодня до вечера',
                'supplier': None,
                'driver': None,
                'use_supplier_balance': False,
                'document_issued': False,
                'document_name': '',
                'pricing_tier': 'retail',
                'items': [
                    ('Кирпич облицовочный', '350', None),
                    ('Цемент М500 50кг', '15', None),
                ],
            },
            {
                'created_at': '2026-03-27T11:45:00',
                'kind': 'retail',
                'status': 'new',
                'client': 'Никита Соколов',
                'payment_method': 'transfer_us',
                'delivery_type': 'delivery',
                'delivery_cost': '1500',
                'additional_costs': '400',
                'notes': 'Повторный заказ на кровлю',
                'supplier': 'МеталлТорг',
                'driver': 'Иван Шишкин',
                'use_supplier_balance': False,
                'document_issued': True,
                'document_name': 'Накладная',
                'pricing_tier': 'retail',
                'items': [
                    ('Профлист С8 0.45', '32', None),
                    ('Саморез кровельный 5.5x19', '300', None),
                ],
            },
        ]

        # normalize one accidental legacy value to a valid payment method used in the project
        for row in order_rows:
            if row['payment_method'] == 'small_opt_non_cash':
                row['payment_method'] = 'invoice_no_vat'

        for row in order_rows:
            client = clients[row['client']]
            supplier = suppliers.get(row['supplier']) if row['supplier'] else None
            driver = drivers.get(row['driver']) if row['driver'] else None
            order = Order(
                kind=row['kind'],
                status=row['status'],
                payment_method=row['payment_method'],
                delivery_type=row['delivery_type'],
                delivery_cost=dec(row['delivery_cost']),
                additional_costs=dec(row['additional_costs']),
                use_supplier_balance=bool(row['use_supplier_balance']),
                notes=row['notes'],
                client=client,
                supplier=supplier,
                driver=driver,
                client_source_snapshot=client.source,
                document_issued=bool(row['document_issued']),
                document_name=row['document_name'] or None,
                created_at=dt(row['created_at']),
            )
            session.add(order)
            session.flush()

            for product_name, quantity, explicit_price in row['items']:
                product = products[product_name]
                qty = dec(quantity)
                sale_price = dec(explicit_price) if explicit_price is not None else product_price_for_tier(product, row['pricing_tier'])
                item = OrderItem(
                    order=order,
                    product=product,
                    quantity=qty,
                    pricing_tier=row['pricing_tier'],
                    purchase_price=dec(product.purchase_price),
                    sale_price=dec(sale_price),
                    line_purchase_total=(qty * dec(product.purchase_price)).quantize(Decimal('0.01')),
                    line_sale_total=(qty * dec(sale_price)).quantize(Decimal('0.01')),
                )
                session.add(item)

            session.flush()
            recalculate_order(order)

            if order.use_supplier_balance and supplier is not None:
                delta = -dec(order.total_purchase)
                supplier.balance = dec(supplier.balance or 0) + delta
                session.add(
                    SupplierBalanceMovement(
                        supplier=supplier,
                        amount=delta,
                        reason=f'Списание по заказу #{order.id}',
                        created_at=order.created_at,
                    )
                )

            if order.payment_method == 'cash_driver' and driver is not None:
                delta = dec(order.total_revenue)
                driver.cash_on_hand = dec(driver.cash_on_hand or 0) + delta
                session.add(
                    DriverCashMovement(
                        driver=driver,
                        amount=delta,
                        reason=f'Оплата по заказу #{order.id}',
                        created_at=order.created_at,
                    )
                )

        general_expenses = [
            ('Офис', '25000', 'Аренда и коммунальные за март', '2026-03-01T10:00:00'),
            ('Авито', '12000', 'Платные размещения и продвижение', '2026-03-03T10:30:00'),
            ('Зарплата', '40000', 'Частичная выплата менеджеру и складу', '2026-03-10T17:00:00'),
            ('Реклама', '8500', 'Ретаргет и объявления', '2026-03-14T12:30:00'),
            ('Прочее', '6300', 'Хозрасходы и связь', '2026-03-20T15:20:00'),
        ]
        for category, amount, note, created_at in general_expenses:
            session.add(
                GeneralExpense(
                    category=category,
                    amount=dec(amount),
                    note=note,
                    created_at=dt(created_at),
                )
            )

        session.add(
            DriverCashMovement(
                driver=drivers['Иван Шишкин'],
                amount=dec('-5000'),
                reason='Сдал часть денег в кассу',
                created_at=dt('2026-03-29T18:00:00'),
            )
        )
        drivers['Иван Шишкин'].cash_on_hand = dec(drivers['Иван Шишкин'].cash_on_hand) + dec('-5000')

        session.add(
            SupplierBalanceMovement(
                supplier=suppliers['МеталлТорг'],
                amount=dec('20000'),
                reason='Пополнение баланса перед новым завозом',
                created_at=dt('2026-03-25T10:00:00'),
            )
        )
        suppliers['МеталлТорг'].balance = dec(suppliers['МеталлТорг'].balance) + dec('20000')

        session.commit()
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    targets = [ROOT / 'buildcrm.db', ROOT / 'buildcrm_ready.db', ROOT / 'buildcrm_demo.db']
    for target in targets:
        seed_database(target)
        print(f'Seeded: {target.name}')
