// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';

import auth from 'auth-astro';

import node from '@astrojs/node';

import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  integrations: [react(), auth(), tailwind()],

  adapter: node({
    mode: 'standalone'
  }),

  server: {
    host: process.env.AWA_UI_HOST ?? 'localhost',
    port: parseInt(process.env.AWA_UI_PORT ?? '8000')
  },

  vite: {
    define: {
      global: 'globalThis',
    },
    optimizeDeps: {
      include: [
        '@emotion/react',
        '@emotion/styled',
        '@mui/material',
        '@mui/icons-material'
      ]
    },
    ssr: {
      noExternal: [
        '@mui/material',
        '@emotion/react',
        '@emotion/styled',
        '@mui/icons-material'
      ]
    }
  }
});
