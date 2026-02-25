# Ubuntu Desktop и безопасный удалённый рабочий стол на сервере

Чтобы потыкать собранный браузер без установки локально: ставим на сервер графический рабочий стол и поднимаем удалённый доступ (с шифрованием).

**Пароль для RDP:** при входе по RDP используются логин и пароль **пользователя Linux** (того, под кем заходишь по SSH). Отдельного «пароля RDP» нет. Надёжный пароль задаётся так:
```bash
passwd          # для текущего пользователя (ubuntu)
# или
sudo passwd ubuntu   # задать пароль пользователю ubuntu
```
Рекомендуется пароль не короче 12 символов, с буквами, цифрами и символами.

## Варианты

| Вариант | Плюсы | Минусы |
|--------|--------|--------|
| **A. xrdp + TLS** | Обычный RDP (Windows/macOS/Linux клиент), один порт, шифрование | Нужен сертификат, порт 3389 наружу (ограничить firewall) |
| **B. VNC по SSH-туннелю** | Не открываем VNC наружу, всё идёт по SSH | Нужно каждый раз поднимать туннель и подключаться к localhost |
| **C. Apache Guacamole** | Доступ из браузера, 2FA, один вход для нескольких машин | Сложнее установка (Java, guacd, nginx) |

Ниже — **вариант A (xrdp + TLS)** как основной и **B (VNC + SSH)** как самый безопасный без доп. портов.

---

## Вариант A: Ubuntu Desktop + xrdp с TLS

### 1. Установка десктопа (один из вариантов)

**Лёгкий (Xfce, меньше RAM):**
```bash
sudo apt update
sudo apt install -y xfce4 xfce4-goodies xfce4-terminal
# Опционально тема «как Ubuntu»:
# sudo apt install -y greybird-gtk-theme
```

**Полный Ubuntu Desktop (GNOME):**
```bash
sudo apt update
sudo apt install -y ubuntu-desktop
# Тяжелее (~2+ GB), нужен нормальный объём RAM.
```

### 2. xrdp (RDP-сервер)

```bash
sudo apt install -y xrdp
sudo systemctl enable xrdp
sudo systemctl start xrdp
```

По умолчанию xrdp слушает порт **3389/tcp**.

### 3. TLS для xrdp (безопасный канал)

Создать каталог и сертификат (self-signed на 1 год):

```bash
sudo mkdir -p /etc/xrdp/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/xrdp/ssl/xrdp.key \
  -out /etc/xrdp/ssl/xrdp.crt \
  -subj "/CN=$(hostname)"
sudo chmod 600 /etc/xrdp/ssl/xrdp.key
sudo chown -R xrdp:xrdp /etc/xrdp/ssl
```

Включить TLS в конфиге:

```bash
sudo sed -i 's/^security_layer=.*/security_layer=tls/' /etc/xrdp/xrdp.ini
sudo sed -i 's/^crypt_level=.*/crypt_level=high/' /etc/xrdp/xrdp.ini
echo -e "\n[tls]\ncertificate=/etc/xrdp/ssl/xrdp.crt\nkey_file=/etc/xrdp/ssl/xrdp.key" | sudo tee -a /etc/xrdp/xrdp.ini
```

Перезапуск:

```bash
sudo systemctl restart xrdp
```

### 4. Сессия для Xfce (если ставили Xfce)

Чтобы при RDP-входе открывался Xfce, а не голый X:

```bash
echo "xfce4-session" | sudo tee /etc/xrdp/startwm.sh
sudo systemctl restart xrdp
```

(Для ubuntu-desktop обычно уже подхватывается GNOME.)

### 5. Файрвол (важно для безопасности)

Не открывать 3389 всему интернету — только своей сети или VPN:

```bash
# Разрешить RDP только с конкретного IP (подставь свой):
sudo ufw allow from YOUR_IP_ADDRESS to any port 3389 proto tcp
sudo ufw enable
# Или только SSH, а RDP туннелить через SSH (см. вариант B).
```

Клиент при первом подключении покажет предупреждение про self-signed сертификат — это нормально, принимаешь и подключаешься.

---

## Вариант B: VNC по SSH-туннелю (без открытия VNC наружу)

Сервер не слушает VNC снаружи — только SSH. Подключаешься по SSH, поднимаешь туннель, входишь в десктоп через localhost.

### 1. Десктоп + VNC-сервер

```bash
sudo apt update
sudo apt install -y xfce4 xfce4-goodies tigervnc-standalone-server
vncpasswd   # задать пароль для VNC (для текущего пользователя)
```

Запуск VNC-сервера (один раз после входа по SSH):

```bash
vncserver :1 -geometry 1920x1080 -depth 24
```

Остановка:

```bash
vncserver -kill :1
```

### 2. Подключение с твоей машины

На **локальной** машине:

```bash
ssh -L 5901:localhost:5901 -N user@SERVER_IP
```

В другом терминале или через VNC-клиент подключаешься к **localhost:5901** (дисплей :1). Весь трафик идёт по SSH — порт 5901 наружу не открыт.

---

## После входа в десктоп

Запуск собранного браузера (подставь свой путь к out и бинарнику):

```bash
/home/ubuntu/knx-west/aib/chromium/src/out/Default_x64/browseros --enable-logging=stderr --user-data-dir=/tmp/browseros-profile
```

Или добавить ярлык на рабочий стол / в меню Xfce/GNOME.

---

## Кратко

- **Красивый GUI на сервере:** `ubuntu-desktop` (GNOME) или `xfce4` + темы.
- **Безопасный удалённый стол:** xrdp с TLS (вариант A) или VNC только по SSH-туннелю (вариант B).
- **Не открывать RDP/VNC всему интернету:** firewall по IP или только SSH + туннель.

Если скажешь, какой вариант выбираешь (A или B) и ставишь Xfce или полный ubuntu-desktop — могу выписать один скрипт под твой выбор (без автоматического запуска, только команды для копирования).
