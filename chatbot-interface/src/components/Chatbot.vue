<template>
  <div class="chat-container">
    <div class="banner">
      <span class="banner-text">POC IA GED ANALYZER ⚙️</span>
    </div>
    <div class="chat-messages" ref="chatMessages">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.type, {'with-avatar': message.type === 'bot'}]">
        <div v-if="message.type === 'bot'" class="avatar">🤖</div>
        <div class="message-content">{{ message.text }}</div>
      </div>
    </div>
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <img 
          src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExancyZHFhdm9jajMzdndsb2VtaGowOHpuMTl2OWcydXV6MjV2MnhmdiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l3nWhI38IWDofyDrW/giphy.gif"
          alt="Loading" 
          class="loading-gif"
        >
        <p>Analyse en cours...</p>
      </div>
    </div>
    <div class="input-container">
      <div class="file-upload-container">
        <label for="file-upload" class="custom-file-upload">
          <i class="fas fa-file-upload"></i> Charger un document
        </label>
        <input id="file-upload" 
               type="file" 
               @change="handleFileUpload" 
               accept=".pdf,.jpg,.jpeg,.png"
               class="file-input">
      </div>
      <div class="message-input-container">
        <input type="text" 
               v-model="userInput" 
               @keyup.enter="sendTextMessage"
               placeholder="Posez votre question..."
               class="text-input">
        <button @click="sendMessage" class="send-button">
          <span>Envoyer</span>
        </button>
      </div>
    </div>
    <div v-if="documentType && suggestedQuestions[documentType]" class="suggested-questions">
      <p class="suggestions-title">Questions suggérées :</p>
      <div class="suggestions-container">
        <button 
          v-for="question in suggestedQuestions[documentType]" 
          :key="question"
          @click="askSuggestedQuestion(question)"
          class="suggestion-btn">
          {{ question }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatbotInterface',
  data() {
    return {
      messages: [],
      userInput: '',
      selectedFile: null,
      currentDocumentId: null,
      documentInfo: null,
      documentType: null,
      isLoading: false,
      suggestedQuestions: {
        "BULLETIN DE SALAIRE": [
          "Quel est le salaire net ?",
          "Quel est le numéro de sécurité sociale ?",
          "Qui est l'employeur ?",
          "Quelle est la période ?"
        ],
        "CONTRAT": [
          "Quelle est la date de début ?",
          "Quel est le salaire ?",
          "Quel est le poste ?",
          "Quelle est la durée ?"
        ],
        // ... autres types ...
      }
    }
  },
  methods: {
    handleFileUpload(event) {
      this.selectedFile = event.target.files[0];
    },
    async sendTextMessage() {
      if (!this.userInput.trim()) return;
      
      const question = this.userInput;
      this.userInput = ''; // Vider l'input immédiatement
      this.addMessage(question, 'user');
      this.isLoading = true; // Activer l'animation

      if (!this.currentDocumentId) {
        this.addMessage("Veuillez d'abord charger un document", 'bot');
        this.isLoading = false;
        return;
      }

      try {
        const response = await fetch('http://localhost:5000/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: question,
            doc_id: this.currentDocumentId
          })
        });

        const data = await response.json();

        if (response.ok) {
          let responseText = `Réponse : ${data.answer}`;
          if (data.confidence) {
            responseText += `\nConfiance : ${(data.confidence * 100).toFixed(2)}%`;
          }
          this.addMessage(responseText, 'bot');
        } else {
          throw new Error(data.error || 'Une erreur est survenue');
        }
      } catch (error) {
        this.addMessage(`Erreur : ${error.message}`, 'bot');
      } finally {
        this.isLoading = false; // Désactiver l'animation
      }
    },
    async sendFile() {
      if (!this.selectedFile) {
        this.addMessage("Veuillez sélectionner un fichier d'abord", 'bot');
        return;
      }

      this.isLoading = true;
      const formData = new FormData();
      formData.append('file', this.selectedFile);

      try {
        // 1. Analyse du document (backend)
        const analyzeResponse = await fetch('http://localhost:8080/analyze', {
          method: 'POST',
          body: formData,
          headers: {
            'Accept': 'application/json',
          },
        });

        if (!analyzeResponse.ok) {
          throw new Error(`Erreur HTTP: ${analyzeResponse.status}`);
        }

        const analyzeData = await analyzeResponse.json();
        
        // 2. Indexation pour le QA
        const docId = this.selectedFile.name;
        await fetch('http://localhost:5000/index', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            doc_id: docId,
            text: analyzeData.text,
            type: analyzeData.type,  // Type de document détecté (BULLETIN DE SALAIRE, CONTRAT, etc.)
            informations: analyzeData.informations
          })
        });

        this.currentDocumentId = docId;
        
        // 3. Afficher le résultat
        this.addMessage(
          `Document analysé avec succès!\nType détecté: ${analyzeData.type}\nConfiance: ${(analyzeData.confidence * 100).toFixed(2)}%\n\nVous pouvez maintenant poser des questions sur ce document.`,
          'bot'
        );

      } catch (error) {
        this.addMessage(`Erreur lors du traitement: ${error.message}`, 'bot');
      } finally {
        this.isLoading = false;
      }

      this.selectedFile = null;
      const fileInput = document.querySelector('.file-input');
      if (fileInput) fileInput.value = '';
    },
    async sendMessage() {
      if (this.selectedFile) {
        await this.sendFile();
      } else if (this.userInput.trim()) {
        await this.sendTextMessage();
      }
    },
    addMessage(text, type) {
      this.messages.push({ text, type });
      this.$nextTick(() => {
        const container = this.$refs.chatMessages;
        container.scrollTop = container.scrollHeight;
      });
    },
    askSuggestedQuestion(question) {
      this.userInput = question;
      this.sendTextMessage();
    }
  }
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  max-width: 800px;
  margin: 20px auto;
  border-radius: 16px;
  height: 600px;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.banner {
  background: linear-gradient(135deg, #1a73e8, #8ab4f8);
  padding: 15px;
  border-radius: 16px 16px 0 0;
}

.banner-text {
  font-size: 1.4em;
  font-weight: bold;
  color: white;
}

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f8f9fa;
}

