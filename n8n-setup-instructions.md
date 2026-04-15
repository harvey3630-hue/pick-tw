# Pick-TW N8N 完整建置指令
# 給小幫手（Claude Code）執行

## 說明
這份文件包含建立 pick-tw.com 全自動化系統的完整指令。
請先確認 credentials.json 已填入所有 API Key，再開始執行。

---

## 執行前確認清單
- [ ] credentials.json 所有欄位已填入
- [ ] N8N 已在執行中（http://localhost:5678 可以打開）
- [ ] Docker 正在運行
- [ ] Google Sheets 已建立並共用給服務帳戶

---

## 第一步：讀取設定檔

請讀取以下路徑的設定檔，之後所有步驟都用這裡的值：
```
D:\N8N全自動工作流\credentials.json
```

把所有 API Key 和設定值儲存在變數中，後面會一直用到。

---

## 第二步：設定 N8N 環境變數

在 N8N 的 Docker 容器中設定以下環境變數。

請執行：
```bash
docker stop n8n
docker rm n8n
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=false \
  -e WEBHOOK_URL=http://localhost:5678 \
  -e GENERIC_TIMEZONE=Asia/Taipei \
  -e TZ=Asia/Taipei \
  -v n8n_data:/home/node/.n8n \
  -v "D:\N8N全自動工作流:/home/node/files" \
  n8nio/n8n
```

執行完後確認 http://localhost:5678 可以打開。

---

## 第三步：透過 N8N API 建立所有 Credentials

N8N 啟動後，用以下方式建立 Credentials。

請用 Python 執行以下程式碼（從 credentials.json 讀取值）：

```python
import json
import requests

# 讀取設定
with open(r'D:\N8N全自動工作流\credentials.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

N8N_URL = "http://localhost:5678"
headers = {"Content-Type": "application/json"}

def create_credential(name, cred_type, data):
    payload = {"name": name, "type": cred_type, "data": data}
    r = requests.post(f"{N8N_URL}/api/v1/credentials", 
                     json=payload, headers=headers)
    if r.status_code in [200, 201]:
        print(f"✅ 建立成功：{name}")
        return r.json().get('id')
    else:
        print(f"❌ 建立失敗：{name} - {r.text}")
        return None

# 1. Gemini API
create_credential(
    "Gemini API",
    "googleGeminiApi",
    {"apiKey": config['credentials']['gemini']['api_key']}
)

# 2. Claude API
create_credential(
    "Claude API", 
    "anthropicApi",
    {"apiKey": config['credentials']['claude']['api_key']}
)

# 3. GitHub Token
create_credential(
    "GitHub Token",
    "githubApi", 
    {"accessToken": config['credentials']['github']['token']}
)

# 4. Telegram Bot
create_credential(
    "Telegram Bot",
    "telegramApi",
    {"accessToken": config['credentials']['telegram']['bot_token']}
)

# 5. Google Sheets
with open(config['credentials']['google_sheets']['credentials_path'], 'r') as f:
    gcp_creds = json.load(f)

create_credential(
    "Google Sheets",
    "googleSheetsOAuth2Api",
    {
        "projectId": gcp_creds.get('project_id', ''),
        "serviceAccountEmail": gcp_creds.get('client_email', ''),
        "privateKey": gcp_creds.get('private_key', '')
    }
)

print("\n✅ 所有 Credentials 建立完成")
```

---

## 第四步：建立 A 流程（每日自動發文）

用 N8N API 匯入以下工作流程。

請用 Python 執行：

