import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  base: "/fieldsignal/",
  build: {
    target: "es2022",
    rollupOptions: {
      input: {
        app: fileURLToPath(new URL("./index.html", import.meta.url)),
        guide: fileURLToPath(new URL("./guide/index.html", import.meta.url)),
      },
    },
  },
});