.message {
  display: flex;
  align-items: flex-start;
  margin: 12px 0;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-content {
  padding: 12px 16px;
  border-radius: 18px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  line-height: 1.4;
}

.user .message-content {
  background-color: #1a73e8;
  color: white;
  border-radius: 18px 18px 0 18px;
}

.bot .message-content {
  background-color: white;
  color: #333;
  border-radius: 18px 18px 18px 0;
}

.avatar {
  width: 35px;
  height: 35px;
  margin: 0 8px;
  background-color: #e8f0fe;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.input-container {
  padding: 15px;
  background-color: white;
  border-top: 1px solid #eee;
}

.message-input-container {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.text-input {
  flex-grow: 1;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  font-size: 1em;
  transition: border-color 0.3s;
}

.text-input:focus {
  border-color: #1a73e8;
  outline: none;
}

.custom-file-upload {
  display: inline-block;
  padding: 8px 16px;
  background-color: #e8f0fe;
  color: #1a73e8;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.custom-file-upload:hover {
  background-color: #d2e3fc;
}

.file-input {
  display: none;
}

.send-button {
  padding: 12px 24px;
  background-color: #1a73e8;
  color: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.send-button:hover {
  background-color: #1557b0;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
  color: #1a73e8;
}

.loading-gif {
  width: 200px;
  height: auto;
  margin-bottom: 20px;
  border-radius: 10px;
}

.suggested-questions {
  padding: 15px;
  background-color: #f8f9fa;
  border-top: 1px solid #eee;
}

.suggestions-title {
  font-weight: 500;
  color: #5f6368;
  margin-bottom: 10px;
}

.suggestions-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-btn {
  padding: 8px 16px;
  background-color: #e8f0fe;
  color: #1a73e8;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.suggestion-btn:hover {
  background-color: #d2e3fc;
}
</style>