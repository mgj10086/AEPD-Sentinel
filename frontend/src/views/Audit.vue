<template>
  <div class="audit">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>审计日志</span>
          <div class="header-actions">
            <el-button text type="primary" @click="verifyChain" :loading="verifying">验证链</el-button>
            <el-button text type="primary" @click="loadLogs">刷新</el-button>
          </div>
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

    <!-- 哈希链验证结果对话框 -->
    <el-dialog v-model="verifyVisible" title="审计日志完整性验证" width="600px" top="5vh">
      <el-alert
        :type="verifyResult?.valid ? 'success' : 'error'"
        :title="verifyResult?.valid ? '✅ 哈希链验证通过，日志未被篡改' : '❌ 发现篡改！'"
        show-icon
        :description="verifyResult ? `共检查 ${verifyResult.checked} 条带 HMAC 的日志，总记录 ${verifyResult.total} 条` : ''"
      />
      <el-table v-if="verifyResult?.issues?.length" :data="verifyResult.issues" stripe max-height="400" style="margin-top: 12px">
        <el-table-column prop="log_id" label="被篡改日志" width="200" />
        <el-table-column label="说明">
          <template #default>
            <span style="color: #f56c6c">HMAC 不匹配 — 数据已被篡改</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const verifying = ref(false)
const verifyVisible = ref(false)
const verifyResult = ref(null)

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

async function verifyChain() {
  verifying.value = true
  try {
    const res = await api.post('/api/admin/audit-logs/verify')
    verifyResult.value = res.data
    verifyVisible.value = true
  } catch (e) {
    console.error('验证失败', e)
  } finally {
    verifying.value = false
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
.header-actions {
  display: flex;
  gap: 8px;
}
</style>