<template>
  <div id="app">
 
    <router-view /> 
  </div>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style>
body {
  margin: 0;
  background-color: #f0f2f5;
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;

}

nav {
  padding: 15px;
  background-color: #34495e;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: right; /* Align logout/query button to right */
}

nav a {
  font-weight: bold;
  color: #fff;
  text-decoration: none;
  padding: 8px 15px;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

nav a.router-link-exact-active {
  background-color: #4CAF50;
}

nav a:hover {
    background-color: #556c80;
}
</style>