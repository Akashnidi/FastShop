import { useState } from 'react'
import { authService } from '../services/api'
import { User, Mail, Lock, AlertCircle, CheckCircle } from 'lucide-react'

export default function Login({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  })

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
    setError('')
    setSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      let result
      if (isLogin) {
        if (!formData.email || !formData.password) {
          throw new Error('Email and password are required')
        }
        result = await authService.login(formData.email, formData.password)
      } else {
        if (!formData.username || !formData.email || !formData.password) {
          throw new Error('All fields are required')
        }
        if (formData.password.length < 8) {
          throw new Error('Password must be at least 8 characters')
        }
        result = await authService.register(
          formData.username,
          formData.email,
          formData.password
        )
      }

      if (result.success) {
        setSuccess(
          isLogin
            ? `Welcome back, ${result.data.username}!`
            : 'Registration successful! Logging you in...'
        )
        setFormData({ username: '', email: '', password: '' })
        setTimeout(() => {
          onLoginSuccess(result.data)
        }, 1500)
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="card shadow-xl">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-blue-600 mb-2">FastShop</h1>
            <p className="text-gray-600">
              {isLogin ? 'Sign in to your account' : 'Create a new account'}
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="alert alert-danger flex items-center gap-2 mb-4">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Success Alert */}
          {success && (
            <div className="alert alert-success flex items-center gap-2 mb-4">
              <CheckCircle size={20} />
              <span>{success}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username - only for register */}
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <User className="inline mr-2" size={16} />
                  Username
                </label>
                <input
                  type="text"
                  name="username"
                  placeholder="Enter your username"
                  value={formData.username}
                  onChange={handleInputChange}
                  className="input-field"
                  required={!isLogin}
                />
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Mail className="inline mr-2" size={16} />
                Email
              </label>
              <input
                type="email"
                name="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleInputChange}
                className="input-field"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Lock className="inline mr-2" size={16} />
                Password
              </label>
              <input
                type="password"
                name="password"
                placeholder={isLogin ? 'Enter your password' : 'At least 8 characters'}
                value={formData.password}
                onChange={handleInputChange}
                className="input-field"
                required
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Toggle */}
          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin)
                  setError('')
                  setSuccess('')
                  setFormData({ username: '', email: '', password: '' })
                }}
                className="ml-1 font-semibold text-blue-600 hover:text-blue-800"
              >
                {isLogin ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-600 text-xs mt-8">
          Lightweight E-Commerce Platform | Phase 5 Demo
        </p>
      </div>
    </div>
  )
}
