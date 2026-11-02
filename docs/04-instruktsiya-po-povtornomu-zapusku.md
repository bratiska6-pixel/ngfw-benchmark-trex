# Инструкция по повторному запуску бенчмарка и скрипты стенда

Данный документ содержит пошаговую инструкцию по повторению или модификации нагрузочного тестирования как в автоматическом, так и в ручном режиме.

---

## 1. Автоматический запуск тестирования через TRex

Скрипт бенчмарка находится в каталоге `scripts/benchmark_local.py`. Для его запуска непосредственно на ноде TRex (`<TREX_HOST_IP>`):

```bash
# 1. Подключение к ноде TRex по SSH
ssh user@<TREX_HOST_IP>
# Пароль: <TREX_PASSWORD>

# 2. Проверка статуса службы TRex Engine
sudo systemctl status trex-engine

# 3. Запуск автоматического тестирования
# Скрипт поочередно переключает шлюзы в /etc/trex_cfg.yaml, перезапускает сервис,
# выполняет ARP resolve и прогоняет сценарии для Ideco и PT NGFW
python3 /tmp/benchmark_local.py
```

Результаты тестирования сохраняются в `/tmp/benchmark_results.json`.

---

## 2. Ручной запуск отдельных тестов через интерактивную консоль TRex

Если требуется запустить профиль вручную и визуально наблюдать за параметрами:

```bash
# Запуск интерактивной консоли TRex в режиме ASTF
cd /opt/trex/v3.08
./trex-console --astf
```

Внутри консоли `trex-console`:

```text
# 1. Загрузка профиля и старт с нужным множителем (например, mult=200 на 30 секунд):
astf> start -f astf/http_simple.py -m 200 -d 30

# 2. Мониторинг в реальном времени (графический дашборд):
astf> tui

# 3. Принудительная остановка теста:
astf> stop
```

---

## 3. Переключение шлюза по умолчанию вручную

Если вы хотите вручную направить весь трафик генератора на конкретный NGFW:

### Направить на Ideco NGFW:
Отредактируйте `/etc/trex_cfg.yaml`:
```yaml
  - port_limit: 2
    version: 2
    interfaces: ['03:00.0', '0b:00.0']
    port_bandwidth_gb: 10
    port_info:
      - ip: 192.168.1.2
        default_gw: 192.168.1.1
      - ip: 172.10.1.2
        default_gw: 172.10.1.1
```
Перезапустите сервис:
```bash
sudo systemctl restart trex-engine
```

### Направить на PT NGFW:
Отредактируйте `/etc/trex_cfg.yaml`:
```yaml
  - port_limit: 2
    version: 2
    interfaces: ['03:00.0', '0b:00.0']
    port_bandwidth_gb: 10
    port_info:
      - ip: 192.168.1.2
        default_gw: 192.168.1.5
      - ip: 172.10.1.2
        default_gw: 172.10.1.5
```
Перезапустите сервис:
```bash
sudo systemctl restart trex-engine
```

---

## 4. Скрипты взаимодействия с API NGFW

В подкаталоге `scripts/` сохранены утилиты автоматизации:
* **`scripts/benchmark_local.py`** — Полный цикл нагрузочного тестирования через официальный Python ASTF API TRex.
* **`scripts/ideco_api.py`** — Скрипт авторизации и получения статуса/интерфейсов Ideco NGFW через REST API (`https://<IDECO_IP>:8443`).
* **`scripts/pt_query.py`** — Скрипт проверки состояния ноды PT NGFW (`<PT_NODE_IP>`) и интерфейсов DPDK.
