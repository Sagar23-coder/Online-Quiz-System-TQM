import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { apiService } from '../../services/api';
import { networkConfig } from '../../services/config';
import { Theme } from '../../theme';

export const ProfileScreen = ({ onLogout }: { onLogout: () => void }) => {
  const user = apiService.getUser();
  const [apiUrl, setApiUrl] = useState(networkConfig.apiUrl);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleSaveApiUrl = () => {
    networkConfig.setApiUrl(apiUrl);
    Alert.alert('Settings Updated', `API endpoint set to:\n${networkConfig.apiUrl}`);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    networkConfig.setApiUrl(apiUrl);
    const res = await apiService.checkHealth();
    setTesting(false);
    if (res.success && res.data) {
      setTestResult(`✓ Connected successfully! Database: ${res.data.database}`);
    } else {
      setTestResult(`✗ Connection failed: ${res.error}`);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Student Profile</Text>
        <Text style={styles.headerSub}>Account settings and networking configuration</Text>
      </View>

      {/* User Information Card */}
      <View style={styles.card}>
        <View style={styles.userTop}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>👤</Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{user?.full_name || 'Student'}</Text>
            <Text style={styles.userRole}>{user?.role?.toUpperCase() || 'STUDENT'}</Text>
          </View>
        </View>

        <View style={styles.divider} />

        <View style={styles.row}>
          <Text style={styles.label}>Email Address</Text>
          <Text style={styles.value}>{user?.email || 'N/A'}</Text>
        </View>

        <View style={[styles.row, { borderBottomWidth: 0 }]}>
          <Text style={styles.label}>Account ID</Text>
          <Text style={styles.value}>#{user?.id || 'N/A'}</Text>
        </View>
      </View>

      {/* Networking & Server Configuration Card */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Backend API Configuration</Text>
        <Text style={styles.helperText}>
          Configure the API endpoint URL for your network environment:
          {'\n'}• Android Emulator: http://10.0.2.2:8000/api/v1
          {'\n'}• Physical Device (LAN): http://YOUR_PC_IP:8000/api/v1
        </Text>

        <TextInput
          style={styles.input}
          value={apiUrl}
          onChangeText={setApiUrl}
          placeholder="http://10.0.2.2:8000/api/v1"
          placeholderTextColor={Theme.TEXT_DIM}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <View style={styles.btnRow}>
          <TouchableOpacity style={styles.saveBtn} onPress={handleSaveApiUrl}>
            <Text style={styles.saveBtnText}>Save URL</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.testBtn} onPress={handleTestConnection} disabled={testing}>
            {testing ? (
              <ActivityIndicator color={Theme.PRIMARY} size="small" />
            ) : (
              <Text style={styles.testBtnText}>Test Connection</Text>
            )}
          </TouchableOpacity>
        </View>

        {testResult ? (
          <Text
            style={[
              styles.resultText,
              testResult.startsWith('✓') ? styles.resultSuccess : styles.resultError,
            ]}
          >
            {testResult}
          </Text>
        ) : null}
      </View>

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutBtn} onPress={onLogout}>
        <Text style={styles.logoutBtnText}>Sign Out of QuizFlow</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.BG_MAIN,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
  },
  headerSub: {
    fontSize: 13,
    color: Theme.TEXT_MUTED,
    marginTop: 2,
  },
  card: {
    backgroundColor: Theme.BG_CARD,
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  userTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Theme.PURPLE_LIGHT,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    fontSize: 20,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
  },
  userRole: {
    fontSize: 11,
    color: Theme.PRIMARY,
    fontWeight: '700',
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: Theme.BORDER,
    marginBottom: 10,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Theme.BORDER,
  },
  label: {
    color: Theme.TEXT_MUTED,
    fontSize: 13,
  },
  value: {
    color: Theme.TEXT_MAIN,
    fontSize: 13,
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
    marginBottom: 6,
  },
  helperText: {
    fontSize: 12,
    color: Theme.TEXT_MUTED,
    lineHeight: 18,
    marginBottom: 12,
  },
  input: {
    backgroundColor: Theme.BG_INPUT,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: Theme.TEXT_MAIN,
    fontSize: 13,
    marginBottom: 12,
  },
  btnRow: {
    flexDirection: 'row',
    gap: 10,
  },
  saveBtn: {
    flex: 1,
    backgroundColor: Theme.PRIMARY,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  saveBtnText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 13,
  },
  testBtn: {
    flex: 1,
    backgroundColor: Theme.PRIMARY_LIGHT,
    borderWidth: 1,
    borderColor: Theme.PRIMARY,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  testBtnText: {
    color: Theme.PRIMARY,
    fontWeight: 'bold',
    fontSize: 13,
  },
  resultText: {
    marginTop: 10,
    fontSize: 12,
    padding: 8,
    borderRadius: 6,
  },
  resultSuccess: {
    backgroundColor: Theme.SUCCESS_LIGHT,
    color: Theme.SUCCESS,
  },
  resultError: {
    backgroundColor: Theme.DANGER_LIGHT,
    color: Theme.DANGER,
  },
  logoutBtn: {
    backgroundColor: Theme.DANGER_LIGHT,
    borderWidth: 1,
    borderColor: Theme.DANGER,
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 8,
  },
  logoutBtnText: {
    color: Theme.DANGER,
    fontSize: 14,
    fontWeight: 'bold',
  },
});
