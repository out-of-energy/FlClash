import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
import yfinance as yf
import schedule
import time

# ---------------------- 用户可配置区域 ----------------------
# 股票代码 (Yahoo Finance 格式) -> (低估区下沿, 上沿)
THRESHOLDS = {
    '002352.SZ': (38.0, 42.0),   # 顺丰控股
    '600600.SS': (88.0, 95.0),   # 青岛啤酒
}

EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_USER = "your_email@example.com"  # 发件人
EMAIL_PASS = "your_smtp_password"       # SMTP 授权码
RECIPIENT   = "dest@example.com"         # 收件人

# ---------------------- 逻辑实现 ---------------------------

def fetch_latest_price(ticker: str) -> float:
    """获取最新收盘价 (若当天未收盘则取上一交易日)."""
    data = yf.Ticker(ticker)
    hist = data.history(period="2d")
    if hist.empty:
        raise ValueError(f"No data for {ticker}")
    return float(hist["Close"].iloc[-1])


def analyse() -> str:
    """分析两只股票是否在买入区间，返回邮件正文."""
    lines = [f"实时检测时间: {datetime.now():%Y-%m-%d %H:%M:%S}\n"]
    for tick, (low, high) in THRESHOLDS.items():
        try:
            price = fetch_latest_price(tick)
            if price < low:
                verdict = "极低估，可分批建仓 ✅"
            elif low <= price <= high:
                verdict = "合理偏低，可考虑买入 ✔️"
            else:
                verdict = "估值中高，暂观望 ⚠️"
            lines.append(f"{tick}: 现价 {price:.2f} 元 | 区间 [{low}-{high}] -> {verdict}")
        except Exception as e:
            lines.append(f"{tick}: 获取数据失败 -> {e}")
    return "\n".join(lines)


def send_email(body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = Header(EMAIL_USER)
    msg["To"] = Header(RECIPIENT)
    msg["Subject"] = Header("每日估值提示 | 顺丰&青岛啤酒", "utf-8")

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, [RECIPIENT], msg.as_string())


def job():
    body = analyse()
    send_email(body)
    print(body)


if __name__ == "__main__":
    # 每个交易日 16:00 运行；如需推送到手机，可在手机端邮件通知或接 webhook
    schedule.every().day.at("16:00").do(job)

    print("[INFO] Stock notifier started …")
    while True:
        schedule.run_pending()
        time.sleep(30)