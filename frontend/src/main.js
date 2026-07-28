import Aura from "@primevue/themes/aura";
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import { createApp } from "vue";

import "primeicons/primeicons.css";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(PrimeVue, { ripple: true, theme: { preset: Aura } });

app.mount("#app");
