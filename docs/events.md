# Events

## PaymentInitiated

Публикует: Wallet Service (после резервирования средств)

| Поле | Тип | Описание |
|------|-----|----------|
| paymentId | string | ID платежа |
| walletId | string | ID кошелька |
| userId | string | ID пользователя |
| amount | number | Сумма в минимальных единицах |
| currency | string | Код валюты |
| recipient | object | Данные получателя |
| recipient.accountNumber | string | Номер счёта |
| recipient.bankBic | string | БИК банка |
| recipient.name | string | ФИО получателя |
| createdAt | string | Время создания |

## PaymentCompleted

Публикует: Payment Service (после успешного callback)

| Поле | Тип | Описание |
|------|-----|----------|
| paymentId | string | ID платежа |
| providerTxnId | string | ID транзакции от провайдера |
| completedAt | string | Время завершения |

## PaymentFailed

Публикует: Payment Service (после неуспешного callback или таймаута)

| Поле | Тип | Описание |
|------|-----|----------|
| paymentId | string | ID платежа |
| providerTxnId | string | ID транзакции (null при timeout) |
| errorCode | string | Код ошибки |
| completedAt | string | Время завершения |

## ProviderCallbackReceived

Публикует: Callback Service (после получения callback)

| Поле | Тип | Описание |
|------|-----|----------|
| providerTxnId | string | ID транзакции от провайдера |
| status | string | SUCCESS, FAILED |
| receivedAt | string | Время получения |
