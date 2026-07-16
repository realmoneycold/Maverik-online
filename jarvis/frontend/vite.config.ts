import { defineConfig } from "vite";

export default defineConfig({
  base: './',
  server: {
    port: 5173,
    proxy: {
      "/ws": {
        target: "http://localhost:8340",
        ws: true,
        secure: false,
      },
      "/api": {
        target: "http://localhost:8340",
        secure: false,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
