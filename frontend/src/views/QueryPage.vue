<template>
  <div class="chat-container">
    <!-- Header with logout -->
    <header class="chat-header">
      <div class="header-content">
        <div class="brand">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="brand-text">
            <h1>AI Supply Chain System</h1>
            <p>Intelligent Assistant</p>
          </div>
        </div>
        <button @click="logout" class="logout-btn">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 17L21 12L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Logout</span>
        </button>
      </div>
    </header>

    <!-- Chat Messages Area -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="conversationHistory.length === 0" class="welcome-screen">
        <div class="welcome-content">
          <div class="welcome-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/>
            </svg>
          </div>
          <h2>How can I help you today?</h2>
          <p>I'm your AI Supply Chain Assistant. Ask me about Organization Policy, SQL Query or Anything related to Supply Chain.</p>
          
          <div class="example-prompts">
            <div class="prompt-card" @click="setExampleQuery('What are the key performance indicators for measuring supplier performance as defined in our Performance Measurement policy?')">
              <div class="prompt-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 3V21H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M9 9L12 6L16 10L21 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="prompt-text">
                <h4>Performance Policy</h4>
                <p>Supply chain slow-moving inventory</p>
              </div>
            </div>
            
            <div class="prompt-card" @click="setExampleQuery('What is our company s definition of slow-moving inventory according to the Inventory Management policy? ')">
              <div class="prompt-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 16V8C20.9996 7.64928 20.9071 7.30481 20.7315 7.00116C20.556 6.69751 20.3037 6.44536 20 6.27L13 2.27C12.696 2.09446 12.3511 2.00205 12 2.00205C11.6489 2.00205 11.304 2.09446 11 2.27L4 6.27C3.69626 6.44536 3.44398 6.69751 3.26846 7.00116C3.09294 7.30481 3.00036 7.64928 3 8V16C3.00036 16.3507 3.09294 16.6952 3.26846 16.9988C3.44398 17.3025 3.69626 17.5546 4 17.73L11 21.73C11.304 21.9055 11.6489 21.9979 12 21.9979C12.3511 21.9979 12.696 21.9055 13 21.73L20 17.73C20.3037 17.5546 20.556 17.3025 20.7315 16.9988C20.9071 16.6952 20.9996 16.3507 21 16Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="prompt-text">
                <h4>Inventory Optimization</h4>
                <p>Strategies to reduce costs and improve efficiency</p>
              </div>
            </div>
            
            <div class="prompt-card" @click="setExampleQuery('Who are our top 10 customers by total order value?')">
              <div class="prompt-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22S8 18 8 13V6L12 4L16 6V13C16 18 12 22 12 22Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="prompt-text">
                <h4>Top 10 Customers</h4>
                <p>According to total order value</p>
              </div>
            </div>
            
            <div class="prompt-card" @click="setExampleQuery('Which products have the highest profit margin across all categories?')">
              <div class="prompt-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="prompt-text">
                <h4>Highest Profitable</h4>
                <p>Highest profit margin across all categories</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Messages -->
      <div v-for="(message, index) in conversationHistory" :key="index" :class="['message-container', message.type]">
        <div class="message-wrapper">
          <div v-if="message.type === 'agent'" class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="message-content">
            <div class="message-text">{{ message.text }}</div>
            <div class="message-actions" v-if="message.type === 'agent'">
              <button class="action-btn" title="Copy">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                  <path d="M5 15H4C3.46957 15 2.96086 14.7893 2.58579 14.4142C2.21071 14.0391 2 13.5304 2 13V4C2 3.46957 2.21071 2.96086 2.58579 2.58579C2.96086 2.21071 3.46957 2 4 2H13C13.5304 2 14.0391 2.21071 14.4142 2.58579C14.7893 2.96086 15 3.46957 15 4V5" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
              <button class="action-btn" title="Regenerate">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 4V10H7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M23 20V14H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M20.49 9C20.0295 7.90769 19.3288 6.94098 18.4402 6.17449C17.5516 5.40799 16.4987 4.86398 15.3653 4.57943C14.2319 4.29488 13.0485 4.27793 11.9067 4.53011C10.7649 4.7823 9.69622 5.29661 8.79 6.03L1 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3.51 15C3.97044 16.0923 4.67118 17.059 5.55982 17.8255C6.44846 18.592 7.50134 19.136 8.63474 19.4206C9.76814 19.7051 10.9515 19.7221 12.0933 19.4699C13.2351 19.2177 14.3038 18.7034 15.21 17.97L23 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div class="message-time">{{ formatTime(new Date()) }}</div>
      </div>

      <!-- Loading Message -->
      <div v-if="isLoading" class="message-container agent">
        <div class="message-wrapper loading">
          <div class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <div class="typing-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="chat-input-area">
      <div class="input-container">
        <div class="input-wrapper">
          <textarea 
            v-model="question" 
            placeholder="Ask Your Query Here..." 
            @keydown="handleKeydown"
            @input="adjustTextareaHeight"
            ref="textarea"
            rows="1"
            :disabled="isLoading"
            class="message-input"
          ></textarea>
          <button 
            @click="handleQuery" 
            :disabled="isLoading || !question.trim()"
            class="send-button"
          >
            <svg v-if="!isLoading" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div v-else class="loading-spinner"></div>
          </button>
        </div>
        <div v-if="queryError" class="error-message">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M15 9L9 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          {{ queryError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'QueryPage',
  data() {
    return {
      backendUrl: 'http://localhost:5000',
      question: '',
      conversationHistory: [],
      queryError: '',
      isLoading: false,
    };
  },
  methods: {
    setExampleQuery(query) {
      this.question = query;
      this.$nextTick(() => {
        this.adjustTextareaHeight();
        this.$refs.textarea.focus();
      });
    },
    
    formatTime(date) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },

    adjustTextareaHeight() {
      const textarea = this.$refs.textarea;
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
      }
    },

    handleKeydown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        this.handleQuery();
      }
    },

    async handleQuery() {
      this.queryError = '';

      const accessToken = localStorage.getItem('accessToken');
      if (!accessToken) {
        this.queryError = 'You are not logged in. Please log in again.';
        this.$router.push('/');
        return;
      }
      if (!this.question.trim()) {
        this.queryError = 'Please enter a question.';
        return;
      }

      this.isLoading = true;
      const userQuestion = this.question;
      this.conversationHistory.push({ type: 'user', text: userQuestion });
      this.question = '';
      this.adjustTextareaHeight();

      this.$nextTick(() => {
        this.scrollToBottom();
      });

      try {
        const response = await axios.post(
          `${this.backendUrl}/query`,
          { question: userQuestion },
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );
        const agentAnswer = response.data.answer;
        this.conversationHistory.push({ type: 'agent', text: agentAnswer });
        console.log('Query successful:', response.data);
      } catch (error) {
        this.queryError = 'Query Error: ' + (error.response?.data?.error || error.message);
        console.error('Query failed:', error.response?.data || error);
        this.conversationHistory.pop();
        
        if (error.response?.status === 401 || error.response?.status === 403) {
          this.queryError += " Session expired or unauthorized. Please log in.";
          this.logout();
        }
      } finally {
        this.isLoading = false;
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },

    scrollToBottom() {
      const container = this.$refs.messagesContainer;
      if (container) {
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        });
      }
    },

    logout() {
      localStorage.removeItem('accessToken');
      this.conversationHistory = [];
      this.$router.push('/');
    }
  },
  
  mounted() {
    if (!localStorage.getItem('accessToken')) {
      this.$router.push('/');
    }
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Poppins:wght@300;400;500;600&display=swap');

* {
  box-sizing: border-box;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  font-family: 'Poppins', sans-serif;
  overflow: hidden;
}

/* Header */
.chat-header {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #4dd0e1, #81c784);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(77, 208, 225, 0.3);
}

.brand-icon svg {
  width: 24px;
  height: 24px;
}

.brand-text h1 {
  font-family: 'Montserrat', sans-serif;
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #263238;
  letter-spacing: -0.02em;
}

.brand-text p {
  margin: 0;
  font-size: 0.8rem;
  color: #607d8b;
  font-weight: 400;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: rgba(255, 255, 255, 0.9);
  color: #546e7a;
  border: 1px solid rgba(84, 110, 122, 0.2);
  border-radius: 50px;
  font-family: 'Poppins', sans-serif;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 1);
  color: #37474f;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.logout-btn svg {
  width: 16px;
  height: 16px;
}

