<template>
  <div class="security-page">
    <el-tabs v-model="activeTab" class="security-tabs">
      <!-- 登录日志 -->
      <el-tab-pane label="登录日志" name="login-logs">
        <div class="filter-bar">
          <el-input v-model="loginFilters.ip_address" placeholder="IP 地址" clearable style="width: 180px" />
          <el-select v-model="loginFilters.status" placeholder="状态" clearable style="width: 120px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-button @click="loadLoginLogs">搜索</el-button>
        </div>

        <el-table :data="loginLogs" v-loading="loginLoading" stripe class="login-logs-table">
          <el-table-column prop="ip_address" label="IP 地址" width="140" />
          <el-table-column prop="user_agent" label="User Agent" width="200" show-overflow-tooltip />
          <el-table-column prop="login_time" label="登录时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.login_time).toLocaleString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fail_reason" label="失败原因" show-overflow-tooltip />
        </el-table>

        <el-pagination
          v-model:current-page="loginPage"
          :page-size="20"
          :total="loginTotal"
          layout="total, prev, pager, next"
          @current-change="loadLoginLogs"
          style="margin-top: 20px; justify-content: center"
        />
      </el-tab-pane>

      <!-- IP 黑名单 -->
      <el-tab-pane label="IP 黑名单" name="ip-bans">
        <div class="filter-bar">
          <el-button type="primary" @click="showBanDialog = true">
            <el-icon><Plus /></el-icon> 添加封禁
          </el-button>
          <el-checkbox v-model="showActiveOnly" @change="loadIPBans" style="margin-left: 16px">
            仅显示生效中
          </el-checkbox>
        </div>

        <el-table :data="ipBans" v-loading="banLoading" stripe class="ip-bans-table">
          <el-table-column prop="ip_address" label="IP 地址" width="140" />
          <el-table-column prop="reason" label="封禁原因" show-overflow-tooltip />
          <el-table-column prop="banned_by" label="操作人" width="120" />
          <el-table-column prop="banned_at" label="封禁时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.banned_at).toLocaleString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column prop="expires_at" label="到期时间" width="180">
            <template #default="{ row }">
              {{ row.expires_at ? new Date(row.expires_at).toLocaleString('zh-CN') : '永久' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'danger' : 'info'" size="small">
                {{ row.is_active ? '生效中' : '已过期' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" size="small" link @click="unbanIP(row.ip_address)">
                解封
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="banPage"
          :page-size="20"
          :total="banTotal"
          layout="total, prev, pager, next"
          @current-change="loadIPBans"
          style="margin-top: 20px; justify-content: center"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 添加封禁对话框 -->
    <el-dialog v-model="showBanDialog" title="添加 IP 封禁" width="500px">
      <el-form :model="banForm" label-width="100px">
        <el-form-item label="IP 地址" required>
          <el-input v-model="banForm.ip_address" placeholder="例如: 192.168.1.1" />
        </el-form-item>
        <el-form-item label="封禁原因">
          <el-input v-model="banForm.reason" type="textarea" rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-select v-model="banForm.expires_in_minutes" placeholder="永久有效" clearable style="width: 100%">
            <el-option label="永久" :value="null" />
            <el-option label="15 分钟" :value="15" />
            <el-option label="1 小时" :value="60" />
            <el-option label="6 小时" :value="360" />
            <el-option label="24 小时" :value="1440" />
            <el-option label="7 天" :value="10080" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBanDialog = false">取消</el-button>
        <el-button type="primary" @click="banIP" :loading="banSubmitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const activeTab = ref('login-logs')

// Login logs
const loginLogs = ref([])
const loginLoading = ref(false)
const loginPage = ref(1)
const loginTotal = ref(0)
const loginFilters = reactive({ ip_address: '', status: '' })

// IP bans
const ipBans = ref([])
const banLoading = ref(false)
const banPage = ref(1)
const banTotal = ref(0)
const showActiveOnly = ref(true)
const showBanDialog = ref(false)
const banSubmitting = ref(false)
const banForm = reactive({ ip_address: '', reason: '', expires_in_minutes: null })

onMounted(() => {
  loadLoginLogs()
  loadIPBans()
})

async function loadLoginLogs() {
  loginLoading.value = true
  try {
    const params = { skip: (loginPage.value - 1) * 20, limit: 20 }
    if (loginFilters.ip_address) params.ip_address = loginFilters.ip_address
    if (loginFilters.status) params.status = loginFilters.status
    const response = await client.get('/security/login-logs', { params })
    loginLogs.value = response.data
    loginTotal.value = response.data.length
  } catch (error) {
    ElMessage.error('加载登录日志失败')
  } finally {
    loginLoading.value = false
  }
}

async function loadIPBans() {
  banLoading.value = true
  try {
    const params = { skip: (banPage.value - 1) * 20, limit: 20, active_only: showActiveOnly.value }
    const response = await client.get('/security/ip-bans', { params })
    ipBans.value = response.data
    banTotal.value = response.data.length
  } catch (error) {
    ElMessage.error('加载 IP 黑名单失败')
  } finally {
    banLoading.value = false
  }
}

async function banIP() {
  if (!banForm.ip_address) {
    ElMessage.warning('请输入 IP 地址')
    return
  }
  banSubmitting.value = true
  try {
    await client.post('/security/ip-bans', {
      ip_address: banForm.ip_address,
      reason: banForm.reason,
      expires_in_minutes: banForm.expires_in_minutes,
    })
    ElMessage.success('IP 封禁成功')
    showBanDialog.value = false
    banForm.ip_address = ''
    banForm.reason = ''
    banForm.expires_in_minutes = null
    loadIPBans()
  } catch (error) {
    ElMessage.error('添加封禁失败')
  } finally {
    banSubmitting.value = false
  }
}

async function unbanIP(ip_address) {
  try {
    await ElMessageBox.confirm(`确定要解封 IP ${ip_address} 吗？`, '确认', { type: 'warning' })
    await client.delete(`/security/ip-bans/${ip_address}`)
    ElMessage.success('解封成功')
    loadIPBans()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('解封失败')
  }
}
</script>

<style scoped>
.security-page { max-width: 1200px; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.login-logs-table, .ip-bans-table { margin-top: 12px; }
</style>
