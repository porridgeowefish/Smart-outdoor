/**
 * 前端路由配置。
 *
 * 页面结构：
 * - /login, /register —— 独立页面（无底部导航栏）
 * - /routes/:id, /plans/:id —— 详情页（无底部导航栏）
 * - / 下所有子页面 —— MainLayout 包裹（含底部导航栏）
 *   - /chat (默认页), /plans, /routes, /profile
 *
 * 带 meta.requiresAuth 的页面需要登录才能访问，未登录时重定向到 /login。
 */

import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import Chat from '../views/Chat.vue'
import Plans from '../views/Plans.vue'
import Routes from '../views/Routes.vue'
import RouteDetail from '../views/RouteDetail.vue'
import PlanDetail from '../views/PlanDetail.vue'
import { hasAuthToken } from '../api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/register',
      name: 'register',
      component: Register
    },
    {
      path: '/routes/:id',
      name: 'route-detail',
      component: RouteDetail,
      meta: { requiresAuth: true }
    },
    {
      path: '/plans/:id',
      name: 'plan-detail',
      component: PlanDetail,
      meta: { requiresAuth: true }
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/chat',
      children: [
        {
          path: 'chat',
          name: 'chat',
          component: Chat,
          meta: { requiresAuth: true }
        },
        {
          path: 'plans',
          name: 'plans',
          component: Plans,
          meta: { requiresAuth: true }
        },
        {
          path: 'routes',
          name: 'routes',
          component: Routes,
          meta: { requiresAuth: true }
        },
        {
          path: 'profile',
          name: 'profile',
          component: Profile,
          meta: { requiresAuth: true }
        }
      ]
    }
  ]
})

// 全局前置守卫：需要认证的页面在未登录时重定向到登录页，并携带原始路径以便登录后回跳
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !hasAuthToken()) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})

export default router
