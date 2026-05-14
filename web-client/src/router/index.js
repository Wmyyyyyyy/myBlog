import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/blogs',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/blogs',
    name: 'BlogList',
    component: () => import('@/views/BlogList.vue'),
  },
  {
    path: '/blogs/new',
    name: 'BlogCreate',
    component: () => import('@/views/BlogEditor.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/blogs/:id',
    name: 'BlogDetail',
    component: () => import('@/views/BlogDetail.vue'),
  },
  {
    path: '/blogs/:id/edit',
    name: 'BlogEdit',
    component: () => import('@/views/BlogEditor.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
  },
  {
    path: '/foundation',
    name: 'Foundation',
    component: () => import('@/views/FoundationView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dynamics',
    name: 'Dynamics',
    component: () => import('@/views/DynamicsView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isLoggedIn = authStore.isLoggedIn

  if (to.meta.guest && isLoggedIn) {
    next('/blogs')
  } else if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