```python
import json
import requests

with open(r'D:\N8N全自動工作流\credentials.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

N8N_URL = "http://localhost:5678"
SPREADSHEET_ID = config['credentials']['google_sheets']['spreadsheet_id']
GITHUB_USER = config['credentials']['github']['username']
GITHUB_REPO = config['credentials']['github']['repo']
GITHUB_BRANCH = config['credentials']['github']['branch']
TELEGRAM_CHAT_ID = config['credentials']['telegram']['chat_id']

workflow_a = {
  "name": "🅐 每日自動發文流程",
  "active": False,
  "nodes": [
    {
      "id": "a1",
      "name": "A-1 每天09:00觸發",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [100, 300],
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
        }
      }
    },
    {
      "id": "a2",
      "name": "A-2 讀取關鍵字清單",
      "type": "n8n-nodes-base.googleSheets",
      "position": [320, 300],
      "parameters": {
        "operation": "read",
        "spreadsheetId": SPREADSHEET_ID,
        "range": "關鍵字清單!A:E",
        "options": {}
      }
    },
    {
      "id": "a2b",
      "name": "A-2b 過濾待寫關鍵字",
      "type": "n8n-nodes-base.filter",
      "position": [540, 300],
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json['狀態']}}",
              "operation": "equal",
              "value2": "待寫"
            }
          ]
        }
      }
    },
    {
      "id": "a2c",
      "name": "A-2c 取前3筆",
      "type": "n8n-nodes-base.limit",
      "position": [760, 300],
      "parameters": {"maxItems": 3}
    },
    {
      "id": "a3",
      "name": "A-3 搜尋競品文章",
      "type": "n8n-nodes-base.httpRequest",
      "position": [980, 300],
      "parameters": {
        "method": "GET",
        "url": "=https://www.googleapis.com/customsearch/v1?key={{$env.GOOGLE_CSE_KEY}}&cx={{$env.GOOGLE_CSE_ID}}&q={{$json['關鍵字']}}&num=5",
        "options": {}
      }
    },
    {
      "id": "a4",
      "name": "A-4 Claude生成SEO文章",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1200, 300],
      "parameters": {
        "method": "POST",
        "url": "https://api.anthropic.com/v1/messages",
        "headers": {
          "parameters": [
            {"name": "x-api-key", "value": config['credentials']['claude']['api_key']},
            {"name": "anthropic-version", "value": "2023-06-01"},
            {"name": "content-type", "value": "application/json"}
          ]
        },
        "body": {
          "mode": "raw",
          "raw": "={\n  \"model\": \"claude-sonnet-4-6\",\n  \"max_tokens\": 4096,\n  \"messages\": [{\n    \"role\": \"user\",\n    \"content\": \"你是台灣最專業的理財部落格作者。請用繁體中文寫一篇關於【{{$('A-2c 取前3筆').item.json['關鍵字']}}】的SEO文章。\\n\\n要求：\\n1. 字數1500字以上\\n2. 包含至少4個H2標題\\n3. 推薦碼/優惠說明在前300字內出現\\n4. 包含速覽比較表格（Markdown格式）\\n5. 包含明確CTA（例如：立即開戶拿NT$XXX）\\n6. 包含至少5個FAQ問題\\n7. 文末再放一次CTA\\n8. 用emoji增加可讀性（📌⚠️✅❌💰🎁）\\n9. 繁體中文用詞要道地自然\\n\\n競品文章資訊：{{$('A-3 搜尋競品文章').item.json}}\\n\\n請直接輸出Markdown格式的文章，不要有任何前言。文章開頭加上Hugo front matter：\\n---\\ntitle: \\\"文章標題\\\"\\ndate: {{$now.format('yyyy-MM-dd')}}\\ndescription: \\\"文章描述（150字以內）\\\"\\ntags: [\\\"推薦碼\\\", \\\"銀行\\\"]\\ncategories: [\\\"金融理財\\\"]\\n---\"\n  }]\n}"
        }
      }
    },
    {
      "id": "a5",
      "name": "A-5 第一道品檢",
      "type": "n8n-nodes-base.code",
      "position": [1420, 300],
      "parameters": {
        "jsCode": "const article = $input.item.json.content[0].text;\nconst checks = {\n  minLength: article.length >= 2400,\n  hasH2: (article.match(/## /g) || []).length >= 3,\n  hasCTA: /立即開戶|點此申請|馬上申請/.test(article),\n  hasFrontMatter: article.includes('---')\n};\nconst passed = Object.values(checks).every(v => v);\nreturn [{\n  json: {\n    article,\n    checks,\n    passed,\n    keyword: $('A-2c 取前3筆').item.json['關鍵字'],\n    retry_count: 0\n  }\n}];"
      }
    },
    {
      "id": "a5_check",
      "name": "A-5 品檢通過？",
      "type": "n8n-nodes-base.if",
      "position": [1640, 300],
      "parameters": {
        "conditions": {
          "boolean": [{"value1": "={{$json.passed}}", "value2": true}]
        }
      }
    },
    {
      "id": "a6",
      "name": "A-6 推送到GitHub",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1860, 200],
      "parameters": {
        "method": "PUT",
        "url": f"=https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/content/posts/{{{{$now.format('yyyy-MM-dd')}}}}-{{{{$json.keyword.replace(/ /g, '-').toLowerCase()}}}}.md",
        "headers": {
          "parameters": [
            {"name": "Authorization", "value": f"token {config['credentials']['github']['token']}"},
            {"name": "Content-Type", "value": "application/json"}
          ]
        },
        "body": {
          "mode": "raw",
          "raw": "={\"message\": \"feat: 自動發文 - {{$json.keyword}}\", \"content\": \"{{Buffer.from($json.article).toString('base64')}}\", \"branch\": \"" + GITHUB_BRANCH + "\"}"
        }
      }
    },
    {
      "id": "a7",
      "name": "A-7 更新發文記錄",
      "type": "n8n-nodes-base.googleSheets",
      "position": [2080, 200],
      "parameters": {
        "operation": "append",
        "spreadsheetId": SPREADSHEET_ID,
        "range": "發文記錄!A:G",
        "valueInputMode": "USER_ENTERED",
        "values": {
          "values": [[
            "={{$now.format('yyyy-MM-dd')}}",
            "={{$('A-5 第一道品檢').item.json.keyword}}",
            "={{$('A-5 第一道品檢').item.json.keyword}}",
            f"=https://{config['site']['url']}/posts/{{{{$now.format('yyyy-MM-dd')}}}}-{{{{$('A-5 第一道品檢').item.json.keyword.replace(/ /g, '-').toLowerCase()}}}}",
            "={{$('A-5 第一道品檢').item.json.article.length}}",
            "已發布",
            "通過"
          ]]
        }
      }
    },
    {
      "id": "a8",
      "name": "A-8 更新關鍵字狀態",
      "type": "n8n-nodes-base.googleSheets",
      "position": [2300, 200],
      "parameters": {
        "operation": "update",
        "spreadsheetId": SPREADSHEET_ID,
        "range": "關鍵字清單!C:C",
        "valueInputMode": "USER_ENTERED",
        "values": {"values": [["已完成"]]}
      }
    },
    {
      "id": "a9_success",
      "name": "A-9 Telegram成功通知",
      "type": "n8n-nodes-base.telegram",
      "position": [2520, 200],
      "parameters": {
        "chatId": TELEGRAM_CHAT_ID,
        "text": "=✅ Pick-TW 今日發文完成！\n\n📝 關鍵字：{{$('A-5 第一道品檢').item.json.keyword}}\n📊 字數：{{$('A-5 第一道品檢').item.json.article.length}} 字\n🌐 網址：https://pick-tw.com\n⏰ 時間：{{$now.format('yyyy-MM-dd HH:mm')}}"
      }
    },
    {
      "id": "a9_fail",
      "name": "A-9b Telegram品檢失敗通知",
      "type": "n8n-nodes-base.telegram",
      "position": [1860, 400],
      "parameters": {
        "chatId": TELEGRAM_CHAT_ID,
        "text": "=⚠️ Pick-TW 品檢未通過，需人工處理\n\n關鍵字：{{$('A-5 第一道品檢').item.json.keyword}}\n失敗項目：{{JSON.stringify($('A-5 第一道品檢').item.json.checks)}}"
      }
    }
  ],
  "connections": {
    "A-1 每天09:00觸發": {"main": [[{"node": "A-2 讀取關鍵字清單", "type": "main", "index": 0}]]},
    "A-2 讀取關鍵字清單": {"main": [[{"node": "A-2b 過濾待寫關鍵字", "type": "main", "index": 0}]]},
    "A-2b 過濾待寫關鍵字": {"main": [[{"node": "A-2c 取前3筆", "type": "main", "index": 0}]]},
    "A-2c 取前3筆": {"main": [[{"node": "A-3 搜尋競品文章", "type": "main", "index": 0}]]},
    "A-3 搜尋競品文章": {"main": [[{"node": "A-4 Claude生成SEO文章", "type": "main", "index": 0}]]},
    "A-4 Claude生成SEO文章": {"main": [[{"node": "A-5 第一道品檢", "type": "main", "index": 0}]]},
    "A-5 第一道品檢": {"main": [[{"node": "A-5 品檢通過？", "type": "main", "index": 0}]]},
    "A-5 品檢通過？": {
      "main": [
        [{"node": "A-6 推送到GitHub", "type": "main", "index": 0}],
        [{"node": "A-9b Telegram品檢失敗通知", "type": "main", "index": 0}]
      ]
    },
    "A-6 推送到GitHub": {"main": [[{"node": "A-7 更新發文記錄", "type": "main", "index": 0}]]},
    "A-7 更新發文記錄": {"main": [[{"node": "A-8 更新關鍵字狀態", "type": "main", "index": 0}]]},
    "A-8 更新關鍵字狀態": {"main": [[{"node": "A-9 Telegram成功通知", "type": "main", "index": 0}]]}
  }
}

r = requests.post(
    f"{N8N_URL}/api/v1/workflows",
    json=workflow_a,
    headers={"Content-Type": "application/json"}
)

if r.status_code in [200, 201]:
    workflow_id = r.json().get('id')
    print(f"✅ A流程建立成功！ID：{workflow_id}")
    print(f"   請打開 http://localhost:5678 確認流程")
else:
    print(f"❌ A流程建立失敗：{r.status_code}")
    print(r.text)
```

