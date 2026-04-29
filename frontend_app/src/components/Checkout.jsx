import { useState } from 'react'
import { checkoutService } from '../services/api'
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react'

export default function Checkout({
  userId,
  cartId,
  cartTotal,
  cartItems,
  onCheckoutComplete,
  onCancel,
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [orderConfirmed, setOrderConfirmed] = useState(null)

  const handleConfirmCheckout = async () => {
    setLoading(true)
    setError('')

    const result = await checkoutService.checkout(userId, cartId)

    if (result.success) {
      setOrderConfirmed(result.data)
      setTimeout(() => {
        onCheckoutComplete(result.data)
      }, 3000)
    } else {
      setError(result.error)
    }

    setLoading(false)
  }

  if (orderConfirmed) {
    return (
      <div className="card bg-gradient-to-br from-green-50 to-emerald-50 border border-green-300">
        <div className="text-center space-y-4">
          <CheckCircle
            className="mx-auto text-green-600 animate-bounce"
            size={48}
          />
          <h2 className="text-2xl font-bold text-green-700">
            Order Confirmed!
          </h2>
          <p className="text-gray-700">
            Thank you for your purchase. Your order has been successfully
            processed.
          </p>

          {/* Order Details */}
          <div className="bg-white rounded-lg p-6 mt-6 space-y-3 text-left">
            <div className="flex justify-between">
              <span className="text-gray-600">Order ID:</span>
              <span className="font-semibold text-gray-800">
                #{orderConfirmed.order_id}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className="font-semibold text-green-600">
                {orderConfirmed.status.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Amount:</span>
              <span className="text-xl font-bold text-blue-600">
                ${orderConfirmed.total_price.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Timestamp:</span>
              <span className="text-sm text-gray-600">
                {new Date(orderConfirmed.timestamp).toLocaleString()}
              </span>
            </div>
          </div>

          <p className="text-sm text-gray-600 mt-4">
            Redirecting back to shopping in 3 seconds...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="card max-w-2xl mx-auto">
      {/* Header */}
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Order Summary</h2>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-danger flex items-center gap-2 mb-6">
          <AlertCircle size={20} />
          <div>
            <p className="font-semibold">Stock Verification Failed</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Order Items */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-4">Items</h3>
        <div className="space-y-3 bg-gray-50 rounded-lg p-4">
          {cartItems.map((item) => (
            <div
              key={item.product_id}
              className="flex justify-between text-sm"
            >
              <span className="text-gray-700">
                Product #{item.product_id} × {item.quantity}
              </span>
              <span className="font-semibold text-gray-800">
                ${item.subtotal.toFixed(2)}
              </span>
            </div>
          ))}
          <div className="border-t border-gray-300 pt-3 mt-3">
            <div className="flex justify-between font-bold text-gray-800">
              <span>Total:</span>
              <span className="text-xl text-blue-600">
                ${cartTotal.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Checkout Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">📦 Note:</span> Your order will be
          processed with real-time stock verification from our Product Hub.
          Click "Confirm Order" to proceed with the transaction.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={onCancel}
          disabled={loading}
          className="btn-secondary flex-1"
        >
          Back to Cart
        </button>
        <button
          onClick={handleConfirmCheckout}
          disabled={loading}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Processing...
            </>
          ) : (
            'Confirm Order'
          )}
        </button>
      </div>

      {/* Processing Info */}
      {loading && (
        <div className="mt-4 text-center text-sm text-gray-600">
          <p>Verifying stock with Product Hub...</p>
          <p className="text-xs text-gray-500 mt-1">
            This may take a few seconds
          </p>
        </div>
      )}
    </div>
  )
}
