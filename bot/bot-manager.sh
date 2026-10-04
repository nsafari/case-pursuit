#!/bin/bash
# اسکریپت مدیریت بازوی بله
# Bale Bot Management Script

# مسیرها
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="bale-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="${BOT_DIR}/logs"
PID_FILE="${BOT_DIR}/bot.pid"
VENV_PYTHON="${BOT_DIR}/.venv/bin/python"

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# تابع نمایش پیام
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# بررسی وجود توکن
check_token() {
    if [ -z "${BALE_BOT_TOKEN}" ]; then
        if [ -f "${BOT_DIR}/.env" ]; then
            source "${BOT_DIR}/.env"
        fi
    fi
    
    if [ -z "${BALE_BOT_TOKEN}" ] || [ "${BALE_BOT_TOKEN}" = "YOUR_TOKEN_HERE" ]; then
        error "توکن بازو تنظیم نشده است!"
        error "لطفاً توکن را در یکی از این مکان‌ها تنظیم کنید:"
        error "  1. متغیر محیطی BALE_BOT_TOKEN"
        error "  2. فایل ${BOT_DIR}/.env"
        error "  3. فایل ${BOT_DIR}/config.py"
        return 1
    fi
    return 0
}

# نصب سرویس
install_service() {
    log "نصب سرویس ${SERVICE_NAME}..."
    
    # بررسی دسترسی root
    if [ "$EUID" -ne 0 ]; then
        error "این دستور نیاز به دسترسی root دارد"
        error "لطفاً با sudo اجرا کنید: sudo $0 install"
        return 1
    fi
    
    # ایجاد پوشه لاگ
    mkdir -p "${LOG_DIR}"
    
    # کپی فایل سرویس
    cp "${BOT_DIR}/bale-bot.service" "${SERVICE_FILE}"
    
    # بازنویسی مسیرها در فایل سرویس
    sed -i "s|YOUR_TOKEN_HERE|${BALE_BOT_TOKEN}|g" "${SERVICE_FILE}"
    
    # فعال‌سازی سرویس
    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}"
    
    log "سرویس با موفقیت نصب شد!"
    log "برای شروع: sudo systemctl start ${SERVICE_NAME}"
    log "برای مشاهده وضعیت: sudo systemctl status ${SERVICE_NAME}"
}

# حذف سرویس
uninstall_service() {
    log "حذف سرویس ${SERVICE_NAME}..."
    
    if [ "$EUID" -ne 0 ]; then
        error "این دستور نیاز به دسترسی root دارد"
        error "لطفاً با sudo اجرا کنید: sudo $0 uninstall"
        return 1
    fi
    
    systemctl stop "${SERVICE_NAME}" 2>/dev/null
    systemctl disable "${SERVICE_NAME}" 2>/dev/null
    rm -f "${SERVICE_FILE}"
    systemctl daemon-reload
    
    log "سرویس با موفقیت حذف شد!"
}

# شروع سرویس
start_service() {
    log "شروع سرویس ${SERVICE_NAME}..."
    
    if [ "$EUID" -eq 0 ]; then
        systemctl start "${SERVICE_NAME}"
    else
        sudo systemctl start "${SERVICE_NAME}"
    fi
    
    sleep 2
    status_service
}

# توقف سرویس
stop_service() {
    log "توقف سرویس ${SERVICE_NAME}..."
    
    if [ "$EUID" -eq 0 ]; then
        systemctl stop "${SERVICE_NAME}"
    else
        sudo systemctl stop "${SERVICE_NAME}"
    fi
    
    log "سرویس متوقف شد."
}

# ری‌استارت سرویس
restart_service() {
    log "ری‌استارت سرویس ${SERVICE_NAME}..."
    
    if [ "$EUID" -eq 0 ]; then
        systemctl restart "${SERVICE_NAME}"
    else
        sudo systemctl restart "${SERVICE_NAME}"
    fi
    
    sleep 2
    status_service
}

# نمایش وضعیت سرویس
status_service() {
    log "وضعیت سرویس ${SERVICE_NAME}:"
    echo ""
    
    if [ "$EUID" -eq 0 ]; then
        systemctl status "${SERVICE_NAME}" --no-pager
    else
        sudo systemctl status "${SERVICE_NAME}" --no-pager
    fi
}

# نمایش لاگ‌ها
show_logs() {
    log "نمایش ۵۰ خط آخر لاگ بازو:"
    echo ""
    
    if [ -f "${LOG_DIR}/bot.log" ]; then
        tail -n 50 "${LOG_DIR}/bot.log"
    else
        error "فایل لاگ یافت نشد: ${LOG_DIR}/bot.log"
    fi
}

# اجرای مستقیم (بدون سرویس)
run_direct() {
    log "اجرای مستقیم بازو (برای تست)..."
    warn "برای اجرای دائمی از سرویس systemd استفاده کنید"
    
    check_token || return 1
    
    cd "${BOT_DIR}"
    
    if [ ! -f "${VENV_PYTHON}" ]; then
        error "محیط مجازی یافت نشد: ${VENV_PYTHON}"
        error "لطفاً ابتدا محیط مجازی را ایجاد کنید:"
        error "  cd ${BOT_DIR}"
        error "  python3 -m venv .venv"
        error "  .venv/bin/pip install -r requirements.txt"
        return 1
    fi
    
    BALE_BOT_TOKEN="${BALE_BOT_TOKEN}" "${VENV_PYTHON}" bot.py
}

# نمایش راهنما
show_help() {
    echo "=== اسکریپت مدیریت بازوی بله ==="
    echo ""
    echo "استفاده: $0 {install|uninstall|start|stop|restart|status|logs|run|help}"
    echo ""
    echo "دستورات:"
    echo "  install    - نصب سرویس systemd"
    echo "  uninstall  - حذف سرویس systemd"
    echo "  start      - شروع سرویس"
    echo "  stop       - توقف سرویس"
    echo "  restart    - ری‌استارت سرویس"
    echo "  status     - نمایش وضعیت سرویس"
    echo "  logs       - نمایش لاگ‌ها"
    echo "  run        - اجرای مستقیم (برای تست)"
    echo "  help       - نمایش این راهنما"
    echo ""
    echo "نکته: برای نصب و حذف سرویس به دسترسی root نیاز است"
}

# بررسی اولیه
check_token || exit 1

# پردازش دستور
case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs
        ;;
    run)
        run_direct
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
