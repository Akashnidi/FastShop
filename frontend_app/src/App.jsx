import { useState, useEffect } from 'react'
import { authService, cartService } from './services/api'
import Login from './components/Login'
import ProductList from './components/ProductList'
import Cart from './components/Cart'
import Checkout from './components/Checkout'
import { LogOut, ShoppingCart, Home, CheckCircle } from 'lucide-react'

export default function App() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Navigation state
  const [currentPage, setCurrentPage] = useState('home')

  // Cart state
  const [cart, setCart] = useState({ items: [], total_price: 0, cart_id: null })
  const [cartLoading, setCartLoading] = useState(false)

  // Initialize auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = authService.getToken()
      if (token) {
        const isValid = await authService.validateToken(token)
        if (isValid) {
          const userId = authService.getUserId()
          const username = localStorage.getItem('username')
          setUser({ user_id: userId, username })
          setIsAuthenticated(true)
          // Load cart for authenticated user
          loadCart(userId)
        } else {
          authService.logout()
          setIsAuthenticated(false)
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [])

  const loadCart = async (userId) => {
    setCartLoading(true)
    const result = await cartService.getCart(userId)
    if (result.success) {
      setCart(result.data)
    }
    setCartLoading(false)
  }

  const handleLoginSuccess = async (userData) => {
    setUser(userData)
    setIsAuthenticated(true)
    setCurrentPage('home')
    await loadCart(userData.user_id)
  }

  const handleLogout = () => {
    authService.logout()
    setUser(null)
    setIsAuthenticated(false)
    setCart({ items: [], total_price: 0, cart_id: null })
    setCurrentPage('home')
  }

  const handleCartUpdate = (updatedCart) => {
    setCart(updatedCart)
  }

  const handleCheckoutComplete = () => {
    setCart({ items: [], total_price: 0 })
    setCurrentPage('home')
    // Reload cart
    if (user) {
      loadCart(user.user_id)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    )
  }

  // Login page
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  // Main app
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <ShoppingCart className="text-blue-600" size={28} />
              <h1 className="text-xl font-bold text-blue-600">FastShop</h1>
            </div>

            {/* Nav Links */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setCurrentPage('home')}
                className={`flex items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                  currentPage === 'home'
                    ? 'bg-blue-100 text-blue-600 font-semibold'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Home size={18} />
                <span className="hidden sm:inline">Shop</span>
              </button>

              <button
                onClick={() => setCurrentPage('cart')}
                className={`flex items-center gap-1 px-3 py-2 rounded-lg transition-colors relative ${
                  currentPage === 'cart'
                    ? 'bg-blue-100 text-blue-600 font-semibold'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <ShoppingCart size={18} />
                <span className="hidden sm:inline">Cart</span>
                {cart.items.length > 0 && (
                  <span className="absolute top-0 right-0 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {cart.items.length}
                  </span>
                )}
              </button>

              {/* User Info */}
              <div className="border-l border-gray-300 pl-4 flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-semibold text-gray-800">
                    {user?.username}
                  </p>
                  <p className="text-xs text-gray-600">User #{user?.user_id}</p>
                </div>

                <button
                  onClick={handleLogout}
                  className="text-red-600 hover:text-red-800 p-2 rounded-lg hover:bg-red-50 transition-colors"
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentPage === 'home' && (
          <ProductList
            userId={user?.user_id}
            onCartUpdate={handleCartUpdate}
          />
        )}

        {currentPage === 'cart' && cart.items.length > 0 && (
          <Cart
            userId={user?.user_id}
            cartData={cart}
            onCartUpdate={handleCartUpdate}
            onCheckout={() => setCurrentPage('checkout')}
          />
        )}

        {currentPage === 'cart' && cart.items.length === 0 && (
          <div className="card text-center py-12">
            <ShoppingCart className="mx-auto text-gray-400 mb-4" size={48} />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Your cart is empty
            </h2>
            <p className="text-gray-600 mb-6">
              Start adding products from our catalog
            </p>
            <button
              onClick={() => setCurrentPage('home')}
              className="btn-primary"
            >
              Continue Shopping
            </button>
          </div>
        )}

        {currentPage === 'checkout' && (
          <Checkout
            userId={user?.user_id}
            cartId={cart.cart_id}
            cartTotal={cart.total_price}
            cartItems={cart.items}
            onCheckoutComplete={handleCheckoutComplete}
            onCancel={() => setCurrentPage('cart')}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* About */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">FastShop</h3>
              <p className="text-sm text-gray-600">
                A lightweight e-commerce platform built with microservices
                architecture for optimal performance on limited resources.
              </p>
            </div>

            {/* Services */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Services</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>✓ Identity Hub (Auth)</li>
                <li>✓ Product Hub (Catalog)</li>
                <li>✓ Transaction Hub (Orders)</li>
              </ul>
            </div>

            {/* Tech Stack */}
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Tech Stack</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• FastAPI + aiosqlite</li>
                <li>• React 18 + Vite</li>
                <li>• TailwindCSS</li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-200 mt-8 pt-8 text-center">
            <p className="text-sm text-gray-600">
              © 2026 FastShop. Phase 5 Complete — Microservices E-Commerce
              Demo.
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Optimized for 6GB RAM systems with Docker Compose orchestration.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
