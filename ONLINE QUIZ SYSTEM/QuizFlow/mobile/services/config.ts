import { Platform } from 'react-native';

class NetworkConfig {
  private _apiUrl: string;

  constructor() {
    // Android emulator maps 10.0.2.2 to development host localhost
    // iOS simulator / Web connects directly to localhost
    if (Platform.OS === 'android') {
      this._apiUrl = 'http://10.0.2.2:8000/api/v1';
    } else {
      this._apiUrl = 'http://localhost:8000/api/v1';
    }
  }

  get apiUrl(): string {
    return this._apiUrl;
  }

  setApiUrl(newUrl: string) {
    this._apiUrl = newUrl.replace(/\/+$/, '');
  }
}

export const networkConfig = new NetworkConfig();

