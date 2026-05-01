import { useState, useEffect } from 'react'
import { productService, cartService } from '../services/api'
import { ShoppingCart, AlertCircle, Loader } from 'lucide-react'

export default function ProductList({ userId, onCartUpdate }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [quantities, setQuantities] = useState({})
  const [addingToCart, setAddingToCart] = useState({})

  useEffect(() => {
    loadProducts()
  }, [])

  const loadProducts = async () => {
    setLoading(true)
    setError('')
    const result = await productService.getAllProducts()
    if (result.success) {
      setProducts(result.data)
      // Initialize quantities
      const qty = {}
      result.data.forEach((p) => {
        qty[p.product_id] = 1
      })
      setQuantities(qty)
    } else {
      setError(result.error)
    }
    setLoading(false)
  }

  const handleQuantityChange = (productId, value) => {
    setQuantities((prev) => ({
      ...prev,
      [productId]: Math.max(1, parseInt(value) || 1),
    }))
  }

  const handleAddToCart = async (productId) => {
    const quantity = quantities[productId]
    setAddingToCart((prev) => ({ ...prev, [productId]: true }))

    const result = await cartService.addToCart(userId, productId, quantity)

    if (result.success) {
      onCartUpdate(result.data)
      // Reset quantity to 1
      setQuantities((prev) => ({
        ...prev,
        [productId]: 1,
      }))
    } else {
      setError(result.error)
    }

    setAddingToCart((prev) => ({ ...prev, [productId]: false }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="animate-spin text-blue-600" size={32} />
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Product Catalog</h2>
        <p className="text-gray-600">
          Browse our collection of {products.length} products
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-danger flex items-center gap-2 mb-6">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Products Grid */}
      {products.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600">No products available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => (
            <div key={product.product_id} className="card-hover">
              {/* Product Image */}
              <div className="mb-4 h-48 bg-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover hover:scale-105 transition-transform"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.parentElement.classList.add('bg-gray-300')
                    }}
                  />
                ) : (
                  <div className="text-gray-400 text-center">
                    <p className="text-sm">No image available</p>
                  </div>
                )}
              </div>

              {/* Product Header */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  {product.name}
                </h3>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {product.description || 'No description available'}
                </p>
              </div>

              {/* Stock Status */}
              <div className="mb-4">
                {product.stock > 0 ? (
                  <span className="badge badge-success">
                    In Stock ({product.stock})
                  </span>
                ) : (
                  <span className="badge badge-danger">Out of Stock</span>
                )}
              </div>

              {/* Price */}
              <div className="mb-4">
                <p className="text-2xl font-bold text-blue-600">
                  ${product.price.toFixed(2)}
                </p>
              </div>

              {/* Add to Cart Section */}
              {product.stock > 0 && (
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="1"
                    max={product.stock}
                    value={quantities[product.product_id] || 1}
                    onChange={(e) =>
                      handleQuantityChange(product.product_id, e.target.value)
                    }
                    className="w-16 px-2 py-2 border border-gray-300 rounded-lg text-center"
                  />
                  <button
                    onClick={() => handleAddToCart(product.product_id)}
                    disabled={addingToCart[product.product_id]}
                    className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <ShoppingCart size={18} />
                    {addingToCart[product.product_id] ? 'Adding...' : 'Add to Cart'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
