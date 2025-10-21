from playwright.sync_api import sync_playwright
import time
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import json

# 設定與共用
base_dir = os.path.dirname(os.path.abspath(__file__))
files_dir = os.path.join(base_dir, "files")
os.makedirs(files_dir, exist_ok=True)
current_time = datetime.today().strftime("%Y%m%d_%H%M%S")

SELECTORS = {
    "address": "div.Io6YTe.fontBodyMedium.kR99db.fdkmkc",
    "average_rating": "div.F7nice span[aria-hidden='true']",
    "review_item": "div[data-review-id]",
    "reviewer": "div.d4r55",
    "comment_rating": "span.kvMYJc",    
    "content_text": "span.wiI7pd",
    "reply_text": "div.wiI7pd",
    "image_button": "button.Tya61d",
}

def log(idx: int | None, msg: str):
    prefix = f"[{idx}] " if idx is not None else ""
    print(prefix + msg)

def load_overview_urls(path: str) -> list[str]:
    urls = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到 {path}，請在與此腳本同目錄放置 store_url.txt")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    if not urls:
        raise ValueError("store_url.txt 內沒有有效的 URL（空行或只有註解）。")
    return urls

def extract_store_name(overview_url: str, idx: int) -> str:
    try:
        store_match = re.search(r"/place/([^/]+)/", overview_url)
        if store_match:
            store_name = store_match.group(1)
            store_name = re.sub(r"%[0-9A-Fa-f]{2}", "_", store_name)  # 移除 URL 編碼片段
            store_name = re.sub(r"[^A-Za-z0-9]+", "_", store_name).strip("_")
        else:
            store_name = f"store_{idx:03d}"
    except Exception:
        store_name = f"store_{idx:03d}"
    return store_name

def parse_coordinates_and_place_id(overview_url: str) -> tuple[str, str, str] | None:
    coord_match = re.search(r'@([-\d\.]+),([-\d\.]+),17z', overview_url)
    if not coord_match:
        return None
    lat, lng = coord_match.groups()

    place_match = re.search(r'!1s([^!]+)', overview_url)
    if not place_match:
        return None
    place_id = place_match.group(1)
    return lat, lng, place_id

def handle_response_factory(review_time_map: dict[str, datetime]):
    # 攔截 listugcposts，取得評論更新時間
    def handle_response(response):
        if "listugcposts" not in response.url:
            return
        try:
            text = response.text()
        except Exception:
            return
        try:
            if text.startswith(")]}'"):
                text = text[4:]
            data = json.loads(text)
            if len(data) > 2:
                for block in data[2]:
                    if not isinstance(block, list):
                        continue
                    for entry in block:
                        if not isinstance(entry, list) or not isinstance(entry[0], str):
                            continue
                        review_id = entry[0]
                        if isinstance(entry[1], list) and len(entry[1]) >= 4:
                            ts_update = entry[1][3]
                            if ts_update:
                                real_time = datetime.fromtimestamp(ts_update / 1_000_000)
                                review_time_map[review_id] = real_time
        except Exception:            
            pass
    return handle_response

def safe_click(page, locator, retries: int = 3, delay: float = 1.0, timeout: float = 5000) -> bool:
    """等待並嘗試點擊元素"""
    for _ in range(retries):
        try:
            locator.wait_for(state="visible", timeout=timeout)
            locator.click()
            return True
        except Exception:
            time.sleep(delay)
    return False

def extract_store_info(page, idx: int) -> tuple[str, str, str]:
    # 地址
    address_text = ""
    try:
        page.wait_for_selector(SELECTORS["address"], timeout=8000)
        el = page.query_selector(SELECTORS["address"])
        address_text = el.inner_text().strip() if el else ""
        log(idx, f"地址文字: {address_text}")
    except Exception as e:
        log(idx, f"地址取得失敗: {e}")

    # 國家（以最後一個逗號分段）
    country = ""
    try:
        if address_text:
            parts = [p.strip() for p in address_text.split(",") if p.strip()]
            if parts:
                country = parts[-1]
        log(idx, f"國家: {country}")
    except Exception as e:
        log(idx, f"country 取得失敗: {e}")

    # 總評分
    average_rating = ""
    try:
        page.wait_for_selector(SELECTORS["average_rating"], timeout=5000)
        el = page.query_selector(SELECTORS["average_rating"])
        average_rating = el.inner_text().strip() if el else ""
        log(idx, f"總評分: {average_rating}")
    except Exception as e:
        log(idx, f"總評分取得失敗: {e}")

    return address_text, country, average_rating

def open_reviews_newest(page, idx: int):
    # 點擊 Reviews 標籤
    try:
        reviews_tab = page.get_by_role("tab", name=re.compile(r"Reviews", re.I)).first
        if not safe_click(page, reviews_tab):
            log(idx, "點擊 Reviews 標籤失敗")
        else:
            page.wait_for_timeout(1000)
            log(idx, "已點擊 Reviews 標籤")
    except Exception as e:
        log(idx, f"點擊 Reviews 標籤失敗: {e}")

    # 開啟排序選單 → 選 Newest
    try:
        sort_btn = page.get_by_text("Sort")
        if safe_click(page, sort_btn):
            page.wait_for_timeout(500)
            newest_btn = page.locator("div[role='menuitemradio']", has_text="Newest")
            safe_click(page, newest_btn)
            page.wait_for_timeout(1000)
        else:
            log(idx, "找不到 Sort 按鈕或點擊失敗")
    except Exception as e:
        log(idx, f"排序選擇失敗: {e}")

