/**
 * usePageState — 页面级 loading/error/empty 三态管理
 *
 * 用法:
 *   const { loading, error, empty, withLoading, setEmpty } = usePageState()
 *   await withLoading(() => api.get('/xxx'))
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function usePageState() {
  const loading = ref(false)
  const error = ref(null)  // { message: string } | null
  const empty = ref(false)

  async function withLoading(fn) {
    loading.value = true
    error.value = null
    try {
      const result = await fn()
      return result
    } catch (e) {
      const msg = e.response?.data?.message || e.message || '请求失败'
      error.value = { message: msg }
      ElMessage.error(msg)
      throw e
    } finally {
      loading.value = false
    }
  }

  function setEmpty(val) {
    empty.value = val
  }

  return { loading, error, empty, withLoading, setEmpty }
}
