import js from "@eslint/js";
import tsParser from "@typescript-eslint/parser";
export default [
  js.configs.recommended,
  {
    files: ["**/*.ts", "**/*.tsx"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parser: tsParser,
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: {
        window: "readonly", document: "readonly", localStorage: "readonly",
        sessionStorage: "readonly", console: "readonly", fetch: "readonly",
        crypto: "readonly", URL: "readonly", URLSearchParams: "readonly",
        setInterval: "readonly", clearInterval: "readonly", setTimeout: "readonly",
        clearTimeout: "readonly", btoa: "readonly", Blob: "readonly",
      },
    },
    rules: { "no-undef": "error", "no-unused-vars": "off" },
  },
];