---

## 第五步：建立 D 流程（每週收益統計）

```python
workflow_d = {
  "name": "🅓 每週收益統計",
  "active": False,
  "nodes": [
    {
      "id": "d1",
      "name": "D-1 每週一09:30觸發",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [100, 300],
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "30 9 * * 1"}]
        }
      }
    },
    {
      "id": "d2",
      "name": "D-2 讀取收益記錄",
      "type": "n8n-nodes-base.googleSheets",
      "position": [320, 300],
      "parameters": {
        "operation": "read",
        "spreadsheetId": SPREADSHEET_ID,
        "range": "收益記錄!A:E"
      }
    },
    {
      "id": "d3",
      "name": "D-3 計算損益",
      "type": "n8n-nodes-base.code",
      "position": [540, 300],
      "parameters": {
        "jsCode": "const records = $input.all();\nconst monthlyFixed = 968;\nconst weeklyFixed = Math.round(monthlyFixed / 4);\nlet weeklyRevenue = 0;\nconst oneWeekAgo = new Date();\noneWeekAgo.setDate(oneWeekAgo.getDate() - 7);\nrecords.forEach(r => {\n  const date = new Date(r.json['日期']);\n  if (date >= oneWeekAgo) weeklyRevenue += Number(r.json['金額(NT$)'] || 0);\n});\nconst totalRevenue = records.reduce((sum, r) => sum + Number(r.json['金額(NT$)'] || 0), 0);\nconst gap = weeklyFixed - weeklyRevenue;\nreturn [{ json: { weeklyRevenue, weeklyFixed, totalRevenue, gap, breakeven: gap <= 0 } }];"
      }
    },
    {
      "id": "d4",
      "name": "D-4 Telegram週報",
      "type": "n8n-nodes-base.telegram",
      "position": [760, 300],
      "parameters": {
        "chatId": TELEGRAM_CHAT_ID,
        "text": "=📊 Pick-TW 本週收益報告\n\n💰 本週收益：NT${{$json.weeklyRevenue}}\n📈 累計收益：NT${{$json.totalRevenue}}\n🎯 每週目標：NT${{$json.weeklyFixed}}\n{{$json.breakeven ? '✅ 本週達到損益平衡！' : '❌ 距損益平衡還差：NT$' + $json.gap}}\n\n⏰ {{$now.format('yyyy-MM-dd')}}"
      }
    }
  ],
  "connections": {
    "D-1 每週一09:30觸發": {"main": [[{"node": "D-2 讀取收益記錄", "type": "main", "index": 0}]]},
    "D-2 讀取收益記錄": {"main": [[{"node": "D-3 計算損益", "type": "main", "index": 0}]]},
    "D-3 計算損益": {"main": [[{"node": "D-4 Telegram週報", "type": "main", "index": 0}]]}
  }
}

r = requests.post(f"{N8N_URL}/api/v1/workflows", json=workflow_d, headers={"Content-Type": "application/json"})
print(f"{'✅' if r.status_code in [200,201] else '❌'} D流程：{r.status_code}")
```

