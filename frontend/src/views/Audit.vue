<template>
  <div class="audit">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>审计日志</span>
          <el-button text type="primary" @click="loadLogs">刷新</el-button>
        </div>
      </template>
      <el-table :data="logs" stripe v-loading="loading" max-height="600">
        <el-table-column prop="log_id" label="日志编号" width="180" />
        <el-table-column prop="user_id" label="用户" width="120" />
        <el-table-column prop="agent_type" label="智能体" width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.agent_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="130">
          <template #default="{ row }">
            <el-tag
              :type="getActionType(row.action)"
              size="small"
            >
              {{ row.action || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_id" label="资源" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="180" align="center" />
      </el-table>
      <el-pagination
        v-model:current-page="page"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="loadLogs"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)

onMounted(() => {
  loadLogs()
})

async function loadLogs() {
  loading.value = true
  try {
    const res = await api.get('/api/admin/audit-logs', {
      params: { page: page.value, page_size: pageSize.value }
    })
    logs.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('加载审计日志失败', e)
  } finally {
    loading.value = false
  }
}

function getActionType(action) {
  const map = {
    'create': '',
    'update': 'warning',
    'delete': 'danger',
    'login': 'success',
    'upload': 'info',
    'export': 'primary'
  }
  return map[action] || 'info'
}
</script>

<style scoped>
.card-header {
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>