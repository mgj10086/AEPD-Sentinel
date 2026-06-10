<template>
  <div class="deviations">
    <el-row :gutter="16" class="stat-row">
      <el-col :span="8">
        <el-card shadow="hover" class="dev-stat-card">
          <div class="dev-stat-header">严重偏离</div>
          <div class="dev-stat-value danger">{{ stats.critical }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="dev-stat-card">
          <div class="dev-stat-header">一般偏离</div>
          <div class="dev-stat-value warning">{{ stats.normal }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="dev-stat-card">
          <div class="dev-stat-header">已解决</div>
          <div class="dev-stat-value success">{{ stats.resolved }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="table-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>偏离记录</span>
              <el-button text type="primary" @click="loadList">刷新</el-button>
            </div>
          </template>
          <el-table :data="list" stripe v-loading="loading" max-height="350">
            <el-table-column prop="deviation_id" label="编号" width="160" />
            <el-table-column prop="patient_id" label="患者" width="110" />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="severity" label="严重程度" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'critical' ? 'danger' : 'warning'" size="small">
                  {{ row.severity === 'critical' ? '严重' : '一般' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'resolved' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'resolved' ? '已解决' : '未解决' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" align="center" />
            <el-table-column label="操作" width="100" align="center" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status !== 'resolved'"
                  type="primary"
                  size="small"
                  @click="openResolve(row)"
                >
                  解决
                </el-button>
                <el-tag v-else type="info" size="small">已完结</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="page"
            :total="total"
            layout="total, prev, pager, next"
            style="margin-top: 16px; justify-content: flex-end"
            @current-change="loadList"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="resolveVisible" title="解决偏离" width="500px" destroy-on-close>
      <el-form :model="resolveForm" label-width="80px">
        <el-form-item label="处理人">
          <el-input v-model="resolveForm.resolved_by" placeholder="处理人姓名" />
        </el-form-item>
        <el-form-item label="解决方式">
          <el-input v-model="resolveForm.resolution" type="textarea" :rows="3" placeholder="请描述解决方式" />
        </el-form-item>
        <el-form-item label="采取措施">
          <el-input v-model="resolveForm.action_taken" type="textarea" :rows="2" placeholder="已采取的措施" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveVisible = false">取消</el-button>
        <el-button type="primary" :loading="resolving" @click="submitResolve">确认解决</el-button>
      </template>
    </el-dialog>

    <el-row :gutter="16" class="table-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>偏离规则参考</span>
            </div>
          </template>
          <el-table :data="rules" stripe max-height="300">
            <el-table-column prop="rule_id" label="规则编号" width="100" />
            <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
            <el-table-column label="严重程度" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'critical' ? 'danger' : 'warning'" size="small">
                  {{ row.severity === 'critical' ? '严重' : '一般' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="建议措施" min-width="150" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const list = ref([])
const rules = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const stats = reactive({ critical: 0, normal: 0, resolved: 0 })

const resolveVisible = ref(false)
const resolving = ref(false)
const currentDeviation = ref(null)
const resolveForm = reactive({
  resolution: '',
  resolved_by: '',
  action_taken: ''
})

onMounted(() => {
  loadList()
  loadRules()
})

async function loadList() {
  loading.value = true
  try {
    const res = await api.get('/api/deviations/list', {
      params: { page: page.value, page_size: pageSize.value }
    })
    list.value = res.data.items || []
    total.value = res.data.total || 0
    calcStats()
  } catch (e) {
    console.error('加载偏离列表失败', e)
  } finally {
    loading.value = false
  }
}

function calcStats() {
  stats.critical = list.value.filter(i => i.severity === 'critical').length
  stats.normal = list.value.filter(i => i.severity !== 'critical').length
  stats.resolved = list.value.filter(i => i.status === 'resolved').length
}

async function loadRules() {
  try {
    const res = await api.get('/api/deviations/rules')
    rules.value = res.data || []
  } catch (e) {
    console.error('加载规则失败', e)
  }
}

function openResolve(row) {
  currentDeviation.value = row
  resolveForm.resolution = ''
  resolveForm.resolved_by = ''
  resolveForm.action_taken = ''
  resolveVisible.value = true
}

async function submitResolve() {
  resolving.value = true
  try {
    await api.put(`/api/deviations/${currentDeviation.value.deviation_id}/resolve`, {
      resolution: resolveForm.resolution,
      resolved_by: resolveForm.resolved_by,
      action_taken: resolveForm.action_taken
    })
    ElMessage.success('偏离已解决')
    resolveVisible.value = false
    loadList()
  } catch (e) {
    ElMessage.error('解决偏离失败')
  } finally {
    resolving.value = false
  }
}
</script>

<style scoped>
.deviations {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.dev-stat-card {
  text-align: center;
  .dev-stat-header {
    font-size: 14px;
    color: #909399;
    margin-bottom: 8px;
  }
  .dev-stat-value {
    font-size: 32px;
    font-weight: bold;
    &.danger { color: #f56c6c; }
    &.warning { color: #e6a23c; }
    &.success { color: #67c23a; }
  }
}
.card-header {
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-row { margin-bottom: 0; }
.table-row { margin-top: 0; }
</style>