<template>
  <div class="knowledge">
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>上传知识文档</span>
            </div>
          </template>
          <el-form :inline="true">
            <el-form-item label="文档类型">
              <el-select v-model="uploadForm.type" placeholder="选择类型" style="width: 180px">
                <el-option label="MedDRA术语" value="meddra" />
                <el-option label="ICH-GCP指南" value="ich_gcp" />
                <el-option label="FAERS数据" value="faers" />
                <el-option label="PubMed文献" value="pubmed" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="uploadForm.description" placeholder="文档描述" style="width: 300px" />
            </el-form-item>
            <el-form-item>
              <el-upload
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                accept=".pdf,.doc,.docx,.txt,.md"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  选择文件
                </el-button>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button type="success" :loading="uploading" :disabled="!file" @click="uploadFile">
                <el-icon><UploadFilled /></el-icon>
                上传
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="table-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>知识库列表</span>
              <el-button text type="primary" @click="loadList">刷新</el-button>
            </div>
          </template>
          <el-table :data="list" stripe v-loading="loading" max-height="450">
            <el-table-column prop="item_id" label="编号" width="160" />
            <el-table-column prop="type" label="类型" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_name" label="文件名" min-width="180" show-overflow-tooltip />
            <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'completed' ? 'success' : row.status === 'processing' ? 'warning' : row.status === 'failed' ? 'danger' : 'info'"
                  size="small"
                >
                  {{ row.status === 'completed' ? '已完成' : row.status === 'processing' ? '处理中' : row.status === 'failed' ? '失败' : '待处理' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="160" align="center">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.progress || 0"
                  :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : ''"
                  :stroke-width="12"
                />
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="170" align="center">
              <template #default="{ row }">
                {{ row.created_at || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center" fixed="right">
              <template #default="{ row }">
                <el-popconfirm
                  title="确定删除该知识条目？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  @confirm="deleteItem(row)"
                >
                  <template #reference>
                    <el-button type="danger" size="small">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)

const file = ref(null)
const uploading = ref(false)
const uploadForm = reactive({
  type: '',
  description: ''
})

onMounted(() => {
  loadList()
})

function handleFileChange(uploadFile) {
  file.value = uploadFile.raw
}

function handleFileRemove() {
  file.value = null
}

async function uploadFile() {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    if (uploadForm.type) formData.append('type', uploadForm.type)
    if (uploadForm.description) formData.append('description', uploadForm.description)
    const res = await api.post('/api/admin/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success(`上传成功，ID: ${res.data.item_id}`)
    file.value = null
    uploadForm.type = ''
    uploadForm.description = ''
    loadList()
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await api.get('/api/admin/knowledge/list', {
      params: { page: page.value, page_size: pageSize.value }
    })
    list.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('加载知识库列表失败', e)
  } finally {
    loading.value = false
  }
}

async function deleteItem(row) {
  try {
    await api.delete(`/api/admin/knowledge/${row.item_id}`)
    ElMessage.success('删除成功')
    loadList()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.knowledge {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.card-header {
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-row {
  margin-top: 0;
}
</style>