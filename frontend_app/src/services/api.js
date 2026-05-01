import axios from 'axios'

// API Base URLs (production endpoints with 98.70.33.254)
const IDENTITY_API_URL = import.meta.env.VITE_API_IDENTITY_URL || 'http://98.70.33.254:8001'
const PRODUCT_API_URL = import.meta.env.VITE_API_PRODUCT_URL || 'http://98.70.33.254:8002'
const TRANSACTION_API_URL = import.meta.env.VITE_API_TRANSACTION_URL || 'http://98.70.33.254:8003'

// ============================================================================
// IDENTITY HUB CLIENT
// ============================================================================

const identityAPI = axios.create({
  baseURL: IDENTITY_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const authService = {
  register: async (username, email, password) => {
    try {
      const response = await identityAPI.post('/auth/register', {
        username,
        email,
        password,
      })
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      }
    }
  },

  login: async (email, password) => {
    try {
      const response = await identityAPI.post('/auth/login', {
        email,
        password,
      })
      // Store token in localStorage
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('user_id', response.data.user_id)
      localStorage.setItem('username', response.data.username)
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      }
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token')
  },

  getToken: () => {
    return localStorage.getItem('token')
  },

  getUserId: () => {
    return parseInt(localStorage.getItem('user_id'))
  },

  validateToken: async (token) => {
    try {
      const response = await identityAPI.get('/auth/validate', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      return response.data.valid
    } catch (error) {
      return false
    }
  },
}

// ============================================================================
// PRODUCT HUB CLIENT
// ============================================================================

const productAPI = axios.create({
  baseURL: PRODUCT_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const productService = {
  getAllProducts: async (limit = 100, offset = 0) => {
    try {
      const response = await productAPI.get('/products', {
        params: { limit, offset },
      })
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch products',
        data: [],
      }
    }
  },

  getProduct: async (productId) => {
    try {
      const response = await productAPI.get(`/products/${productId}`)
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Product not found',
      }
    }
  },

  checkStock: async (productId, quantity = 1) => {
    try {
      const response = await productAPI.get(`/products/${productId}/stock`, {
        params: { quantity },
      })
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Stock check failed',
      }
    }
  },
}

// ============================================================================
// TRANSACTION HUB CLIENT
// ============================================================================

const transactionAPI = axios.create({
  baseURL: TRANSACTION_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const cartService = {
  getCart: async (userId) => {
    try {
      const response = await transactionAPI.get(`/cart/${userId}`)
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch cart',
        data: { items: [], total_price: 0 },
      }
    }
  },

  addToCart: async (userId, productId, quantity) => {
    try {
      const response = await transactionAPI.post(`/cart/${userId}/items`, {
        product_id: productId,
        quantity,
      })
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to add to cart',
      }
    }
  },

  removeFromCart: async (userId, productId) => {
    try {
      const response = await transactionAPI.delete(
        `/cart/${userId}/items/${productId}`
      )
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to remove from cart',
      }
    }
  },

  clearCart: async (userId) => {
    try {
      await transactionAPI.delete(`/cart/${userId}`)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to clear cart',
      }
    }
  },
}

export const checkoutService = {
  checkout: async (userId, cartId) => {
    try {
      const response = await transactionAPI.post('/checkout', {
        user_id: userId,
        cart_id: cartId,
      })
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error:
          error.response?.data?.detail ||
          'Checkout failed. Please try again.',
      }
    }
  },

  getOrder: async (orderId) => {
    try {
      const response = await transactionAPI.get(`/orders/${orderId}`)
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch order',
      }
    }
  },

  getUserOrders: async (userId, limit = 50, offset = 0) => {
    try {
      const response = await transactionAPI.get(
        `/orders/user/${userId}`,
        {
          params: { limit, offset },
        }
      )
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to fetch orders',
        data: [],
      }
    }
  },
}

export default {
  authService,
  productService,
  cartService,
  checkoutService,
}
