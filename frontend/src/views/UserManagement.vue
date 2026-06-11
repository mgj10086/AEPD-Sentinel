<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div class="header-actions">
            <el-input
              v-model="keyword"
              placeholder="搜索用户名/姓名"
              clearable
              style="width: 200px; margin-right: 8px"
              @clear="loadUsers"
              @keyup.enter="loadUsers"
            />
            <el-button type="primary" @click="openCreate">新建用户</el-button>
            <el-button text type="primary" @click="loadUsers">刷新</el-button>
          </div>
        </div>
      </template>
      <el-table :data="users" stripe v-loading="loading" max-height="600">
        <el-table-column prop="user_id" label="用户ID" width="120" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button text type="warning" size="small" @click="openPassword(row)">重置密码</el-button>
            <el-popconfirm
              title="确定删除此用户？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
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
        @current-change="loadUsers"
      />
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新建用户'" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="PV专员" value="pv_specialist" />
            <el-option label="CRA" value="cra" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="pwdVisible" title="重置密码" width="400px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handlePassword">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const users = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const saving = ref(false)

// 列表
onMounted(() => loadUsers())

async function loadUsers() {
  loading.value = true
  try {
    const res = await api.get('/api/admin/users/list', {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined }
    })
    users.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('加载用户列表失败', e)
  } finally {
    loading.value = false
  }
}

// 创建/编辑
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = reactive({ username: '', name: '', password: '', role: 'cra', email: '', phone: '' })
const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

function openCreate() {
  isEdit.value = false
  form.username = ''
  form.name = ''
  form.password = ''
  form.role = 'cra'
  form.email = ''
  form.phone = ''
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  form.username = row.username
  form.name = row.name
  form.password = ''
  form.role = row.role
  form.email = row.email || ''
  form.phone = row.phone || ''
  form._userId = row.user_id
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/api/admin/users/${form._userId}`, {
        name: form.name, role: form.role, email: form.email, phone: form.phone
      })
      ElMessage.success('用户更新成功')
    } else {
      await api.post('/api/admin/users/create', {
        username: form.username, password: form.password,
        name: form.name, role: form.role, email: form.email, phone: form.phone
      })
      ElMessage.success('用户创建成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (e) {
    console.error('保存用户失败', e)
  } finally {
    saving.value = false
  }
}

// 删除
async function handleDelete(row) {
  try {
    await api.delete(`/api/admin/users/${row.user_id}`)
    ElMessage.success('用户已删除')
    await loadUsers()
  } catch (e) {
    console.error('删除失败', e)
  }
}

// 重置密码
const pwdVisible = ref(false)
const pwdFormRef = ref(null)
const pwdForm = reactive({ new_password: '', confirm: '', _userId: '' })
const pwdRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (rule, value, cb) => value === pwdForm.new_password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' }
  ]
}

function openPassword(row) {
  pwdForm.new_password = ''
  pwdForm.confirm = ''
  pwdForm._userId = row.user_id
  pwdVisible.value = true
}

async function handlePassword() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await api.put(`/api/admin/users/${pwdForm._userId}/password`, { new_password: pwdForm.new_password })
    ElMessage.success('密码已重置')
    pwdVisible.value = false
  } catch (e) {
    console.error('密码重置失败', e)
  } finally {
    saving.value = false
  }
}

// 角色显示
function roleType(role) {
  return { admin: 'danger', pv_specialist: 'warning', cra: 'primary' }[role] || 'info'
}
function roleLabel(role) {
  return { admin: '管理员', pv_specialist: 'PV专员', cra: 'CRA' }[role] || role
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
  align-items: center;
}
</style>
