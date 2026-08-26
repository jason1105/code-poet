#!/usr/bin/env python3
import subprocess
import json
import os
import re
import sys
from datetime import datetime, timezone
from openai import OpenAI

# ── 1. Gather git information ─────────────────────────────────────────
def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

commit_sha   = run("git rev-parse HEAD")
short_sha    = commit_sha[:7]
commit_msg   = run("git log -1 --pretty=%s")
author       = run("git log -1 --pretty=%an")
timestamp    = datetime.now(timezone.utc).isoformat()

stat_raw = run("git diff HEAD~1 HEAD --stat")
diff_raw = run(
    "git diff HEAD~1 HEAD -- '*.java' '*.ts' '*.tsx' '*.py' '*.js'"
)

stat = stat_raw[:3000]
diff = diff_raw[:3000]

# Parse insertions / deletions from stat summary line
insertions = 0
deletions  = 0
files_changed = 0
m = re.search(r'(\d+) files? changed', stat_raw)
if m:
    files_changed = int(m.group(1))
m = re.search(r'(\d+) insertion', stat_raw)
if m:
    insertions = int(m.group(1))
m = re.search(r'(\d+) deletion', stat_raw)
if m:
    deletions = int(m.group(1))

# ── 2. Build prompt ───────────────────────────────────────────────────
prompt = f"""你是一位精通编程哲学的诗人。请根据以下代码变更，创作一首诗。
诗歌形式自由选择（七言绝句/现代诗/俳句/打油诗/自由诗），要体现代码的本质和程序员的情感。

变更摘要：
{stat}

代码diff片段：
{diff}

提交信息：{commit_msg}

请输出：
1) 诗体类型
2) 诗歌标题
3) 正文（保留换行）
4) 一句关于这次提交的程序员感悟（15字以内）

严格按以下JSON格式输出，不要有任何额外文字：
{{
"type": "七言绝句",
"title": "标题",
"poem": "第一行\\n第二行\\n第三行\\n第四行",
"insight": "感悟一句话"
}}"""

# ── 3. Call Anthropic API ─────────────────────────────────────────────
MODEL = os.environ.get("LLM_MODEL") or os.environ.get("OPENROUTER_MODEL") or "deepseek-v4-flash"
client = OpenAI(base_url=os.environ.get("LLM_BASE_URL") or "https://api.deepseek.com",
                api_key=os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", ""))

message = client.chat.completions.create(
    model=MODEL,
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
)

raw_response = message.choices[0].message.content.strip()

# Strip markdown code fences if present
raw_response = re.sub(r'^```(?:json)?\s*', '', raw_response)
raw_response = re.sub(r'\s*```$', '', raw_response)

# ── 4. Parse JSON response ────────────────────────────────────────────
try:
    poem_data = json.loads(raw_response)
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    print(f"Raw response: {raw_response}")
    sys.exit(1)

# ── 5. Build poem record ──────────────────────────────────────────────
new_poem = {
    "id": short_sha,
    "commit_sha": commit_sha,
    "commit_message": commit_msg,
    "author": author,
    "timestamp": timestamp,
    "type": poem_data.get("type", "现代诗"),
    "title": poem_data.get("title", "无题"),
    "poem": poem_data.get("poem", ""),
    "insight": poem_data.get("insight", ""),
    "files_changed": files_changed,
    "insertions": insertions,
    "deletions": deletions,
}

# ── 6. Read, prepend, trim, write collection ──────────────────────────
collection_path = "poems/collection.json"
os.makedirs("poems", exist_ok=True)

if os.path.exists(collection_path):
    with open(collection_path, "r", encoding="utf-8") as f:
        collection = json.load(f)
else:
    collection = []

collection.insert(0, new_poem)
collection = collection[:50]  # keep at most 50 poems

with open(collection_path, "w", encoding="utf-8") as f:
    json.dump(collection, f, ensure_ascii=False, indent=2)

print(f"✓ Poem written: 《{new_poem['title']}》 ({new_poem['type']})")
print(f"  Insight: {new_poem['insight']}")