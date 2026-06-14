<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <span>AE总数</span>
            <el-icon :size="24" color="#409EFF"><Document /></el-icon>
          </div>
          <div class="stat-value" :class="'primary'">{{ stats.totalAe }}</div>
          <div class="stat-label">累计不良事件编码</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <span>SAE待报告</span>
            <el-icon :size="24" color="#e6a23c"><WarningFilled /></el-icon>
          </div>
          <div class="stat-value" :class="'warning'">{{ stats.pendingSae }}</div>
          <div class="stat-label">严重不良事件等待处理</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <span>开放偏离</span>
            <el-icon :size="24" color="#f56c6c"><CloseCircle /></el-icon>
          </div>
          <div class="stat-value" :class="'danger'">{{ stats.openDeviation }}</div>
          <div class="stat-label">方案偏离未解决</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <span>合规评分</span>
            <el-icon :size="24" color="#67c23a"><CircleCheckFilled /></el-icon>
          </div>
          <div class="stat-value" :class="getComplianceClass">{{ stats.complianceScore }}<span style="font-size: 16px">%</span></div>
          <div class="stat-label">整体合规度</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="quick-actions">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <el-space>
            <el-button type="primary" size="large" :icon="Plus" @click="goToPage('/ae')">
              新增AE编码
            </el-button>
            <el-button type="success" size="large" :icon="Document" @click="goToPage('/sae')">
              查看SAE报告
            </el-button>
            <el-button type="warning" size="large" :icon="WarningFilled" @click="goToPage('/deviation')">
              处理方案偏离
            </el-button>
            <el-button type="info" size="large" :icon="TrendCharts" @click="goToPage('/signal')">
              信号挖掘分析
            </el-button>
            <el-button type="danger" size="large" :loading="importing" @click="importMockCases">
              <el-icon><Upload /></el-icon>
              导入模拟测试病例
            </el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="system-status">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
            </div>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="LLM 模型">
              <el-tag :type="health.llm ? 'success' : 'danger'">
                {{ health.llm ? '正常' : '异常' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="向量数据库">
              <el-tag :type="health.vector_db ? 'success' : 'danger'">
                {{ health.vector_db ? '正常' : '异常' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="关系数据库">
              <el-tag :type="health.db ? 'success' : 'danger'">
                {{ health.db ? '正常' : '异常' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const importing = ref(false)
const stats = reactive({
  totalAe: 0,
  pendingSae: 0,
  openDeviation: 0,
  complianceScore: 0
})
const health = reactive({
  llm: false,
  vector_db: false,
  db: false
})

onMounted(() => {
  loadData()
})

async function loadData() {
  try {
    const [aeRes, saeRes, devRes, compRes, healthRes] = await Promise.all([
      api.get('/api/ae/results', { params: { page: 1, page_size: 1 } }),
      api.get('/api/saereport/list', { params: { page: 1, page_size: 1 } }),
      api.get('/api/deviations/list', { params: { page: 1, page_size: 1, status: 'open' } }),
      api.get('/api/compliance/report'),
      api.get('/api/health')
    ])
    stats.totalAe = aeRes.data.total || 0
    stats.pendingSae = saeRes.data.total || 0
    stats.openDeviation = devRes.data.total || 0
    stats.complianceScore = Math.round(compRes.data.overall_score * 100) || 0
    health.llm = healthRes.data.llm_status !== 'unhealthy'
    health.vector_db = healthRes.data.vector_db_status === 'healthy'
    health.db = healthRes.data.mysql_status === 'healthy'
  } catch (e) {
    console.error('加载数据失败', e)
  }
}

function goToPage(path) {
  router.push(path)
}

function getComplianceClass() {
  if (stats.complianceScore >= 90) return 'success'
  if (stats.complianceScore >= 70) return 'warning'
  return 'danger'
}

async function importMockCases() {
  importing.value = true
  try {
    const res = await api.post('/api/admin/seed/mock-cases')
    ElMessage.success(`成功导入 ${res.data.count} 个模拟病例`)
    await loadData()
  } catch (e) {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.stat-card {
  .stat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-size: 14px;
    color: #909399;
  }
  .stat-value {
    font-size: 36px;
    font-weight: bold;
    line-height: 1;
    margin-bottom: 8px;
    &.primary { color: #2B579A; }
    &.success { color: #67c23a; }
    &.warning { color: #e6a23c; }
    &.danger { color: #f56c6c; }
  }
  .stat-label {
    font-size: 12px;
    color: #c0c4cc;
    margin-top: 8px;
  }
}
.card-header {
  font-weight: 600;
}
.quick-actions {
  margin-top: 8px;
}
.system-status {
  margin-top: 8px;
}
</style>