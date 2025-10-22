# | **Google Maps Review Crawler**<br>

An automated Google Maps review crawler developed with Python 3.13 + Playwright.<br>
It automatically extracts business information, the latest reviews, ratings, images, and owner replies,<br>
then exports the collected data into an Excel file for easy analysis and organization.<br>

## | **Features**<br>

1. Automatically opens each business page on Google Maps<br>
2. Extracts address, country, and average rating<br>
3. Collects reviews sorted by **“Newest”**, including:<br>
   · Reviewer name<br>
   · Rating (numeric only)<br>
   · Review content<br>
   · Business reply (if available)<br>
   · Review image URLs<br>
   · Review date<br>
4. Automatically exports results to an **Excel (.xlsx)** file<br>

*Automatically stops at reviews older than one year to avoid duplicates and unnecessary data.*<br>
![example1](image/google_map.png)<br>
![example2](image/google_comment.png)<br>
## | **Package Installation**<br>

`pip install -r requirements.txt`<br>

## | **Target Business Configuration**<br>

Please paste the Google Maps link of the business you want to scrape reviews from into **store_url**.<br>

## | **Output File**<br>
![example4](image/output_file_content.png)<br>
<br><br>
# | **Google Maps 評論爬蟲**<br>

以 Python 3.13 + Playwright 開發的自動化 Google Maps 評論爬蟲工具。<br>
可自動擷取店家資訊、最新評論、星等、圖片、商家回覆等資料，<br>
並將結果輸出為 Excel 檔案，方便後續分析與整理。<br>

## | **功能特色**<br>

1. 自動開啟 Google Maps 各店家頁面<br>
2. 擷取地址、國家、平均評分<br>
3. 收集「最新排序」評論，包含：<br>
  · 評論者名稱<br>
  · 星等（純數字）<br>
  · 評論內容<br>
  · 店家回覆（若有）<br>
  · 評論圖片連結<br>
  · 評論時間<br>
4. 結果自動輸出至 Excel (.xlsx)<br>

*自動停止在一年以前的評論，避免重複與冗長資料*<br>
![example1](image/google_map.png)<br>
![example2](image/google_comment.png)<br>
## | **套件安裝**<br>

`pip install -r requirements.txt`<br>

## | **目標商家設定**<br>

請至 strore_url 貼上想要爬取評論的商家 Google Map 連結

## | **輸出檔案**<br>

![example4](image/output_file_content.png)<br>
