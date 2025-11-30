/**
 * Jest Setup File
 * Configures test environment for React Native
 */

// Define React Native globals
(global as any).__DEV__ = true;

// Mock AsyncStorage with in-memory storage for integration tests
const storage = new Map<string, string>();

jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn((key: string, value: string) => {
    storage.set(key, value);
    return Promise.resolve();
  }),
  getItem: jest.fn((key: string) => {
    return Promise.resolve(storage.get(key) || null);
  }),
  removeItem: jest.fn((key: string) => {
    storage.delete(key);
    return Promise.resolve();
  }),
  multiRemove: jest.fn((keys: string[]) => {
    keys.forEach(key => storage.delete(key));
    return Promise.resolve();
  }),
  clear: jest.fn(() => {
    storage.clear();
    return Promise.resolve();
  }),
}));

// Mock Expo Constants
jest.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      extra: {
        apiUrl: 'http://localhost:8000/api/v1',
      },
    },
  },
}));

// Mock Expo modules
jest.mock('expo-linear-gradient', () => ({
  LinearGradient: 'LinearGradient',
}));

jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(),
  notificationAsync: jest.fn(),
  selectionAsync: jest.fn(),
}));

jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(() => Promise.resolve()),
  getItemAsync: jest.fn(() => Promise.resolve(null)),
  deleteItemAsync: jest.fn(() => Promise.resolve()),
}));

// Mock navigation
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    setOptions: jest.fn(),
  }),
  useRoute: () => ({
    params: {},
  }),
  useFocusEffect: jest.fn(),
}));

// Silence console warnings in tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
};

// Fix for Jest worker circular reference error with axios
// Override toJSON on Error prototype to prevent circular refs in test serialization
if (typeof (Error.prototype as any).toJSON !== 'function') {
  Object.defineProperty(Error.prototype, 'toJSON', {
    value: function () {
      const alt: any = {};
      Object.getOwnPropertyNames(this).forEach((key) => {
        if (key !== 'config' && key !== 'request' && key !== 'response') {
          alt[key] = (this as any)[key];
        }
      });
      return alt;
    },
    configurable: true,
    writable: true,
  });
}