---

## 第六步：建立 N 流程（系統健康監控）

```python
workflow_n = {
  "name": "🅘 系統健康監控",
  "active": False,
  "nodes": [
    {
      "id": "n1",
      "name": "N-1 每天23:00觸發",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [100, 300],
      "parameters": {
        "rule": {"interval": [{"field": "cronExpression", "expression": "0 23 * * *"}]}
      }
    },
    {
      "id": "n2",
      "name": "N-2 確認今日有無發文",
      "type": "n8n-nodes-base.googleSheets",
      "position": [320, 300],
      "parameters": {
        "operation": "read",
        "spreadsheetId": SPREADSHEET_ID,
        "range": "發文記錄!A:F"
      }
    },
    {
      "id": "n3",
      "name": "N-3 判斷今日發文狀態",
      "type": "n8n-nodes-base.code",
      "position": [540, 300],
      "parameters": {
        "jsCode": "const records = $input.all();\nconst today = new Date().toISOString().split('T')[0];\nconst todayPost = records.find(r => r.json['日期'] === today);\nreturn [{ json: { hasPost: !!todayPost, today, post: todayPost?.json || null } }];"
      }
    },
    {
      "id": "n4",
      "name": "N-4 ping 網站",
      "type": "n8n-nodes-base.httpRequest",
      "position": [760, 300],
      "parameters": {
        "method": "GET",
        "url": config['site']['url'],
        "options": {"timeout": 10000}
      }
    },
    {
      "id": "n5",
      "name": "N-5 Telegram健康報告",
      "type": "n8n-nodes-base.telegram",
      "position": [980, 300],
      "parameters": {
        "chatId": TELEGRAM_CHAT_ID,
        "text": "=🏥 Pick-TW 每日健康報告\n\n{{$('N-3 判斷今日發文狀態').item.json.hasPost ? '✅ 今日已發文' : '⚠️ 今日尚未發文！'}}\n🌐 網站狀態：{{$json.statusCode === 200 ? '✅ 正常' : '❌ 異常！'}}\n⏰ {{$now.format('yyyy-MM-dd HH:mm')}}"
      }
    }
  ],
  "connections": {
    "N-1 每天23:00觸發": {"main": [[{"node": "N-2 確認今日有無發文", "type": "main", "index": 0}]]},
    "N-2 確認今日有無發文": {"main": [[{"node": "N-3 判斷今日發文狀態", "type": "main", "index": 0}]]},
    "N-3 判斷今日發文狀態": {"main": [[{"node": "N-4 ping 網站", "type": "main", "index": 0}]]},
    "N-4 ping 網站": {"main": [[{"node": "N-5 Telegram健康報告", "type": "main", "index": 0}]]}
  }
}

r = requests.post(f"{N8N_URL}/api/v1/workflows", json=workflow_n, headers={"Content-Type": "application/json"})
print(f"{'✅' if r.status_code in [200,201] else '❌'} N流程：{r.status_code}")
print("\n🎉 所有流程建立完成！請打開 http://localhost:5678 確認")
```

---

## 第七步：測試所有流程

```python
import requests

N8N_URL = "http://localhost:5678"

# 列出所有已建立的流程
r = requests.get(f"{N8N_URL}/api/v1/workflows")
workflows = r.json().get('data', [])

print("📋 已建立的流程：")
for wf in workflows:
    print(f"  ID: {wf['id']} | 名稱: {wf['name']} | 狀態: {'啟用' if wf['active'] else '停用'}")

print("\n⚠️ 注意：所有流程預設為停用狀態")
print("請打開 http://localhost:5678 手動測試每個流程")
print("確認運作正常後再開啟自動執行")
```

---

## 第八步：手動測試 A 流程

在 N8N 介面：
1. 打開 http://localhost:5678
2. 點「🅐 每日自動發文流程」
3. 點右上角 **「Execute Workflow」**
4. 觀察每個節點是否正常執行
5. 確認 Telegram 有收到通知
6. 確認 Google Sheets 有新增記錄

全部正常後，點右上角開關**啟用**流程。

---

## 完成後回報

請告訴我：
1. 哪些流程建立成功
2. 哪些步驟有錯誤（附上錯誤訊息）
3. http://localhost:5678 畫面截圖
