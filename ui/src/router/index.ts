import { createRouter, createWebHistory } from 'vue-router';
// 由于组件没有默认导出，使用具名导入
import IntermediateQuestionPage from '../components/IntermediateQuestionPage.vue';
import GuideView from '../views/GuideView.vue';
import App from '../App.vue';

const routes = [
  {
    path: '/',
    name: 'Guide',
    component: GuideView
  },
  {
    path: '/faith',
    name: 'Faith',
    component: App
  },
  {
    path: '/intermediate-question/:question',
    name: 'IntermediateQuestionPage',
    component: IntermediateQuestionPage,
    props: true
  }
];

const router = createRouter({
  history: createWebHistory('/faith/'),
  routes
});

export default router;