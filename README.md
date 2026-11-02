# 🛡️ Cisco TRex NGFW Benchmark & Testing Methodology

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Ubuntu%20%7C%20VMware%20ESXi%20%7C%20Proxmox-orange.svg)]()
[![Generator](https://img.shields.io/badge/Traffic%20Engine-Cisco%20TRex%20v3.08%20(ASTF)-green.svg)]()
[![Methodology](https://img.shields.io/badge/Testing-Stateful%20L7%20(No--NAT)-purple.svg)]()
[![Report](https://img.shields.io/badge/Report-Interactive%20HTML%20(Chart.js)-red.svg)](report/ngfw_comparison_benchmark.html)

> 🤖 **Дисклеймер:** Данный проект, архитектура решения, методика испытаний, скрипты автоматизации и комплект документации разработаны и сформированы с помощью искусственного интеллекта (AI Assistant).

> **Открытая универсальная методика, набор скриптов автоматизации и эталонный сравнительный отчет** для проведения независимого нагрузочного тестирования **любых межсетевых экранов нового поколения (NGFW)** с помощью генератора трафика **Cisco TRex ASTF** (Advanced Stateful Traffic Generator).  
> Подходит для тестирования любых решений: Ideco NGFW, Positive Technologies PT NGFW, UserGate, Континент 4, ViPNet xFW, Check Point, Fortinet, Palo Alto Networks, pfSense/OPNsense и др.

---

## 🎯 Возможности и назначение репозитория

* **100% честное тестирование (Stateful L7):** В отличие от синтетического Stateless-трафика (спам пакетами UDP), используется режим **Cisco TRex ASTF** с полной эмуляцией клиент-серверного диалога: трехстороннее TCP-рукопожатие, L7-заголовки (HTTP/TLS/DNS/SMTP), корректное закрытие сессий.
* **Реалистичный профиль нагрузки Enterprise Mix (SFR):** Имитация типового офисного рабочего дня с одновременным трафиком веба, почты, передачи крупных файлов и DNS-запросов.
* **Готовый интерактивный HTML-отчет для заказчиков:** Автономный презентационный отчет с интерактивными графиками **Chart.js**, таблицами замеров и рекомендациями по сайзингу.
* **Два режима работы:** Подробные руководства, как проводить тестирование **с помощью автономного ИИ-агента** и **вручную (без ИИ)** через веб-панель **TRex Studio** или CLI.
* **Руководство «для чайников»:** Простое объяснение каждой метрики (CPS, Throughput RX/TX, Active Flows, Conntrack, DPDK) на понятных жизненных аналогиях.

---

## 📊 Результаты эталонного тестирования (Case Study: Ideco vs PT NGFW)

Сравнительный тест двух ведущих российских NGFW на абсолютно равных аппаратных ресурсах (**4 vCPU / 16 GB RAM** на один узел):

```text
+-----------------------------------------------------------------------------------------+
| Сценарий нагрузки                   | Ideco NGFW Novum v23   | PT NGFW Node 1           |
+-------------------------------------+------------------------+--------------------------+
| Enterprise SFR Mix Throughput (RX)  | 933.4 Мбит/с 🏆        | 752.8 Мбит/с (-24%)      |
| HTTP Baseline Throughput (RX)       | 403.7 Мбит/с           | 734.6 Мбит/с (+82%)      |
| HTTP Stress Throughput (RX)         | 358.9 Мбит/с           | 1 041.4 Мбит/с (+190%)   |
| Enterprise SFR Mix CPS (Сессий/сек) | 8 585.5 CPS            | 19 082.1 CPS (+122%)     |
| Простота развертывания              | 1 ВМ «All-in-One»      | 2+ ВМ (MGMT + Node)      |
| Встроенные дашборды                 | Из коробки             | Требует Grafana/ClickHouse|
+-----------------------------------------------------------------------------------------+
```

### Ключевые выводы:
1. 🏆 **Ideco NGFW — лидер в реальном корпоративном трафике (933.4 Мбит/с):** Отличная буферизация TCP-окна ядром Linux на передаче объемных данных и непревзойденная скорость развертывания (монолит «Все-в-одном» за 15 минут со всеми встроенными дашбордами).
2. ⚡ **PT NGFW — лидер в стрессовом шторме сессий (19 000+ CPS):** Архитектура **DPDK User-space** позволяет преодолевать гигабитный барьер на коротких транзакциях, но требует многонодового развертывания (отдельная ВМ управления) и внешней системы визуализации (Grafana).

---

## 🏛 Топология тестового стенда

Тестирование осуществляется по схеме «Генератор (Клиенты) ➔ Целевой МЭ ➔ Генератор (Серверы)»:

```text
[ Генератор Cisco TRex ASTF ]                        [ Любой тестируемый NGFW / DUT ]
  Port 0 (192.168.1.2)  ====== LAN: 192.168.1.1 ======>  [ Входной порт LAN ]
  (Клиенты 16.0.0.0/8)                                         |
                                                         [ Модули инспекции: ]
                                                         [ L4 Firewall / DPI ]
                                                         [ IPS / No-NAT      ]
                                                               |
  Port 1 (172.10.1.2)   <===== WAN: 172.10.1.1 =======   [ Выходной порт WAN ]
  (Серверы 48.0.0.0/8)
```

### Основные настройки на любом МЭ:
1. **Маршрутизация:** Сеть `16.0.0.0/8` через `192.168.1.2`, сеть `48.0.0.0/8` через `172.10.1.2`.
2. **Правило No-NAT:** Исключить подсети TRex из трансляции SNAT/маскарадинга.
3. **Firewall Policy:** Разрешающее правило LAN ➔ WAN.

---

## 📂 Структура документации в каталоге `docs/`

| Документ | Назначение |
|---|---|
| [**00-chajnik-guide-kak-chitat-metriki.md**](docs/00-rukovodstvo-dlya-chajnikov-kak-chitat-metriki.md) | **💡 Руководство «для чайников»:** Простое объяснение на понятных аналогиях параметров CPS, Throughput, Active Flows, разницы архитектур и шпаргалка для заказчиков. |
| [**01-arkhitektura-stenda-i-setevaya-skhema.md**](docs/01-arkhitektura-stenda-i-setevaya-skhema.md) | **Архитектура стенда:** Паритет аппаратных ресурсов, VLAN, L2-сегменты, Promiscuous Mode и IP-план. |
| [**02-metodologiya-i-avtomatizaciya-testirovaniya.md**](docs/02-metodologiya-i-avtomatizaciya-testirovaniya.md) | **Методология ASTF:** Описание профилей `http_simple` и `sfr.py`, механизм динамического переключения шлюзов. |
| [**03-sravnitelnye-rezultaty-i-analiz.md**](docs/03-sravnitelnye-rezultaty-i-analiz.md) | **Сравнительный анализ:** Таблицы замеров, архитектурный разбор DPDK vs Linux Kernel Conntrack, рекомендации по сайзингу. |
| [**04-instruktsiya-po-povtornomu-zapusku.md**](docs/04-instruktsiya-po-povtornomu-zapusku.md) | **Инструкция по запуску:** Пошаговое руководство по консольному запуску через CLI и `trex-console`. |
| [**05-ruchnoe-testirovanie-trex-studio-universalnoe.md**](docs/05-ruchnoe-testirovanie-trex-studio-universalnoe.md) | **Ручное тестирование любого МЭ:** Пошаговый алгоритм работы через веб-панель TRex Studio (ARP, профили, ступенчатый стресс, DPI-конструктор). |
| [**06-testirovanie-s-pomoshchyu-ai-i-bez-ai.md**](docs/06-testirovanie-s-pomoshchyu-ai-i-bez-ai.md) | **Тестирование с ИИ и Без ИИ:** Как настроить автономное тестирование через AI-агента и как выполнить полный цикл вручную. |

---

## 🚀 Быстрый старт: Автоматизированный запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/bratiska6-pixel/ngfw-benchmark-trex.git
cd ngfw-benchmark-trex
```

### 2. Запуск нагрузочного теста (Python ASTF)
```bash
# Запуск базового теста HTTP (mult=100, 15 сек)
python3 scripts/benchmark_astf.py \
    --server 127.0.0.1 \
    --profile astf/http_simple.py \
    --mult 100 \
    --duration 15 \
    --output report/result_http100.json
```

### 3. Динамическое переключение шлюза на другой NGFW
```bash
# Переключение шлюзов по умолчанию в /etc/trex_cfg.yaml и рестарт службы
sudo ./scripts/switch_gateway.sh 192.168.1.5 172.10.1.5
```

### 4. Просмотр готового интерактивного отчета
Откройте файл в любом браузере:
[`report/ngfw_comparison_benchmark.html`](report/ngfw_comparison_benchmark.html)

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [Apache 2.0](LICENSE).
Вы можете свободно использовать, модифицировать и внедрять данную методику в своих проектах и на стендах демонстраций заказчикам.
