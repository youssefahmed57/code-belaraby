import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const projectRules = {
  files: ["**/*.{js,jsx,mjs,ts,tsx}"],
  ignores: ["eslint.config.mjs"],
  rules: {
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/set-state-in-effect": "warn",
    "react-hooks/refs": "warn",
    "import/no-anonymous-default-export": "off",
  },
};

export default [
  ...nextCoreWebVitals,
  ...nextTypeScript,
  projectRules,
];
