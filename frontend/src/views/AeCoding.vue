<template>
  <div class="ae-coding">
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AE编码录入</span>
            </div>
          </template>
          <el-form :model="form" label-width="100px" ref="formRef">
            <el-form-item label="患者编号" prop="patient_id">
              <el-input v-model="form.patient_id" placeholder="如 NSCLC-001" />
            </el-form-item>
            <el-form-item label="访视日期" prop="visit_date">
              <el-date-picker
                v-model="form.visit_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="药物名称" prop="drug_name">
              <el-input v-model="form.drug_name" placeholder="如 XK-001" />
            </el-form-item>
            <el-form-item label="AE描述" prop="ae_text">
              <el-input
                v-model="form.ae_text"
                type="textarea"
                :rows="5"
                placeholder="请输入不良事件描述文本..."
              />
            </el-form-item>
            <el-form-item label="发生日期">
              <el-date-picker
                v-model="form.onset_date"
                type="date"
                placeholder="可选，AE发生日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="processing" @click="submitAe">
                <el-icon><VideoPlay /></el-icon>
                AI编码分析
              </el-button>
              <el-button @click="resetForm">清空</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card v-if="result">
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="AE编号">{{ result.ae_id }}</el-descriptions-item>
            <el-descriptions-item label="MedDRA编码">
              <el-tag v-for="(code, idx) in result.meddra_codes" :key="idx" type="info" style="margin-right: 4px">
                {{ code.pt_name || code.llt_name || code }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="严重程度">
              <el-tag :type="getSeverityType(result.severity)">{{ getSeverityLabel(result.severity) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="SAE标记">
              <el-tag :type="result.sae_flag ? 'danger' : 'success'">
                {{ result.sae_flag ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="result.sae_flag" label="SAE标准">
              <el-tag v-for="c in result.sae_criteria" :key="c" type="warning" style="margin-right: 4px">
                {{ c }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="预期性">
              <el-tag :type="result.expected_flag ? 'primary' : 'warning'">
                {{ result.expected_flag ? '预期内' : '非预期' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="因果关系（暂定）">{{ result.causality_tentative || '-' }}</el-descriptions-item>
            <el-descriptions-item label="处理耗时">{{ result.processing_time_ms }}ms</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card v-else>
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
            </div>
          </template>
          <el-empty description="暂无分析结果，请在左侧提交AE数据" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="ae-table-section">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AE编码记录</span>
              <el-button text type="primary" @click="loadRecords">刷新</el-button>
            </div>
          </template>
          <el-table :data="records" stripe v-loading="loadingRecords" max-height="400">
            <el-table-column prop="ae_id" label="编号" width="140" />
            <el-table-column prop="patient_id" label="患者" width="110" />
            <el-table-column prop="visit_date" label="访视日期" width="110" />
            <el-table-column label="MedDRA PT" min-width="140">
              <template #default="{ row }">
                <el-tag v-for="(code, idx) in (row.meddra_codes || [])" :key="idx" size="small" style="margin-right: 4px">
                  {{ code.pt_name || code.llt_name || code }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="严重度" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ getSeverityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="SAE" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="row.sae_flag ? 'danger' : 'success'" size="small">
                  {{ row.sae_flag ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="预期" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="row.expected_flag ? 'primary' : 'warning'" size="small">
                  {{ row.expected_flag ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.sae_flag"
                  type="danger"
                  size="small"
                  @click="generateSae(row)"
                >
                  生成SAE
                </el-button>
                <span v-else style="color: #c0c4cc">-</span>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="page"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            style="margin-top: 16px; justify-content: flex-end"
            @current-change="loadRecords"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const formRef = ref(null)
const processing = ref(false)
const result = ref(null)
const records = ref([])
const loadingRecords = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)

const form = reactive({
  patient_id: '',
  visit_date: '',
  drug_name: 'XK-001',
  ae_text: '',
  onset_date: ''
})

onMounted(() => {
  loadRecords()
})

function getSeverityType(severity) {
  const map = { '轻度': '', '中度': 'warning', '重度': 'danger' }
  return map[severity] || 'info'
}

function getSeverityLabel(severity) {
  return severity || '-'
}

function resetForm() {
  form.patient_id = ''
  form.visit_date = ''
  form.drug_name = 'XK-001'
  form.ae_text = ''
  form.onset_date = ''
  result.value = null
}

async function submitAe() {
  if (!form.ae_text) {
    ElMessage.warning('请输入AE描述文本')
    return
  }
  processing.value = true
  try {
    const res = await api.post('/api/ae/process', {
      ae_text: form.ae_text,
      patient_id: form.patient_id,
      visit_date: form.visit_date,
      drug_name: form.drug_name,
      onset_date: form.onset_date || undefined
    })
    result.value = res.data
    ElMessage.success('AE编码分析完成')
    loadRecords()
  } catch (e) {
    ElMessage.error(e.message || 'AE编码分析失败')
  } finally {
    processing.value = false
  }
}

async function loadRecords() {
  loadingRecords.value = true
  try {
    const res = await api.get('/api/ae/results', {
      params: { page: page.value, page_size: pageSize.value }
    })
    records.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('加载记录失败', e)
  } finally {
    loadingRecords.value = false
  }
}

async function generateSae(row) {
  try {
    await api.post('/api/saereport/generate', {
      ae_id: row.ae_id,
      reporter_name: '系统用户',
      reporter_org: 'AE Sentinel'
    })
    ElMessage.success(`SAE报告已生成，编号: ${row.ae_id}`)
  } catch (e) {
    ElMessage.error('SAE报告生成失败')
  }
}
</script>

<style scoped>
.ae-coding {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card-header {
  font-weight: 600;
}
.ae-table-section {
  margin-top: 0;
}
</style>