/* Chat Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.4);
  border-radius: 2px;
}

/* Welcome Screen */
.welcome-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  animation: fadeIn 0.6s ease-out;
}

.welcome-content {
  text-align: center;
  max-width: 700px;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #4dd0e1, #81c784);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2rem;
  color: white;
  box-shadow: 0 8px 32px rgba(77, 208, 225, 0.3);
}

.welcome-icon svg {
  width: 40px;
  height: 40px;
}

.welcome-content h2 {
  font-family: 'Montserrat', sans-serif;
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #263238;
  letter-spacing: -0.02em;
}

.welcome-content > p {
  font-size: 1.1rem;
  color: #546e7a;
  margin-bottom: 3rem;
  line-height: 1.6;
  font-weight: 400;
}

.example-prompts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
}

.prompt-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  text-align: left;
}

.prompt-card:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.prompt-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #4dd0e1, #81c784);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.prompt-icon svg {
  width: 20px;
  height: 20px;
}

.prompt-text h4 {
  font-family: 'Montserrat', sans-serif;
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #263238;
}

.prompt-text p {
  margin: 0;
  font-size: 0.85rem;
  color: #607d8b;
  line-height: 1.4;
}

/* Message Containers */
.message-container {
  animation: slideUp 0.4s ease-out;
  max-width: 100%;
}

