import { createApp } from 'vue'
import RootApp from './RootApp.vue'
import router from './router'
import BootstrapVue3 from 'bootstrap-vue-3'
import * as echarts from 'echarts'
import { createPinia } from 'pinia'

// 导入样式
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-3/dist/bootstrap-vue-3.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

const app = createApp(RootApp)
const pinia = createPinia()
app.use(pinia)

// 全局挂载 echarts
app.config.globalProperties.$echarts = echarts

// 使用插件
app.use(router)
app.use(BootstrapVue3)

app.mount('#app')