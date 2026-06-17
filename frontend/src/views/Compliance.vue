<template>
  <div class="compliance">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="hover" class="score-card">
          <div class="score-label">综合评分</div>
          <el-progress
            type="dashboard"
            :percentage="data.overall_score ? Math.round(data.overall_score * 100) : 0"
            :color="scoreColor"
          >
            <template #default="{ percentage }">
              <span class="score-number">{{ percentage }}%</span>
            </template>
          </el-progress>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="score-card">
          <div class="score-label">及时性评分</div>
          <el-progress
            type="dashboard"
            :percentage="data.timeliness_score ? Math.round(data.timeliness_score * 100) : 0"
            :color="scoreColor"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="score-card">
          <div class="score-label">完整性评分</div>
          <el-progress
            type="dashboard"
            :percentage="data.completeness ? Math.round(data.completeness * 100) : 0"
            :color="scoreColor"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="table-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>时限监控</span>
            </div>
          </template>
          <el-table :data="data.sae_timeliness || []" stripe max-height="350">
            <el-table-column prop="report_id" label="报告编号" width="160" />
            <el-table-column label="剩余天数" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="getDaysType(row.days_remaining)" size="small">
                  {{ row.days_remaining ?? '-' }} 天
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="deadline_7day" label="7日截止" width="120" align="center" />
            <el-table-column prop="status" label="状态" min-width="120" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>质量问题</span>
            </div>
          </template>
          <el-table :data="data.issues || []" stripe max-height="350">
            <el-table-column label="严重程度" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'critical' ? 'danger' : 'warning'" size="small">
                  {{ row.severity === 'critical' ? '严重' : '一般' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="问题描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="source" label="来源" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'

const data = reactive({
  overall_score: 0,
  timeliness_score: 0,
  sae_timeliness: [],
  completeness: 0,
  issues: []
})

const scoreColor = computed(() => {
  if (!data.overall_score) return 'var(--ae-stat-danger)'
  if (data.overall_score >= 0.9) return 'var(--ae-stat-success)'
  if (data.overall_score >= 0.7) return 'var(--ae-stat-warning)'
  return 'var(--ae-stat-danger)'
})

onMounted(() => {
  loadData()
})

async function loadData() {
  try {
    const res = await api.get('/api/compliance/report')
    const score = res.data.overall_score || 0
    Object.assign(data, {
      overall_score: score,
      timeliness_score: res.data.timeliness_score || score,
      sae_timeliness: res.data.sae_timeliness || [],
      completeness: res.data.completeness_score || score,
      issues: (res.data.issues || []).map(issue => ({
        description: issue,
        severity: issue.includes('超期') ? 'critical' : 'warning',
        source: '合规检查'
      }))
    })
  } catch (e) {
    console.error('加载合规数据失败', e)
  }
}

function getDaysType(days) {
  if (days == null) return 'info'
  if (days <= 3) return 'danger'
  if (days <= 7) return 'warning'
  return 'success'
}
</script>

<style scoped>
.compliance {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.score-card {
  text-align: center;
  .score-label {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--ae-text-score-label);
  }
}
.score-number {
  font-size: 22px;
  font-weight: bold;
}
.card-header {
  font-weight: 600;
}
.table-row {
  margin-top: 0;
}
</style>