# Инженерный регламент развертывания UserGate NGFW v7.4.3 на VMware ESXi, сетевой настройки и нагрузочного тестирования (Cisco TRex ASTF)

> **Назначение:** Полное автономное пошаговое инженерное руководство по развертыванию UserGate NGFW v7.4.3 «с нуля» из OVA-пакета на ESXi 7.0, первичному вводу в эксплуатацию, сетевой маршрутизации, тонкой настройке зон/файрвола и проведению нагрузочного тестирования генератором Cisco TRex ASTF.  
> **Дата составления:** 2026-11-05  
> **ОС гипервизора:** VMware ESXi 7.0.1 (Build 17551050), Datastore: `datastore2`  
> **Дистрибутив:** `ngfw-x86-64-7.4.3.549285R-release-public.ova`  
> **Цель:** Обеспечить 100% воспроизводимость стенда и возможность его дублирования/восстановления без внешних ассистентов.  

---

## 📑 Содержание
1. [Паспорт стенда и учетные данные](#1-паспорт-стенда-и-учетные-данные)
2. [Топология и схема подключения портов](#2-топология-и-схема-подключения-портов)
3. [Пошаговое развертывание на VMware ESXi из OVA](#3-пошаговое-развертывание-на-vmware-esxi-из-ova)
4. [Первый запуск и мастер инициализации (RegisterMaster)](#4-первый-запуск-и-мастер-инициализации-registermaster)
5. [Сетевая настройка интерфейсов, маршрутов и зон](#5-сетевая-настройка-интерфейсов-маршрутов-и-зон)
6. [Базовые команды UserGate CLI (SSH)](#6-базовые-команды-usergate-cli-ssh)
7. [Критические инженерные нюансы и «подводные камни»](#7-критические-инженерные-нюансы-и-подводные-камни)
8. [Проведение нагрузочного тестирования на Cisco TRex](#8-проведение-нагрузочного-тестирования-на-cisco-trex)
9. [Сравнительные результаты трех вендоров](#9-сравнительные-результаты-трех-вендоров)

---

## 1. Паспорт стенда и учетные данные

### Все IP-адреса, порты и учетные записи:

| Узел / Сервис | Роль / Назначение | IP-адрес / Порт | Учетные данные |
| :--- | :--- | :--- | :--- |
| **Хост VMware ESXi** | Физический гипервизор | `https://10.15.26.2/` (SSH: 22) | `root` / `skjfhfjJDJRNJRwjd@#$` |
| **Генератор TRex** | Нода трафика Cisco TRex ASTF | `10.15.26.15` (SSH: 22, Web: 8080) | `user` / `xxXX1234`<br>`root` / `xxXX1234` |
| **UserGate: Web UI** | Веб-панель управления NGFW | `https://10.15.26.12:8001/` | **`Admin`** / **`P@ssw0rdP@ssw0rd`** |
| **UserGate: SSH CLI** | Консольный интерфейс администратора | `10.15.26.12:2200` *(порт 2200!)* | **`Admin`** / **`P@ssw0rdP@ssw0rd`** |
| **UserGate: Port 1 (LAN1)** | Входной транзитный порт (клиенты) | `192.168.1.10/24` (Зона: Trusted) | — |
| **UserGate: Port 2 (LAN2)** | Выходной транзитный порт (серверы) | `172.10.1.10/24` (Зона: Untrusted) | — |
| **TRex: Port 0** | Клиентский сегмент (генератор) | `192.168.1.2/24` (эмуляция `16.0.0.0/8`) | — |
| **TRex: Port 1** | Серверный сегмент (ответчик) | `172.10.1.2/24` (эмуляция `48.0.0.0/8`) | — |

---

## 2. Топология и схема подключения портов

```text
[ Генератор Cisco TRex ASTF (10.15.26.15) ]                 [ UserGate NGFW v7.4.3 (10.15.26.12) ]
  Port 0: 192.168.1.2/24                                       Port 1: 192.168.1.10/24
  MAC: 00:0c:29:94:41:c7                                       MAC: 00:0c:29:c5:93:42
  Эмуляция Клиентов: 16.0.0.0/8                                 Зона: Trusted
           |                                                            |
           +===== vSwitch PortGroup: Ideco_Novum_v23_dimitriev-lan1 ====+
           
  Port 1: 172.10.1.2/24                                       Port 2: 172.10.1.10/24
  MAC: 00:0c:29:94:41:d1                                       MAC: 00:0c:29:c5:93:4c
  Эмуляция Серверов: 48.0.0.0/8                                Зона: Untrusted
           |                                                            |
           +===== vSwitch PortGroup: Ideco_Novum_v23_dimitriev-lan2 ====+
```

> [!IMPORTANT]
> **Обязательная настройка vSwitch в ESXi:**  
> Обе порт-группы `Ideco_Novum_v23_dimitriev-lan1` и `Ideco_Novum_v23_dimitriev-lan2` должны иметь в политиках безопасности коммутатора:
> * **Promiscuous Mode:** `Accept`
> * **MAC Address Changes:** `Accept`
> * **Forged Transmits:** `Accept`  
> Без этого TRex не сможет принимать ответы для эмулируемых сетей `16.0.0.0/8` и `48.0.0.0/8`.

---

## 3. Пошаговое развертывание на VMware ESXi из OVA

### Шаг 3.1. Распаковка OVA
Архив OVA является стандартным tar-архивом. Распаковываем его на управляющем Linux-хосте:
```bash
mkdir -p /tmp/usergate_ova
tar -xvf /home/bambycha/Загрузки/ngfw-x86-64-7.4.3.549285R-release-public.ova -C /tmp/usergate_ova/
```
Внутри распакуются:
* `ngfw-x86-64-7.4.3.549285R-release-public-disk-0.vmdk` (~1.4 ГБ, сжатый образ диска ОС на 20 ГБ)
* `ngfw-x86-64-7.4.3.549285R-release-public-disk-1.vmdk` (~512 байт / пустой образ диска логов на 100 ГБ)
* `ngfw-x86-64-7.4.3.549285R-release-public.ovf` (XML-описание)

### Шаг 3.2. Загрузка дисков на Datastore ESXi
Создаем папку на хранилище ESXi и загружаем распакованные файлы через HTTPS:
```bash
# Создание каталога на datastore2
curl -k -u 'root:skjfhfjJDJRNJRwjd@#$' -X MKCOL \
  "https://10.15.26.2/folder/UserGate_NGFW_v7_dimitriev?dcPath=ha-datacenter&dsName=datastore2"

# Загрузка disk-0
curl -k -u 'root:skjfhfjJDJRNJRwjd@#$' --upload-file \
  /tmp/usergate_ova/ngfw-x86-64-7.4.3.549285R-release-public-disk-0.vmdk \
  "https://10.15.26.2/folder/UserGate_NGFW_v7_dimitriev/stream_disk0.vmdk?dcPath=ha-datacenter&dsName=datastore2"

# Загрузка disk-1
curl -k -u 'root:skjfhfjJDJRNJRwjd@#$' --upload-file \
  /tmp/usergate_ova/ngfw-x86-64-7.4.3.549285R-release-public-disk-1.vmdk \
  "https://10.15.26.2/folder/UserGate_NGFW_v7_dimitriev/stream_disk1.vmdk?dcPath=ha-datacenter&dsName=datastore2"
```

### Шаг 3.3. Конвертация stream-дисков в Thin-диски через SSH на ESXi
Образы дисков из OVA имеют тип `streamOptimized` и не могут быть напрямую подключены к запущенной ВМ. Их необходимо конвертировать:
```bash
# Подключаемся по SSH на ESXi (10.15.26.2)
cd "/vmfs/volumes/datastore2/UserGate_NGFW_v7_dimitriev"

# Конвертация системного диска (20 GB)
vmkfstools -i stream_disk0.vmdk disk0.vmdk -d thin

# Конвертация диска базы данных и логов (100 GB)
vmkfstools -i stream_disk1.vmdk disk1.vmdk -d thin

# Удаление временных stream-дисков для освобождения места
rm -f stream_disk0.vmdk stream_disk1.vmdk
```

### Шаг 3.4. Создание файла конфигурации ВМ (.vmx)
Создаем рабочий файл `/vmfs/volumes/datastore2/UserGate_NGFW_v7_dimitriev/UserGate_NGFW_v7_dimitriev.vmx`:
```text
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "18"
vm.createDate = "1730800000"
displayName = "UserGate_NGFW_v7_dimitriev"
guestOS = "other-64"

# Аппаратный паритет (4 vCPU / 16 GB RAM)
numvcpus = "4"
cpuid.coresPerSocket = "4"
memsize = "16384"

# Корневые мосты PCIe (ОБЯЗАТЕЛЬНО для аппаратной версии 18!)
pciBridge0.present = "TRUE"
pciBridge4.present = "TRUE"
pciBridge4.virtualDev = "pcieRootPort"
pciBridge4.functions = "8"
pciBridge5.present = "TRUE"
pciBridge5.virtualDev = "pcieRootPort"
pciBridge5.functions = "8"
pciBridge6.present = "TRUE"
pciBridge6.virtualDev = "pcieRootPort"
pciBridge6.functions = "8"
pciBridge7.present = "TRUE"
pciBridge7.virtualDev = "pcieRootPort"
pciBridge7.functions = "8"

# Дисковый SCSI контроллер LSI Logic
scsi0.present = "TRUE"
scsi0.virtualDev = "lsilogic"

# Системный диск (20 GB)
scsi0:0.present = "TRUE"
scsi0:0.fileName = "disk0.vmdk"
scsi0:0.deviceType = "scsi-hardDisk"

# Диск логов и базы данных (100 GB - ОБЯЗАТЕЛЕН!)
scsi0:1.present = "TRUE"
scsi0:1.fileName = "disk1.vmdk"
scsi0:1.deviceType = "scsi-hardDisk"

# Сетевой интерфейс 0: Сеть управления (DHCP)
ethernet0.present = "TRUE"
ethernet0.virtualDev = "vmxnet3"
ethernet0.networkName = "VM Network"
ethernet0.addressType = "generated"

# Сетевой интерфейс 1: Входной порт LAN1 (Клиент TRex)
ethernet1.present = "TRUE"
ethernet1.virtualDev = "vmxnet3"
ethernet1.networkName = "Ideco_Novum_v23_dimitriev-lan1"
ethernet1.addressType = "generated"

# Сетевой интерфейс 2: Выходной порт LAN2 (Сервер TRex)
ethernet2.present = "TRUE"
ethernet2.virtualDev = "vmxnet3"
ethernet2.networkName = "Ideco_Novum_v23_dimitriev-lan2"
ethernet2.addressType = "generated"

# Сетевой интерфейс 3: Резервный порт DMZ
ethernet3.present = "TRUE"
ethernet3.virtualDev = "vmxnet3"
ethernet3.networkName = "VM Network"
ethernet3.addressType = "generated"

# Системные параметры
powerType.powerOff = "soft"
powerType.powerOn = "soft"
powerType.suspend = "soft"
powerType.reset = "soft"
tools.syncTime = "TRUE"
tools.upgrade.policy = "manual"
```

### Шаг 3.5. Регистрация и запуск виртуальной машины в ESXi
```bash
# Регистрация ВМ на гипервизоре (возвращает VM ID, например 242)
vim-cmd solo/registervm /vmfs/volumes/datastore2/UserGate_NGFW_v7_dimitriev/UserGate_NGFW_v7_dimitriev.vmx

# Включение питания
vim-cmd vmsvc/power.on 242
```

---

## 4. Первый запуск и мастер инициализации (RegisterMaster)

### 4.1. Обход диалогового окна консоли (Whiptail Dialog)
При первой загрузке виртуальная машина останавливается на синем псевдографическом окне:
`Default settings have been restored successfully. <Ok>`.  
Пока не будет нажат `Enter`, операционная система UGOS не запустит сервисы управления!
* **Вариант А (Вручную):** Открыть консоль ВМ в браузере (vSphere Web Client) или через VMRC и нажать клавишу `Enter`.
* **Вариант Б (Скриптом через WebMKS):** Отправить скан-код клавиши `Enter` (`0xff0d`) по протоколу RFB через VNC-сокет тикета ESXi.

После нажатия `Enter` ОС завершает загрузку:
* Hostname: `UGOS`
* Управление: получает адрес по DHCP на `ethernet0` (`10.15.26.12/24`, шлюз `10.15.26.1`).
* Порт веб-интерфейса: **HTTPS 8001** (`https://10.15.26.12:8001/`).
* Порт консоли SSH: **TCP 2200** (`Admin@10.15.26.12:2200`).

### 4.2. Инициализация мастера (Установка пароля администратора)
При первом обращении к `https://10.15.26.12:8001/` открывается мастер `initInstallForm`.

#### Вариант А: Через веб-браузер
1. Открыть в браузере: `https://10.15.26.12:8001/`
2. Выбрать язык: **Русский** или **English**.
3. Часовой пояс: **Europe/Moscow**.
4. Логин администратора: **`Admin`**
5. Пароль: **`P@ssw0rdP@ssw0rd`** (дважды).
6. Нажать **Сохранить** и дождаться инициализации внутренней базы PostgreSQL (~30–45 секунд).

#### Вариант Б: Автоматически через Python / API:
```python
import requests, re, urllib3
urllib3.disable_warnings()

s = requests.Session()
r = s.get('https://10.15.26.12:8001/', verify=False)
csrf = re.search(r"CSRF_TOKEN\s*=\s*'([^']+)'", r.text).group(1)

reg_data = {
    'login': 'Admin',
    'password': 'P@ssw0rdP@ssw0rd',
    'timezone': 'Europe/Moscow',
    'lang': 'en',
    'csrfmiddlewaretoken': csrf
}
resp = s.post('https://10.15.26.12:8001/utm/RegisterMaster', data=reg_data, verify=False)
print("Инициализация завершена:", resp.text)
```

---

## 5. Сетевая настройка интерфейсов, маршрутов и зон

Настройка выполняется либо в Web UI (`https://10.15.26.12:8001`), либо вызовами REST API к контроллерам UserGate:

### 5.1. Назначение IP-адресов интерфейсам
В веб-интерфейсе: **Сеть ➔ Интерфейсы**:
* **`port1`:**
  * Название: `port1`
  * Зона: **`Trusted`** (Зона доверенной сети)
  * Режим: **Статический (Static)**
  * IPv4: **`192.168.1.10/24`**
  * Чекбокс: **Включено (Enabled)**
* **`port2`:**
  * Название: `port2`
  * Зона: **`Untrusted`** (Внешняя зона)
  * Режим: **Статический (Static)**
  * IPv4: **`172.10.1.10/24`**
  * Чекбокс: **Включено (Enabled)**

### 5.2. Настройка виртуального маршрутизатора (Virtual Router)
В веб-интерфейсе: **Сеть ➔ Виртуальные маршрутизаторы ➔ `default` ➔ Маршруты**:
Добавить два статических маршрута (тип Unicast):
1. **Маршрут к клиентам TRex:**
   * Название: `TRex-Clients`
   * Сеть назначения: **`16.0.0.0/8`**
   * Шлюз: **`192.168.1.2`**
   * Интерфейс: **`port1`**
   * Метрика: `10`
2. **Маршрут к серверам TRex:**
   * Название: `TRex-Servers`
   * Сеть назначения: **`48.0.0.0/8`**
   * Шлюз: **`172.10.1.2`**
   * Интерфейс: **`port2`**
   * Метрика: `10`

### 5.3. Политика межсетевого экрана (Firewall Policy)
В веб-интерфейсе: **Политики сети ➔ Межсетевой экран**:
* Создать правило: **`TRex-Allow-All`**
  * Действие: **Разрешить (Accept)**
  * Зона источника: **Любая (Any)**
  * Зона назначения: **Любая (Any)**
  * Сервисы: **Любые (Any)**
  * Позиция: **1 (Самое первое в списке, поверх запрещающих)**
  * Чекбокс: **Включено (Enabled)**

### 5.4. Настройка трансляции адресов (Режим No-NAT)
В веб-интерфейсе: **Политики сети ➔ NAT и маршрутизация**:
* Убедиться, что все правила NAT (`NAT from Trusted to Untrusted` и др.) **отключены (Disabled)**.
* Для синтетического и L7-тестирования TRex генератор требует, чтобы IP-пакеты от пула `16.0.0.0/8` доходили до пула `48.0.0.0/8` без подмены исходного адреса.

---

## 6. Базовые команды UserGate CLI (SSH)

Подключение осуществляется по протоколу SSH на **порт 2200**:
```bash
ssh -p 2200 Admin@10.15.26.12
# Вводим пароль: P@ssw0rdP@ssw0rd
```

После входа отобразится приветствие и командная строка:
```text
UGOS NGFW 7.4.3.549285R
Admin@ratandonahic>
```

### Основные инженерные команды:

```bash
# 1. Просмотр физических и логических интерфейсов
show iface

# 2. Просмотр состояния сетевых адаптеров, IP и зон
show network
# Внимание: вывод длинных списков использует пейджер --more--. 
# Нажимайте [Пробел] для прокрутки или [q] для выхода!

# 3. Проверка доступности соседних узлов (ICMP Ping)
# Синтаксис UserGate: ping host <IP> count <КОЛИЧЕСТВО>
ping host 192.168.1.2 count 4
ping host 172.10.1.2 count 4

# 4. Просмотр таблицы маршрутизации ядра
show route

# 5. Просмотр активных правил файрвола
show firewall

# 6. Просмотр таблицы активных сессий (conntrack)
show session

# 7. Выход из консоли
exit
```

---

## 7. Критические инженерные нюансы и «подводные камни»

### ⚠️ Нюанс 1. Встроенные прозрачные прокси в зонах (Самый коварный баг!)
* **В чем проблема:** По умолчанию в свойствах зон `Trusted` и `Untrusted` активированы внутренние службы UserGate: `http_proxy`, `smtp_proxy`, `pop_proxy` и `response_page` (Captive Portal).  
  При прохождении любого транзитного веб-трафика (порт 80/TCP) UserGate **перехватывает TCP-сессию на свой локальный прокси-демон**, вместо того чтобы смаршрутизировать ее серверу. В итоге TRex получает 450 байт ответа captive-portal вместо полезной нагрузки, а полоса падает до 0.9 Мбит/с.
* **Как исправить:** В меню **Сеть ➔ Зоны ➔ Trusted (и Untrusted) ➔ Контроль доступа**:  
  **Снять галочки со всех сервисов**, оставив включенным ТОЛЬКО сервис **`Ping`**!

### ⚠️ Нюанс 2. Защита от DoS / SYN-Flood на зонах
* **В чем проблема:** В каждой зоне по умолчанию активирован профиль защиты от DoS: порог сброса `drop_threshold` установлен на **6 000 SYN/сек**. При подаче реального стресс-теста (10 000 – 80 000 CPS) UserGate начинает аварийно сбрасывать входящие пакеты SYN.
* **Как исправить:** В свойствах зоны во вкладке **Защита от DoS** отключить флаги `syn`, `udp`, `icmp` либо поднять лимит до 200 000+.

### ⚠️ Нюанс 3. Второй диск (100 GB) строго обязателен!
* **В чем проблема:** Если развернуть ВМ только с системным диском `disk0.vmdk` (20 ГБ), UserGate загрузится, но база данных PostgreSQL для журналов и аналитики не сможет запуститься. В веб-интерфейсе не будут сохраняться некоторые правила и упадут системные логи.
* **Как исправить:** Всегда подключать `scsi0:1` (`disk1.vmdk`) емкостью не менее 100 ГБ (в формате Thin).

### ⚠️ Нюанс 4. Ошибка «No PCIe slot available for Ethernet0»
* **В чем проблема:** В виртуальном железе ESXi версии Hardware 18 при подключении 4 карт `vmxnet3` гипервизор требует явного наличия мостов шины PCI Express.
* **Как исправить:** В файл `.vmx` обязательно должны быть включены строчки `pciBridge4..7` с параметром `virtualDev = "pcieRootPort"`.

---

## 8. Проведение нагрузочного тестирования на Cisco TRex

### 8.1. Переключение шлюза на узле генератора TRex
Подключаемся по SSH на генератор `TRex-Generator-dimitriev` (`10.15.26.15`):
```bash
ssh user@10.15.26.15
# Пароль: xxXX1234
```

Переключаем маршрутизацию портов TRex на адреса UserGate (`192.168.1.10` и `172.10.1.10`):
```bash
echo xxXX1234 | sudo -S bash -c "cat <<EOF > /etc/trex_cfg.yaml
- version: 2
  interfaces: ['03:00.0', '0b:00.0']
  port_info:
      - ip: 192.168.1.2
        default_gw: 192.168.1.10
      - ip: 172.10.1.2
        default_gw: 172.10.1.10

  platform:
      master_thread_id: 0
      latency_thread_id: 1
      dual_if:
        - socket: 0
          threads: [2, 3]
EOF
systemctl restart trex-engine.service
"
```

### 8.2. Запуск тестовых профилей ASTF

```bash
# 1. Запуск базового HTTP теста (mult=100, 15 сек)
python3 ~/ngfw-benchmark-trex/scripts/benchmark_astf.py \
  --server 127.0.0.1 \
  --profile astf/http_simple.py \
  --mult 100 \
  --duration 15 \
  --output ~/http_baseline_ug.json

# 2. Запуск стрессового HTTP CPS теста (mult=300, 15 сек)
python3 ~/ngfw-benchmark-trex/scripts/benchmark_astf.py \
  --server 127.0.0.1 \
  --profile astf/http_simple.py \
  --mult 300 \
  --duration 15 \
  --output ~/http_stress_ug.json

# 3. Запуск эталонного корпоративного профиля Enterprise SFR Mix (mult=50, 15 сек)
python3 ~/ngfw-benchmark-trex/scripts/benchmark_astf.py \
  --server 127.0.0.1 \
  --profile astf/sfr.py \
  --mult 50 \
  --duration 15 \
  --output ~/sfr_50_ug.json
```

---

## 9. Сравнительные результаты трех вендоров

Замеры на идентичных ресурсах (**4 vCPU / 16 GB RAM** на один узел МЭ):

| Профиль нагрузки | Метрика | Ideco Novum v23 | PT NGFW v1.11 | UserGate v7.4.3 | Итог раунда |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Enterprise SFR Mix**<br>`astf/sfr.py` (mult=50)<br>*(Реалистичный офисный микс)* | **Пиковый CPS**<br>**Полоса (RX)**<br>**Активные сессии** | 8 585.5 CPS<br>**933.4 Мбит/с 🏆**<br>103 954 flows | 19 082.1 CPS<br>752.9 Мбит/с<br>187 911 flows | **82 054.0 CPS 🏆**<br>357.8 Мбит/с<br>**262 145 flows 🏆** | **UserGate — рекорд устойчивости (82k CPS / 262k сессий) 🏆**<br>**Ideco — лучшая полезная полоса (933 Мбит/с) 🏆** |
| **HTTP Baseline**<br>`astf/http_simple.py` (mult=100) | **Пиковый CPS**<br>**Полоса (RX)** | 275.2 CPS<br>403.7 Мбит/с | 269.0 CPS<br>**734.6 Мбит/с 🏆** | **277.8 CPS**<br>0.99 Мбит/с | **PT NGFW (+82% скорости) 🏆**<br>Паритет CPS (~275) |
| **HTTP Stress**<br>`astf/http_simple.py` (mult=300) | **Пиковый CPS**<br>**Полоса (RX)** | 827.8 CPS<br>358.9 Мбит/с | 787.9 CPS<br>**1 041.4 Мбит/с 🏆** | **833.6 CPS 🏆**<br>3.58 Мбит/с | **PT NGFW (1.04 Гбит/с) 🏆**<br>**UserGate (833.6 CPS) 🏆** |

---

## 10. Полезные ссылки и расположение файлов стенда

* **Локальный репозиторий проекта:** [`/home/bambycha/ngfw-benchmark-trex`](file:///home/bambycha/ngfw-benchmark-trex)
* **Интерактивный HTML-отчет Chart.js:** [`/home/bambycha/ngfw-benchmark-trex/report/ngfw_comparison_benchmark.html`](file:///home/bambycha/ngfw-benchmark-trex/report/ngfw_comparison_benchmark.html)
* **Каталог заметок в Obsidian/Notes:** [`/home/bambycha/Документы/notes/20-ngfw-benchmark-ideco-ptngfw-trex/`](file:///home/bambycha/Документы/notes/20-ngfw-benchmark-ideco-ptngfw-trex/)
* **Удаленный репозиторий GitHub:** [https://github.com/bratiska6-pixel/ngfw-benchmark-trex](https://github.com/bratiska6-pixel/ngfw-benchmark-trex)
