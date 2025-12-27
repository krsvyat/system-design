# Diagram Style Guide

Правила оформления PlantUML C4 диаграмм.

## 1. Directional Relationships

**Плохо:** `Rel()` — PlantUML сам решает куда вести стрелку

**Хорошо:** Явное направление

```plantuml
Rel_R(a, b, "...")   ' стрелка ВПРАВО
Rel_L(a, b, "...")   ' стрелка ВЛЕВО
Rel_D(a, b, "...")   ' стрелка ВНИЗ
Rel_U(a, b, "...")   ' стрелка ВВЕРХ
```

## 2. Layout Hints

Располагай элементы явно:

```plantuml
Lay_R(serviceA, broker)    ' serviceA слева от broker
Lay_D(broker, consumer)    ' consumer под broker
```

## 3. Arrow Congestion (> 3 стрелок к элементу)

### Упрости labels

| Плохо | Хорошо |
|-------|--------|
| `"PaymentInitiated, PaymentCompleted, PaymentFailed"` | `"Payment events"` |
| `"Sends PaymentCompleted to Kafka"` | `"Events"` |

### Группируй по направлениям

```plantuml
' Publishers слева
Lay_L(producer1, broker)
Lay_L(producer2, broker)

' Consumers справа
Lay_R(broker, consumer1)
Lay_R(broker, consumer2)

' Стрелки идут в одном направлении
Rel_R(producer1, broker, "Events")
Rel_R(producer2, broker, "Events")
Rel_R(broker, consumer1, "Events")
Rel_R(broker, consumer2, "Events")
```

## 4. Группировка по слоям

```
TOP:     User, External clients
         ↓
LAYER 1: Gateway, BFF
         ↓
LAYER 2: Core services (Wallet, Payment, etc.)
         ↓
LAYER 3: Infrastructure (Kafka, Databases)
         ↓
BOTTOM:  External systems
```

## 5. Скрытые связи к БД

Не показывай очевидные связи service → db:

```plantuml
' Вместо Rel_D(service, db, "") используй:
Rel_D(service, db, "", $tags="hidden")
```

Или вообще убери — БД внутри Boundary и так понятно.

## 6. Разделяй диаграммы

Если > 15 контейнеров или > 30 связей:

- **c2-sync.puml** — HTTP/gRPC связи
- **c2-async.puml** — Kafka/events связи

Или:

- **c2-core.puml** — основные сервисы
- **c2-supporting.puml** — вспомогательные (auth, notifications)

## 7. Цвета по типам

```plantuml
' В C4-PlantUML уже есть:
Container()       ' синий
ContainerDb()     ' синий с иконкой БД
ContainerQueue()  ' синий с иконкой очереди
System_Ext()      ' серый

' Для кастомных:
AddElementTag("core", $bgColor="#1168bd")
AddElementTag("supporting", $bgColor="#438dd5")
```

## 8. Не более 7±2 элементов в Boundary

Если больше — разбей на под-boundary или вынеси в отдельную диаграмму.

## 9. Чек-лист перед коммитом

- [ ] Нет пересекающихся стрелок
- [ ] Нет labels которые перекрывают друг друга
- [ ] Используются directional Rel (Rel_R, Rel_L, Rel_D, Rel_U)
- [ ] Layout hints для ключевых элементов
- [ ] Kafka/broker по центру, publishers слева, consumers справа
- [ ] External systems внизу
- [ ] Не более 30 связей на диаграмме
