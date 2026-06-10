<template>
  <div class="signals">
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>信号挖掘分析</span>
            </div>
          </template>
          <el-form :inline="true">
            <el-form-item label="药物名称">
              <el-input v-model="drugName" placeholder="如 XK-001" />
            </el-form-item>
            <el-form-item label="分析周期">
              <el-select v-model="analysisPeriod" placeholder="选择周期">
                <el-option label="最近30天" value="30d" />
                <el-option label="最近90天" value="90d" />
                <el-option label="最近180天" value="180d" />
                <el-option label="最近1年" value="1y" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="triggering" @click="triggerSignal">
                <el-icon><TrendCharts /></el-icon>
                触发分析
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>发生率趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>信号分布</span>
          </template>
          <div ref="pieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="table-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>信号列表</span>
              <el-button text type="primary" @click="loadSignals">刷新</el-button>
            </div>
          </template>
          <el-table :data="signals" stripe v-loading="loadingSignals" max-height="400">
            <el-table-column prop="signal_id" label="编号" width="160" />
            <el-table-column prop="drug_name" label="药物" width="100" />
            <el-table-column prop="signal_name" label="信号名" min-width="150" show-overflow-tooltip />
            <el-table-column prop="event_count" label="事件数" width="80" align="center" />
            <el-table-column prop="incidence_rate" label="发生率" width="90" align="center" />
            <el-table-column prop="background_rate" label="背景率" width="90" align="center" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'confirmed' ? 'danger' : row.status === 'monitoring' ? 'warning' : 'info'"
                  size="small"
                >
                  {{ row.status === 'confirmed' ? '已确认' : row.status === 'monitoring' ? '监测中' : '待确认' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="references" label="文献" min-width="150" show-overflow-tooltip />
          </el-table>
          <el-pagination
            v-model:current-page="signalPage"
            :total="signalTotal"
            layout="total, prev, pager, next"
            style="margin-top: 16px; justify-content: flex-end"
            @current-change="loadSignals"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../api'

const drugName = ref('XK-001')
const analysisPeriod = ref('30d')
const triggering = ref(false)

const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null

const signals = ref([])
const loadingSignals = ref(false)
const signalPage = ref(1)
const signalTotal = ref(0)

onMounted(() => {
  loadSignals()
  nextTick(() => {
    initCharts()
  })
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
})

function handleResize() {
  trendChart?.resize()
  pieChart?.resize()
}

function initCharts() {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['发生率', '背景率'] },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value', name: '发生率(%)' },
      series: [
        {
          name: '发生率',
          type: 'line',
          data: [0.5, 0.8, 1.2, 1.0, 1.5, 1.3],
          smooth: true,
          itemStyle: { color: '#f56c6c' },
          areaStyle: { color: 'rgba(245, 108, 108, 0.1)' }
        },
        {
          name: '背景率',
          type: 'line',
          data: [0.3, 0.4, 0.5, 0.4, 0.5, 0.5],
          smooth: true,
          itemStyle: { color: '#409EFF' },
          areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
        }
      ]
    })
  }

  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          label: { show: false },
          data: [
            { value: 15, name: '已确认信号' },
            { value: 28, name: '监测中信号' },
            { value: 42, name: '待确认信号' }
          ],
          color: ['#f56c6c', '#e6a23c', '#909399']
        }
      ]
    })
  }
}

function updateCharts() {
  if (trendChart) {
    trendChart.setOption({
      xAxis: { data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      series: [
        { data: [0.5, 0.8, 1.2, 1.0, 1.5, 1.3 + Math.random() * 0.5] },
        { data: [0.3, 0.4, 0.5, 0.4, 0.5, 0.5] }
      ]
    })
  }
}

async function triggerSignal() {
  if (!drugName.value) {
    ElMessage.warning('请输入药物名称')
    return
  }
  triggering.value = true
  try {
    await api.post('/api/signals/trigger', {
      drug_name: drugName.value,
      analysis_period: analysisPeriod.value
    })
    ElMessage.success('信号分析已触发')
    updateCharts()
    loadSignals()
  } catch (e) {
    ElMessage.error('信号分析失败')
  } finally {
    triggering.value = false
  }
}

async function loadSignals() {
  loadingSignals.value = true
  try {
    const res = await api.get('/api/signals/list', {
      params: { page: signalPage.value, page_size: 50 }
    })
    signals.value = res.data.items || []
    signalTotal.value = res.data.total || 0
  } catch (e) {
    console.error('加载信号列表失败', e)
  } finally {
    loadingSignals.value = false
  }
}
</script>

<style scoped>
.signals {
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
.chart-row {
  margin-top: 0;
}
.chart-container {
  width: 100%;
  height: 320px;
}
.table-row {
  margin-top: 0;
}
</style>