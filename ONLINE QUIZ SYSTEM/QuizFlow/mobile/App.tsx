import React, { useState } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { AuthScreen } from './app/screens/AuthScreen';
import { RootNavigator } from './navigation/RootNavigator';
import { apiService } from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(apiService.getToken());
  });

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    apiService.logout();
    setIsAuthenticated(false);
  };

  const content = isAuthenticated ? (
    <NavigationContainer>
      <RootNavigator onLogout={handleLogout} />
    </NavigationContainer>
  ) : (
    <AuthScreen onLoginSuccess={handleLoginSuccess} />
  );

  return (
    <SafeAreaProvider style={styles.provider}>
      <StatusBar style="light" backgroundColor="#0F172A" />
      {Platform.OS === 'web' ? (
        <View style={styles.webWrapper}>
          <View style={styles.phoneContainer}>{content}</View>
        </View>
      ) : (
        content
      )}
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  provider: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  webWrapper: {
    flex: 1,
    backgroundColor: '#090D16',
    alignItems: 'center',
    justifyContent: 'center',
  },
  phoneContainer: {
    width: '100%',
    maxWidth: 480,
    height: '100%',
    backgroundColor: '#0F172A',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.35,
    shadowRadius: 20,
    elevation: 8,
  },
});
