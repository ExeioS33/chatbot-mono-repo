<template>
  <div id="app">
    <Chatbot />
  </div>
</template>

<script>
import Chatbot from './components/Chatbot.vue'

export default {
  name: 'App',
  components: {
    Chatbot
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  padding: 20px;
}
</style>
