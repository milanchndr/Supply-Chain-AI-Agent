<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- Left Side - Welcome Section -->
      <div class="welcome-section">
        <div class="welcome-content">
          <div class="welcome-text">
            <h3>Welcome</h3>
          </div>
          
          <!-- Layered Icon Illustration -->
          <div class="illustration-container">
            <div class="layered-icon">
              <div class="layer layer-1"></div>
              <div class="layer layer-2"></div>
              <div class="layer layer-3"></div>
            </div>
          </div>
          
          <div class="subtitle">
            <p>INTRODUCING AI SUPPLY CHAIN SYSTEM</p>
          </div>
        </div>
        
        <!-- Geometric Background Elements -->
        <div class="geometric-bg">
          <div class="shape shape-1"></div>
          <div class="shape shape-2"></div>
          <div class="shape shape-3"></div>
        </div>
      </div>

      <!-- Right Side - Login Form -->
      <div class="form-section">
        <div class="form-content">
          <h2 class="form-title">LOGIN</h2>
          
          <form @submit.prevent="login" class="login-form">
            <div class="input-group">
              <label for="username">Username</label>
              <div class="input-wrapper">
                <input 
                  type="text" 
                  id="username" 
                  v-model="username" 
                  :disabled="isLoading"
                  @focus="focusedField = 'username'"
                  @blur="focusedField = null"
                />
                <div class="input-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </div>
            </div>

            <div class="input-group">
              <label for="password">Password</label>
              <div class="input-wrapper">
                <input 
                  type="password" 
                  id="password" 
                  v-model="password" 
                  :disabled="isLoading"
                  @focus="focusedField = 'password'"
                  @blur="focusedField = null"
                />
                <div class="input-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              class="login-button"
              :class="{ 'loading': isLoading }"
              :disabled="isLoading || !username || !password"
            >
              <span v-if="!isLoading">Login</span>
              <div v-else class="loading-content">
                <div class="spinner"></div>
                <span>Logging in...</span>
              </div>
            </button>
          </form>

          <transition name="status-slide">
            <div v-if="loginStatus" class="status-message" :class="statusClass">
              {{ loginStatus }}
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'LoginPage',
  data() {
    return {
      username: '',
      password: '',
      loginStatus: '',
      isLoading: false,
      focusedField: null,
      backendUrl: 'http://localhost:5000',
    };
  },
  computed: {
    statusClass() {
      return {
        'success': this.loginStatus.includes('Success'),
        'error': this.loginStatus.includes('Error')
      };
    }
  },
  methods: {
    async login() {
      this.loginStatus = '';
      this.isLoading = true;
      
      try {
        const response = await axios.post(`${this.backendUrl}/login`, {
          username: this.username,
          password: this.password,
        });
        
        const accessToken = response.data.access_token;
        localStorage.setItem('accessToken', accessToken);
        this.loginStatus = 'Login Success!';
        
        console.log('Login successful:', response.data);
        
        setTimeout(() => {
          this.$router.push('/query');
        }, 1500);
        
      } catch (error) {
        this.loginStatus = 'Login Error: ' + (error.response?.data?.error || error.message);
        console.error('Login failed:', error.response?.data || error);
        localStorage.removeItem('accessToken');
      } finally {
        this.isLoading = false;
      }
    }
  },
  
  mounted() {
    if (localStorage.getItem('accessToken')) {
      this.$router.push('/query');
    }
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');

* {
  box-sizing: border-box;
}

.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #a8e6cf 0%, #dcedc1 50%, #ffd3a5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
}

