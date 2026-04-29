import { useState, useEffect } from 'react'
import { cartService } from '../services/api'
import { Trash2, AlertCircle, Loader } from 'lucide-react'

export default function Cart({ userId, cartData, onCartUpdate, onCheckout }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [removingItem, setRemovingItem] = useState(null)

  const handleRemoveItem = async (productId) => {
    setRemovingItem(productId)
    const result = await cartService.removeFromCart(userId, productId)

    if (result.success) {
      onCartUpdate(result.data)
      setError('')
    } else {
      setError(result.error)
    }

    setRemovingItem(null)
  }

  const handleClearCart = async () => {
    if (!confirm('Are you sure you want to clear your cart?')) return

    setLoading(true)
    const result = await cartService.clearCart(userId)

    if (result.success) {
      onCartUpdate({ items: [], total_price: 0 })
      setError('')
    } else {
      setError(result.error)
    }

    setLoading(false)
  }

  const items = cartData?.items || []
  const total = cartData?.total_price || 0
  const isEmpty = items.length === 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Shopping Cart</h2>
        <p className="text-gray-600">
          {isEmpty ? 'Your cart is empty' : `${items.length} item(s) in cart`}
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-danger flex items-center gap-2">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {isEmpty ? (
        <div className="card text-center py-12">
          <p className="text-gray-600 text-lg">Your cart is empty</p>
          <p className="text-gray-500 text-sm mt-2">
            Add some products to get started
          </p>
        </div>
      ) : (
        <>
          {/* Cart Items */}
          <div className="space-y-4">
            {items.map((item) => (
              <div
                key={item.product_id}
                className="card flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
              >
                {/* Item Details */}
                <div className="flex-grow">
                  <h3 className="font-semibold text-gray-800">
                    Product #{item.product_id}
                  </h3>
                  <div className="text-sm text-gray-600 mt-2 space-y-1">
                    <p>
                      Unit Price:{' '}
                      <span className="font-medium text-blue-600">
                        ${item.unit_price.toFixed(2)}
                      </span>
                    </p>
                    <p>
                      Quantity:{' '}
                      <span className="font-medium">{item.quantity}</span>
                    </p>
                  </div>
                </div>

                {/* Item Total */}
                <div className="text-right flex items-center gap-4">
                  <div>
                    <p className="text-2xl font-bold text-blue-600">
                      ${item.subtotal.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Subtotal</p>
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => handleRemoveItem(item.product_id)}
                    disabled={removingItem === item.product_id}
                    className="btn-danger btn-sm"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Cart Summary */}
          <div className="card bg-blue-50 border border-blue-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <p className="text-sm text-gray-600 mb-2">Cart Total</p>
                <p className="text-3xl font-bold text-blue-600">
                  ${total.toFixed(2)}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 flex-col sm:flex-row">
                <button
                  onClick={handleClearCart}
                  disabled={loading}
                  className="btn-secondary"
                >
                  Clear Cart
                </button>
                <button
                  onClick={onCheckout}
                  disabled={loading || isEmpty}
                  className="btn-primary flex items-center justify-center gap-2"
                >
                  {loading ? 'Processing...' : 'Proceed to Checkout'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
