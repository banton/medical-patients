module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['./setupTests.ts'],
  moduleNameMapper: {
    // If you have module aliases in tsconfig.json, map them here
    // Example: '^@components/(.*)$': '<rootDir>/src/components/$1'
  },
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json', // or your specific tsconfig file
    }],
  },
};
