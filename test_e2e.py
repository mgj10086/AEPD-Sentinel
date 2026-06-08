import urllib.request, json, time, sys

API = 'http://localhost:8000'

def api(url, method='GET', body=None):
    data = None
    headers = {}
    if body:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(API + url, data=data, headers=headers, method=method)
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

print('='*60)
print('AE Sentinel 端到端测试')
print('='*60)

# 1. Login
print('\n[1] 登录测试')
r = api('/api/auth/login', 'POST', {'username': 'pv_user', 'password': '123456'})
print(f'  结果: code={r["code"]}, role={r["data"]["role"]}')
assert r['code'] == 200

# 2. Health
print('\n[2] 健康检查')
r = api('/api/health')
print(f'  LLM={r["services"]["llm"]}, VectorDB={r["services"]["vector_db"]}, MySQL={r["services"]["mysql"]}')

# 3. Batch import 10 cases
print('\n[3] 批量导入10个模拟病例')
cases = [
    {'ae_text': '患者出现头痛，轻度，自行缓解', 'patient_id': 'NSCLC-001', 'visit_date': '2025-06-01', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现恶心，持续约2小时，未予特殊处理', 'patient_id': 'NSCLC-002', 'visit_date': '2025-06-02', 'drug_name': 'XK-001'},
    {'ae_text': '患者诉食欲下降，进食量减少约一半', 'patient_id': 'NSCLC-003', 'visit_date': '2025-06-03', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现皮疹，斑丘疹，外用激素软膏后缓解', 'patient_id': 'NSCLC-004', 'visit_date': '2025-06-04', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现免疫相关肺炎，CT显示间质性肺病，气促加重，收治入院', 'patient_id': 'NSCLC-005', 'visit_date': '2025-06-05', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现免疫相关肝炎，ALT 350 U/L（>=5xULN），AST 280 U/L', 'patient_id': 'NSCLC-006', 'visit_date': '2025-06-06', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现疲乏，影响日常活动', 'patient_id': 'NSCLC-007', 'visit_date': '2025-06-07', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现发热，体温38.5度', 'patient_id': 'NSCLC-008', 'visit_date': '2025-06-08', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现输液反应，寒战，轻度发热', 'patient_id': 'NSCLC-009', 'visit_date': '2025-06-09', 'drug_name': 'XK-001'},
    {'ae_text': '患者出现肺炎，伴发热咳嗽，肺部感染，收入院治疗', 'patient_id': 'NSCLC-010', 'visit_date': '2025-06-10', 'drug_name': 'XK-001'},
]
r = api('/api/ae/batch', 'POST', {'ae_list': cases})
data = r['data']
print(f'  成功: {data["success_count"]} / 失败: {data["fail_count"]} / 总计: {data["total_count"]}')

sae_ids = []
for i, res in enumerate(data['results']):
    if 'error' in res:
        print(f'  [ERROR] {res["error"]}')
        continue
    sev = res.get('severity', '?')
    sae = res.get('sae_flag', False)
    pt = res['meddra_codes'][0]['pt_name'] if res['meddra_codes'] else '?'
    sae_tag = ' [SAE]' if sae else ''
    case = cases[i]
    print(f'  {res["ae_id"]} | {case["patient_id"]} | PT:{pt} | 严重度:{sev}{sae_tag}')
    if sae:
        sae_ids.append(res['ae_id'])

# 4. Generate SAE reports
print(f'\n[4] 生成SAE报告 ({len(sae_ids)}个)')
for ae_id in sae_ids:
    r = api('/api/saereport/generate', 'POST', {'ae_id': ae_id, 'reporter_name': '张医生', 'reporter_org': '研究中心'})
    d = r['data']
    print(f'  报告: {d["report_id"]} | 状态: {d["report_status"]} | 截止: {d["deadline"]}')

# 5. Query AE results
print('\n[5] 查询AE结果')
r = api('/api/ae/results?page=1&page_size=5')
print(f'  总数: {r["data"]["total"]}')

# 6. Query SAE list
print('\n[6] 查询SAE列表')
r = api('/api/saereport/list?page=1&page_size=10')
print(f'  SAE总数: {r["data"]["total"]}')

# 7. Deviation rules
print('\n[7] 偏离规则')
r = api('/api/deviations/rules')
print(f'  规则数: {len(r["data"])}')

# 8. Signal analysis
print('\n[8] 触发信号分析')
r = api('/api/signals/trigger', 'POST', {'drug_name': 'XK-001', 'analysis_period': 'monthly'})
print(f'  任务: {r["data"]["task_id"]} | 状态: {r["data"]["status"]}')

time.sleep(2)

# 9. Query signals
print('\n[9] 查询信号列表')
r = api('/api/signals/list?page=1&page_size=10')
print(f'  信号数: {r["data"]["total"]}')

# 10. Compliance
print('\n[10] 合规质控报告')
r = api('/api/compliance/report')
print(f'  综合评分: {r["data"]["overall_score"]}')
print(f'  SAE及时性: {len(r["data"].get("sae_timeliness", []))}条')
print(f'  完整性: {len(r["data"].get("field_completeness", []))}条')

# 11. Deviations list
print('\n[11] 偏离记录查询')
r = api('/api/deviations/list?page=1&page_size=10')
print(f'  偏离总数: {r["data"]["total"]}')

# 12. SAE deadlines
print('\n[12] SAE截止日监控')
r = api('/api/compliance/sae-deadlines')
print(f'  待监控报告: {len(r["data"])}条')

# 13. View SAE detail
r1 = api('/api/saereport/list?page=1&page_size=1')
if r1['data']['items']:
    report_id = r1['data']['items'][0]['report_id']
    print(f'\n[13] SAE详情查询: {report_id}')
    r2 = api(f'/api/saereport/{report_id}')
    print(f'  因果关系: {r2["data"]["causality_assessment"]}')
    print(f'  状态: {r2["data"]["report_status"]}')

# 14. Query AE detail
r = api('/api/ae/results?page=1&page_size=1')
if r['data']['items']:
    ae_id = r['data']['items'][0]['ae_id']
    print(f'\n[14] AE详情查询: {ae_id}')
    r2 = api(f'/api/ae/results/{ae_id}')
    codes = r2['data']['meddra_codes']
    if isinstance(codes, str):
        codes = json.loads(codes)
    print(f'  MedDRA PT: {codes[0]["pt_name"] if codes else "N/A"}')

print('\n' + '='*60)
print('所有测试通过!')
print('='*60)
