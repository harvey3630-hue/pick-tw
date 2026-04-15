# momo 聯盟商品管理指南
建立日期：2026-03-22
作者：研究員-sonnet

---

## 一、momo 後台登入資訊

登入資訊存放於：`D:\N8N全自動工作流\momo_config.json`

```json
{
  "account": "F127736309",
  "password": "a127736309",
  "default_limit": 10,
  "sheets_id": "1ZS2mRy1LRQnpJO7YCm04PnMRKmSuCQg8WXIHzwO4-Tc",
  "sheets_tab": "momo聯盟商品"
}
```

- **momo 聯盟後台網址**：https://www.momoshop.com.tw/affiliates/
- **Google SA 憑證**：`D:\N8N全自動工作流\google-credentials.json`

---

## 二、推薦優先推廣的商品類別

根據 Pick-tw 現有文章類別（居家家電、科技工具、金融理財），對應 momo 商品推廣優先度：

| 優先度 | momo 商品類別 | 對應 Pick-tw 類別 | 推廣理由 |
|--------|-------------|-----------------|---------|
| 高 | 空氣清淨機、吸塵器、掃地機器人 | 居家家電 | 客單價高、分潤金額大、有評測需求 |
| 高 | 藍牙耳機、智慧手錶、鍵盤滑鼠 | 科技工具 | Pick-tw 核心讀者群科技取向 |
| 高 | 路由器、NAS、行動電源 | 科技工具 | 高搜尋量、評測文章轉換率佳 |
| 中 | 記憶體、SSD、顯示卡 | 科技工具 | 季節性需求（學生開學、遊戲季）|
| 中 | 廚房家電（氣炸鍋、電鍋） | 居家家電 | 女性讀者擴展、節慶禮品需求 |
| 低 | 保健食品 | 金融理財以外 | 尚無對應文章類別，暫緩 |
| 低 | 服飾配件 | 非核心類別 | Pick-tw 讀者不對齊 |

---

## 三、Playwright 腳本使用方式

### 主腳本位置

```
D:\N8N全自動工作流\momo_affiliate.py
```

### 基本使用（Terminal）

```bash
# 搜尋商品並寫入 Google Sheets
python3 "D:\N8N全自動工作流\momo_affiliate.py" --keyword "空氣清淨機" --limit 10 --headless

# 測試模式（不寫入 Sheets）
python3 "D:\N8N全自動工作流\momo_affiliate.py" --keyword "藍牙耳機" --limit 5 --headless --no-sheets
```

### 參數說明

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--keyword` / `-k` | 搜尋關鍵字 | 必填 |
| `--limit` / `-l` | 最多抓取筆數 | 10 |
| `--headless` | 無頭模式（伺服器必加）| 否 |
| `--no-sheets` | 不寫入 Google Sheets | 否 |

### 常見問題排除

- Python 找不到：改用絕對路徑 `C:\Users\harve\AppData\Local\Programs\Python\Python311\python.exe`
- 中文亂碼：指令前加 `chcp 65001 &&`
- Sheets 寫入失敗：確認 `google-credentials.json` 有效且 SA 有 Sheets 編輯權限

---

## 四、商品管理 Google Sheets 欄位說明

**Sheets ID**：`1ZS2mRy1LRQnpJO7YCm04PnMRKmSuCQg8WXIHzwO4-Tc`
**分頁名稱**：`momo 商品管理`

| 欄位 | 說明 | 填寫範例 |
|------|------|---------|
| A：商品類別 | Pick-tw 對應分類 | 科技工具、居家家電 |
| B：商品名稱 | momo 上的完整商品名稱 | Dyson V15 Detect 吸塵器 |
| C：推廣URL | 帶有 affiliate 追蹤碼的 momo 連結 | https://www.momoshop.com.tw/... |
| D：原價 | 商品未折扣原始售價（NT$）| 28900 |
| E：促銷價 | 目前特價或優惠價（NT$）| 22900 |
| F：分潤比例 | momo 後台顯示的 CPS 百分比 | 3.5% |
| G：優先度 | 高 / 中 / 低 | 高 |
| H：抓取時間 | ISO 8601 格式，腳本自動填入 | 2026-03-22T14:30:00 |

### 注意事項

- 欄位 C（推廣URL）必須使用 momo 後台產生的追蹤連結，不可直接使用商品頁 URL，否則無法計算佣金
- 欄位 F（分潤比例）依商品類別不同，從 1% 到 8% 不等，高單價家電通常在 2-4%
- 欄位 G（優先度）「高」代表應優先寫評測文章或加入 Pick-tw 推薦清單

---

## 五、未來接入 A-flow 的方式（R-flow 同步邏輯）

### 目前架構

```
momo 後台 → Playwright (momo_affiliate.py) → Google Sheets (momo 商品管理)
```

### 目標架構（A-flow 整合）

```
R-flow（定期觸發）→ momo_affiliate.py → Sheets 更新
                                    ↓
                      A-flow 讀取 Sheets → 生成文章草稿
                                    ↓
                      Pick-tw Hugo → 發布文章
```

### 接入步驟

1. **建立 R-flow（定期刷新商品）**
   - N8N Schedule Trigger（每天 09:00）
   - Execute Command 節點呼叫 `momo_affiliate.py --keyword "熱門關鍵字"`
   - 結果寫入 Sheets `momo 商品管理`

2. **A-flow 讀取 Sheets 商品（需修改現有 A-flow）**
   - 在 A-flow 中加入 Google Sheets 讀取節點
   - 篩選條件：優先度 = 高、且抓取時間在最近 7 天內
   - 將商品資料（名稱、原價、促銷價、推廣URL）注入文章生成 prompt

3. **商品文章 prompt 範本**
   ```
   請根據以下 momo 商品資訊，生成一篇 Pick-tw 風格的推薦文章：
   商品名稱：{B欄}
   原價：{D欄}
   促銷價：{E欄}
   推廣連結：{C欄}
   文章類別：{A欄}
   ```

4. **同步頻率建議**
   - 商品資料刷新：每天 1 次（早上）
   - 文章生成：每週 3-5 篇（避免過度發文影響 SEO 品質）

### 短期行動項目

- [ ] 確認 momo_affiliate.py 能成功抓取商品並寫入 Sheets
- [ ] 在 Sheets 新增 `momo 商品管理` 分頁（已由研究員-sonnet 建立）
- [ ] 挑選前 3 個高優先度商品，手動生成測試文章
- [ ] A-flow prompt 加入 momo 商品資料佔位符

---

## 六、快速測試 N8N Webhook

```bash
curl -X POST http://localhost:5678/webhook/momo-affiliate \
  -H "Content-Type: application/json" \
  -d '{"keyword": "空氣清淨機", "limit": 5}'
```

---

*參考：`D:\N8N全自動工作流\momo_webhook_setup.md`（N8N 節點設定說明）*
