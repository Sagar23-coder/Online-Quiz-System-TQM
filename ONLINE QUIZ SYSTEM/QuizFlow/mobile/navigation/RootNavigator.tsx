import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { RootStackParamList, MainTabParamList } from '../types';

import { DashboardScreen } from '../app/screens/DashboardScreen';
import { HistoryScreen } from '../app/screens/HistoryScreen';
import { ProfileScreen } from '../app/screens/ProfileScreen';
import { QuizDetailScreen } from '../app/screens/QuizDetailScreen';
import { QuizActiveScreen } from '../app/screens/QuizActiveScreen';
import { ResultScreen } from '../app/screens/ResultScreen';

import { Theme } from '../theme';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

const TabNavigator = ({ onLogout }: { onLogout: () => void }) => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: Theme.BG_CARD },
        headerTintColor: Theme.TEXT_MAIN,
        headerTitleStyle: { fontWeight: '700', fontSize: 17 },
        tabBarStyle: {
          backgroundColor: Theme.BG_CARD,
          borderTopColor: Theme.BORDER,
          height: 62,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarActiveTintColor: Theme.PRIMARY,
        tabBarInactiveTintColor: Theme.TEXT_MUTED,
        tabBarLabelStyle: { fontSize: 12, fontWeight: '600' },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          title: 'Quizzes',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>📝</Text>,
        }}
      />
      <Tab.Screen
        name="History"
        component={HistoryScreen}
        options={{
          title: 'History',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>📊</Text>,
        }}
      />
      <Tab.Screen
        name="Profile"
        children={() => <ProfileScreen onLogout={onLogout} />}
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>👤</Text>,
        }}
      />
    </Tab.Navigator>
  );
};

export const RootNavigator = ({ onLogout }: { onLogout: () => void }) => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: Theme.BG_CARD },
        headerTintColor: Theme.TEXT_MAIN,
        headerTitleStyle: { fontWeight: '700', fontSize: 17 },
        headerBackTitleVisible: false,
      }}
    >
      <Stack.Screen
        name="MainTabs"
        children={() => <TabNavigator onLogout={onLogout} />}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="QuizDetail"
        component={QuizDetailScreen}
        options={{ title: 'Assessment Instructions' }}
      />
      <Stack.Screen
        name="QuizActive"
        component={QuizActiveScreen}
        options={{
          title: 'QuizFlow Assessment',
          headerBackVisible: false,
          gestureEnabled: false,
        }}
      />
      <Stack.Screen
        name="Result"
        component={ResultScreen}
        options={{
          title: 'Assessment Results',
          headerBackVisible: false,
        }}
      />
    </Stack.Navigator>
  );
};

