// .vitepress/theme/index.ts
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import './style/style.css'
import Layout from "./Layout.vue";

// custom CSS
import './style/print.css'

export default {
    extends: DefaultTheme,
    Layout,
  };
