<template>
  <div class="sae-reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>SAE报告列表</span>
          <el-button text type="primary" @click="loadReports">刷新</el-button>
        </div>
      </template>
      <el-table :data="reports" stripe v-loading="loading" max-height="500">
        <el-table-column prop="report_id" label="报告编号" width="160" />
        <el-table-column prop="patient_id" label="患者" width="110" />
        <el-table-column prop="ae_text" label="AE描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.report_status === 'draft' ? 'info' : row.report_status === 'submitted' ? 'success' : 'warning'" size="small">
              {{ row.report_status || '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="120" align="center">
          <template #default="{ row }">
            {{ row.deadline || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170" align="center">
          <template #default="{ row }">
            {{ row.created_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">查看</el-button>
            <el-button type="success" size="small" @click="exportDocx(row)">导出</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="loadReports"
      />
    </el-card>

    <el-dialog v-model="detailVisible" title="SAE报告详情" width="800px" destroy-on-close>
      <el-descriptions v-if="detail" :column="2" border size="small">
        <el-descriptions-item label="报告编号" :span="2">{{ detail.report_id }}</el-descriptions-item>
        <el-descriptions-item label="患者编号">{{ detail.patient_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ detail.cioms_fields?.patient_gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出生日期" :span="2">{{ detail.cioms_fields?.patient_dob || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="detail.report_status === 'draft' ? 'info' : 'success'" size="small">
            {{ detail.report_status || '草稿' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template v-if="detail && detail.cioms_fields">
        <el-divider content-position="left">CIOMS-I 字段</el-divider>
        <el-descriptions :column="3" border size="small">
          <template v-for="(value, key) in detail.cioms_fields" :key="key">
            <el-descriptions-item :label="key">
              {{ value || '-' }}
            </el-descriptions-item>
          </template>
        </el-descriptions>
      </template>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="success" @click="exportDetailDocx">导出 DOCX</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const reports = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)

const detailVisible = ref(false)
const detail = ref(null)

onMounted(() => {
  loadReports()
})

async function loadReports() {
  loading.value = true
  try {
    const res = await api.get('/api/saereport/list', {
      params: { page: page.value, page_size: pageSize.value }
    })
    reports.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('加载SAE报告失败', e)
  } finally {
    loading.value = false
  }
}

async function viewDetail(row) {
  try {
    const res = await api.get(`/api/saereport/${row.report_id}`)
    detail.value = res.data
    detailVisible.value = true
  } catch (e) {
    ElMessage.error('获取报告详情失败')
  }
}

function exportDocx(row) {
  window.open(`/api/saereport/${row.report_id}/export?format=docx`, '_blank')
}

function exportDetailDocx() {
  if (detail.value) {
    window.open(`/api/saereport/${detail.value.report_id}/export?format=docx`, '_blank')
  }
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