.login-wrapper {
  background: white;
  border-radius: 24px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(255, 255, 255, 0.5);
  overflow: hidden;
  display: flex;
  max-width: 900px;
  width: 100%;
  min-height: 580px;
  animation: slideIn 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Left Side - Welcome Section */
.welcome-section {
  flex: 1;
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  overflow: hidden;
}

.welcome-content {
  text-align: center;
  z-index: 2;
  position: relative;
}

.welcome-text {
  margin-bottom: 40px;
  animation: fadeInUp 1s ease-out 0.3s both;
}

.welcome-text h3 {
  font-size: 32px;
  font-weight: 300;
  color: white;
  margin: 0;
  letter-spacing: 2px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  position: absolute;
  left: -120px;
  top: 50%;
  transform: translateY(-50%);
  font-family: 'Montserrat', sans-serif;
}

/* Layered Icon Illustration */
.illustration-container {
  margin-bottom: 50px;
  animation: fadeInUp 1s ease-out 0.6s both;
}

.layered-icon {
  position: relative;
  width: 120px;
  height: 90px;
  margin: 0 auto;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

.layer {
  position: absolute;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.layer-1 {
  width: 120px;
  height: 75px;
  background: rgba(255, 255, 255, 0.95);
  top: 15px;
  left: 0;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  animation: layerSlide1 2s ease-out 0.5s both;
}

.layer-2 {
  width: 110px;
  height: 70px;
  background: rgba(255, 255, 255, 0.9);
  top: 10px;
  left: 5px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  animation: layerSlide2 2s ease-out 0.7s both;
}

.layer-3 {
  width: 100px;
  height: 65px;
  background: rgba(255, 255, 255, 0.85);
  top: 5px;
  left: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  animation: layerSlide3 2s ease-out 0.9s both;
}

@keyframes layerSlide1 {
  from {
    opacity: 0;
    transform: translateX(30px) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0) translateY(0);
  }
}

@keyframes layerSlide2 {
  from {
    opacity: 0;
    transform: translateX(20px) translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateX(0) translateY(0);
  }
}

@keyframes layerSlide3 {
  from {
    opacity: 0;
    transform: translateX(10px) translateY(0px);
  }
  to {
    opacity: 1;
    transform: translateX(0) translateY(0);
  }
}

.layered-icon:hover .layer-1 {
  transform: translateX(-3px) translateY(-2px);
}

.layered-icon:hover .layer-2 {
  transform: translateX(-1px) translateY(-1px);
}

.layered-icon:hover .layer-3 {
  transform: translateX(1px) translateY(1px);
}

.subtitle {
  animation: fadeInUp 1s ease-out 0.9s both;
}

.subtitle p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 1.5px;
  margin: 0;
  font-family: 'Montserrat', sans-serif;
}

/* Geometric Background */
.geometric-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.shape {
  position: absolute;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.shape-1 {
  width: 120px;
  height: 120px;
  top: 10%;
  right: -60px;
  animation: rotate 20s linear infinite;
}

.shape-2 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  left: -40px;
  animation: rotate 15s linear infinite reverse;
}

.shape-3 {
  width: 200px;
  height: 200px;
  top: 60%;
  right: -100px;
  animation: rotate 25s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Right Side - Form Section */
.form-section {
  flex: 1;
  padding: 60px 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-content {
  width: 100%;
  max-width: 320px;
  animation: fadeInRight 0.8s ease-out 0.4s both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.form-title {
  font-size: 28px;
  font-weight: 600;
  color: #4ecdc4;
  margin: 0 0 40px 0;
  letter-spacing: 1px;
  font-family: 'Montserrat', sans-serif;
}

.login-form {
  margin-bottom: 30px;
}

.input-group {
  margin-bottom: 25px;
  position: relative;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Montserrat', sans-serif;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 15px 45px 15px 15px;
  border: 2px solid #f0f0f0;
  border-radius: 8px;
  font-size: 16px;
  background: #fafafa;
  transition: all 0.3s ease;
  outline: none;
  font-family: 'Poppins', sans-serif;
  font-weight: 400;
}

.input-wrapper input:focus {
  border-color: #4ecdc4;
  background: white;
  box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
}

.input-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #ccc;
  transition: color 0.3s ease;
}

.input-wrapper input:focus + .input-icon {
  color: #4ecdc4;
}

.login-button {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 10px;
  position: relative;
  overflow: hidden;
  font-family: 'Poppins', sans-serif;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(78, 205, 196, 0.3);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.link {
  color: #4ecdc4;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.3s ease;
  font-family: 'Poppins', sans-serif;
}

.link:hover {
  opacity: 0.7;
}

.status-message {
  margin-top: 20px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  font-family: 'Poppins', sans-serif;
}

.status-message.success {
  background: rgba(78, 205, 196, 0.1);
  color: #44a08d;
  border: 1px solid rgba(78, 205, 196, 0.3);
}

.status-message.error {
  background: rgba(255, 107, 107, 0.1);
  color: #e74c3c;
  border: 1px solid rgba(255, 107, 107, 0.3);
}

.status-slide-enter-active,
.status-slide-leave-active {
  transition: all 0.3s ease;
}

.status-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.status-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
    max-width: 400px;
  }
  
  .welcome-section {
    padding: 40px 30px;
    min-height: 300px;
  }
  
  .welcome-text h3 {
    position: static;
    writing-mode: initial;
    text-orientation: initial;
    font-size: 24px;
    margin-bottom: 20px;
  }
  
  .form-section {
    padding: 40px 30px;
  }
  
  .layered-icon {
    width: 100px;
    height: 75px;
  }
  
  .layer-1 {
    width: 100px;
    height: 60px;
  }
  
  .layer-2 {
    width: 90px;
    height: 55px;
  }
  
  .layer-3 {
    width: 80px;
    height: 50px;
  }
}
</style>