def build_review_link(lat: str, lng: str, review_id: str, place_id: str) -> str:
    return (
        f"https://www.google.com/maps/reviews/@{lat},{lng},17z/"
        f"data=!3m1!4b1!4m6!14m5!1m4!2m3!1s{review_id}!2m1!1s{place_id}?entry=ttu"
    )

def parse_comment_rating(raw: str) -> str:
    if raw == "N/A" or not raw:
        return "N/A"
    m = re.search(r"[\d\.]+", raw)
    return m.group() if m else "N/A"

def scrape_reviews(
    page,
    lat: str,
    lng: str,
    place_id: str,
    review_time_map: dict[str, datetime],
    country: str,
    store_name: str,
    average_rating: str,
    idx: int) -> list[dict]:
    seen_ids: set[str] = set()
    all_reviews: list[dict] = []

    stop = False
    same_rounds = 0
    max_rounds = 5

    try:
        page.wait_for_selector(SELECTORS["review_item"], timeout=10000)
    except TimeoutError:
        log(idx, "未載入任何評論區塊，略過")
        return []

    while not stop:
        reviews = page.query_selector_all(SELECTORS["review_item"])
        for r in reviews:
            try:
                review_id = r.get_attribute("data-review-id")
                if not review_id or review_id in seen_ids:
                    continue
                seen_ids.add(review_id)

                # 基本欄位
                poster = r.query_selector(SELECTORS["reviewer"]).inner_text() if r.query_selector(SELECTORS["reviewer"]) else "N/A"
                comment_rating_raw = r.query_selector(SELECTORS["comment_rating"]).get_attribute("aria-label") if r.query_selector(SELECTORS["comment_rating"]) else "N/A"
                comment_rating = parse_comment_rating(comment_rating_raw)                                
                content = r.query_selector(SELECTORS["content_text"]).inner_text() if r.query_selector(SELECTORS["content_text"]) else ""
                reply = r.query_selector(SELECTORS["reply_text"]).inner_text() if r.query_selector(SELECTORS["reply_text"]) else ""

                # 圖片
                images = []
                for btn in r.query_selector_all(SELECTORS["image_button"]):
                    style = btn.get_attribute("style")
                    if style and "url(" in style:
                        url = style.split("url(")[1].split(")")[0].strip("'\"")
                        images.append(url)
                images_url = ", ".join(images) if images else ""

                # 連結與時間
                review_link = build_review_link(lat, lng, review_id, place_id)
                real_time = review_time_map.get(review_id)

                # 一年以前就停止
                if real_time and real_time < datetime.now() - timedelta(days=365):
                    stop = True
                    break

                date_str = real_time.strftime("%Y-%m-%d %H:%M:%S") if real_time else ""

                review_data = {
                    "country": country,
                    "store_name": store_name,
                    "average_rating": average_rating,
                    "link": review_link,
                    "poster": poster,
                    "comment_rating": comment_rating,
                    "date": date_str,
                    "content": content,
                    "images": images_url,
                    "reply": reply
                }

                log(idx, str(review_data))
                all_reviews.append(review_data)

            except Exception as e:
                log(idx, f"略過異常評論: {e}")
                continue

        if stop:
            break

        before = len(seen_ids)
        # 滾到底
        try:
            page.keyboard.down("End")
        except Exception:
            pass
        time.sleep(2)
        after = len(seen_ids)

        same_rounds = same_rounds + 1 if after == before else 0
        if same_rounds >= max_rounds:
            log(idx, "已經滾動至底或無新評論")
            break

    return all_reviews

def save_to_excel(store_name: str, all_reviews: list[dict], output_dir: str, idx: int):
    if not all_reviews:
        log(idx, "此 URL 無評論可輸出")
        return
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", store_name)
    output_file = os.path.join(output_dir, f"{safe_name}_{current_time}.xlsx")
    df = pd.DataFrame(all_reviews)
    # 可依需要固定欄位順序
    cols = ["country", "store_name", "average_rating", "link", "poster", "comment_rating", "date", "content", "images", "reply"]
    df = df[[c for c in cols if c in df.columns]]
    df.fillna("", inplace=True)
    df.to_excel(output_file, index=False, engine="openpyxl")
    log(idx, f"已存成 Excel: {output_file}")

def process_store(p, overview_url: str, idx: int, output_dir: str):
    store_name = extract_store_name(overview_url, idx)
    log(idx, f"處理商家: {store_name}")

    parsed = parse_coordinates_and_place_id(overview_url)
    if not parsed:
        log(idx, f"URL 無法解析座標或 place_id，略過：{overview_url}")
        return
    lat, lng, place_id = parsed

    browser = p.chromium
    page = browser.launch(headless=False).new_page()

    review_time_map: dict[str, datetime] = {}
    page.on("response", handle_response_factory(review_time_map))

    # 進入 Overview
    page.goto(overview_url)
    page.wait_for_load_state("load")
    time.sleep(5)

    # 基本資訊
    _, country, average_rating = extract_store_info(page, idx)

    # Reviews → Newest
    open_reviews_newest(page, idx)

    # 抓評論
    all_reviews = scrape_reviews(
        page=page,
        lat=lat,
        lng=lng,
        place_id=place_id,
        review_time_map=review_time_map,
        country=country,
        store_name=store_name,
        average_rating=average_rating,
        idx=idx
    )

    save_to_excel(store_name, all_reviews, output_dir, idx)

    # 關閉分頁/瀏覽器
    page.context.browser.close()

def main():
    overview_list_path = os.path.join(base_dir, "store_url.txt")
    overview_urls = load_overview_urls(overview_list_path)

    with sync_playwright() as p:
        for idx, overview_url in enumerate(overview_urls, start=1):
            process_store(p, overview_url, idx, files_dir)

    print("所有商家處理完成。")

if __name__ == "__main__":
    main()