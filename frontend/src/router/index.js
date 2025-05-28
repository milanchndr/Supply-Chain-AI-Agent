// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/LoginPage.vue';
import QueryPage from '../views/QueryPage.vue';

const routes = [
  {
    path: '/',
    name: 'Login',
    component: LoginPage,
    meta: { requiresAuth: false }
  },
  {
    path: '/query',
    name: 'Query',
    component: QueryPage,
    meta: { requiresAuth: true }
  },
  // You can add a catch-all route for 404 errors
  {
    path: '/:pathMatch(.*)*',
    redirect: '/' // Redirect to login page for any unmatched routes
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

// Global Navigation Guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('accessToken');

  if (to.meta.requiresAuth && !isAuthenticated) {
    // If the route requires auth and user is not authenticated, redirect to login
    next('/');
  } else if (to.name === 'Login' && isAuthenticated) {
    // If user is already authenticated and tries to go to login, redirect to query page
    next('/query');
  } else {
    // Otherwise, allow navigation
    next();
  }
});


export default router;