.message-container.user {
  align-self: flex-end;
}

.message-container.agent {
  align-self: flex-start;
}

.message-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  max-width: 100%;
}

.message-container.user .message-wrapper {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #4dd0e1, #81c784);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.message-avatar svg {
  width: 16px;
  height: 16px;
}

.message-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 18px;
  padding: 1rem 1.25rem;
  max-width: calc(100% - 50px);
  position: relative;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.message-container.user .message-content {
  background: linear-gradient(135deg, #4dd0e1, #81c784);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.message-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #263238;
  word-wrap: break-word;
}

.message-container.user .message-text {
  color: white;
}

.message-actions {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message-wrapper:hover .message-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: rgba(0, 0, 0, 0.05);
  color: #607d8b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #37474f;
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.message-time {
  font-size: 0.75rem;
  color: #90a4ae;
  margin-top: 0.5rem;
  text-align: center;
}

/* Loading Animation */
.message-wrapper.loading {
  animation: pulse 1.5s ease-in-out infinite;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  background: #4dd0e1;
  border-radius: 50%;
  animation: typing 1.4s ease-in-out infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

/* Input Area */
.chat-input-area {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  padding: 1.5rem 2rem;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  background: white;
  border-radius: 24px;
  padding: 0.75rem 1rem;
  font-family: 'Montserrat', sans-serif;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
    width: 100%;        
}
.input-wrapper:hover {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.1);
}
.message-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #263238;
  background: transparent;
  padding: 0.5rem;
  font-family: 'Montserrat', sans-serif;
  width: 100%;
}
.send-button {
  background: linear-gradient(135deg, #4dd0e1, #81c784);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.send-button:hover {
  background: linear-gradient(135deg, #3bbdcf, #6fbf7c);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.loading-spinner {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 235, 238, 0.9);
  color: #d32f2f;
  border: 1px solid rgba(255, 205, 210, 0.5);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  margin-top: 1rem;
}
.error-message svg {
  width: 16px;
  height: 16px;
  color: #d32f2f;
}
.input-footer {
  margin-top: 1rem;
  font-size: 0.85rem;
  color: #546e7a;
}
.input-footer p {
  margin: 0;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}
@keyframes typing {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}
</style>
