import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
    },
    {
      path: '/lobby',
      name: 'lobby',
      component: () => import('./views/LobbyView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/recruit',
      name: 'recruit',
      component: () => import('./views/CreateRecruitmentView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/room/:id',
      name: 'room',
      component: () => import('./views/RoomView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/room/:id/feedback',
      name: 'feedback',
      component: () => import('./views/FeedbackView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    const auth = useAuthStore()
    if (!auth.user) {
      await auth.fetchMe()
    }
    if (!auth.user) {
      return { name: 'login' }
    }
  }
})

export default router
