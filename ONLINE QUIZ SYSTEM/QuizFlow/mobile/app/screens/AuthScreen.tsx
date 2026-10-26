import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { apiService } from '../../services/api';
import { Theme } from '../../theme';

export const AuthScreen = ({ onLoginSuccess }: { onLoginSuccess: () => void }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [role, setRole] = useState<'participant' | 'organizer'>('participant');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async () => {
    setErrorMsg('');
    if (!email.trim() || !password.trim()) {
      setErrorMsg('Please enter your email and password.');
      return;
    }

    setLoading(true);
    if (isLogin) {
      const res = await apiService.login(email.trim(), password.trim());
      setLoading(false);
      if (res.success) {
        onLoginSuccess();
      } else {
        setErrorMsg(res.error || 'Authentication failed. Please check credentials.');
      }
    } else {
      if (!fullName.trim()) {
        setErrorMsg('Please provide your full name.');
        setLoading(false);
        return;
      }
      if (password !== confirmPassword) {
        setErrorMsg('Passwords do not match.');
        setLoading(false);
        return;
      }

      const res = await apiService.register(email.trim(), fullName.trim(), password, confirmPassword, role);
      if (res.success) {
        const loginRes = await apiService.login(email.trim(), password);
        setLoading(false);
        if (loginRes.success) {
          onLoginSuccess();
        } else {
          setIsLogin(true);
          setErrorMsg('Account created successfully! Please sign in.');
        }
      } else {
        setLoading(false);
        setErrorMsg(res.error || 'Registration failed.');
      }
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.brandBox}>
          <View style={styles.brandBadge}>
            <Text style={styles.brandBadgeIcon}>✦</Text>
          </View>
          <Text style={styles.brandTitle}>QuizFlow</Text>
          <Text style={styles.brandSubtitle}>Online Quiz & Assessment Platform</Text>
        </View>

        <View style={styles.card}>
          <View style={styles.tabRow}>
            <TouchableOpacity
              style={[styles.tab, isLogin && styles.activeTab]}
              onPress={() => {
                setIsLogin(true);
                setErrorMsg('');
              }}
            >
              <Text style={[styles.tabText, isLogin && styles.activeTabText]}>Sign In</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.tab, !isLogin && styles.activeTab]}
              onPress={() => {
                setIsLogin(false);
                setErrorMsg('');
              }}
            >
              <Text style={[styles.tabText, !isLogin && styles.activeTabText]}>Register</Text>
            </TouchableOpacity>
          </View>

          {errorMsg ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMsg}</Text>
            </View>
          ) : null}

          {!isLogin && (
            <>
              <View style={styles.roleContainer}>
                <Text style={styles.label}>I am registering as:</Text>
                <View style={styles.roleRow}>
                  <TouchableOpacity
                    style={[styles.roleBtn, role === 'participant' && styles.roleBtnActive]}
                    onPress={() => setRole('participant')}
                  >
                    <Text
                      style={[
                        styles.roleBtnText,
                        role === 'participant' && styles.roleBtnTextActive,
                      ]}
                    >
                      Participant (Student)
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.roleBtn, role === 'organizer' && styles.roleBtnActive]}
                    onPress={() => setRole('organizer')}
                  >
                    <Text
                      style={[
                        styles.roleBtnText,
                        role === 'organizer' && styles.roleBtnTextActive,
                      ]}
                    >
                      Organizer (Teacher)
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Full Name</Text>
                <TextInput
                  style={styles.input}
                  placeholder={role === 'organizer' ? 'Prof. Jane Smith' : 'Jane Doe'}
                  placeholderTextColor={Theme.TEXT_DIM}
                  value={fullName}
                  onChangeText={setFullName}
                  autoCapitalize="words"
                />
              </View>
            </>
          )}

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={styles.input}
              placeholder="student@example.com"
              placeholderTextColor={Theme.TEXT_DIM}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              placeholder="••••••••"
              placeholderTextColor={Theme.TEXT_DIM}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          {!isLogin && (
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Confirm Password</Text>
              <TextInput
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor={Theme.TEXT_DIM}
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
              />
            </View>
          )}

          <TouchableOpacity
            style={styles.submitBtn}
            activeOpacity={0.8}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.submitBtnText}>
                {isLogin
                  ? 'Sign In to QuizFlow'
                  : role === 'organizer'
                  ? 'Create Teacher Account'
                  : 'Create Student Account'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.BG_MAIN,
  },
  scroll: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
    paddingVertical: 36,
  },
  brandBox: {
    alignItems: 'center',
    marginBottom: 24,
  },
  brandBadge: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Theme.PRIMARY_LIGHT,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  brandBadgeIcon: {
    color: Theme.PRIMARY,
    fontSize: 20,
    fontWeight: 'bold',
  },
  brandTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
    letterSpacing: 0.5,
  },
  brandSubtitle: {
    fontSize: 13,
    color: Theme.TEXT_MUTED,
    marginTop: 4,
  },
  card: {
    backgroundColor: Theme.BG_CARD,
    borderRadius: 16,
    padding: 22,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  tabRow: {
    flexDirection: 'row',
    backgroundColor: Theme.BG_MAIN,
    borderRadius: 8,
    padding: 4,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: Theme.BORDER,
  },
  tab: {
    flex: 1,
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeTab: {
    backgroundColor: Theme.PRIMARY,
  },
  tabText: {
    color: Theme.TEXT_MUTED,
    fontSize: 13,
    fontWeight: '600',
  },
  activeTabText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  inputGroup: {
    marginBottom: 14,
  },
  label: {
    color: Theme.TEXT_MUTED,
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 6,
  },
  input: {
    backgroundColor: Theme.BG_INPUT,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: Theme.TEXT_MAIN,
    fontSize: 14,
  },
  submitBtn: {
    backgroundColor: Theme.PRIMARY,
    borderRadius: 8,
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 10,
    shadowColor: Theme.PRIMARY,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  submitBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  errorBox: {
    backgroundColor: Theme.DANGER_LIGHT,
    borderRadius: 8,
    padding: 10,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Theme.DANGER,
  },
  errorText: {
    color: Theme.DANGER,
    fontSize: 12,
    textAlign: 'center',
    fontWeight: '500',
  },
  roleContainer: {
    marginBottom: 14,
  },
  roleRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  roleBtn: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    backgroundColor: Theme.BG_INPUT,
    alignItems: 'center',
  },
  roleBtnActive: {
    borderColor: Theme.PRIMARY,
    backgroundColor: Theme.PRIMARY_LIGHT,
  },
  roleBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: Theme.TEXT_MUTED,
  },
  roleBtnTextActive: {
    color: Theme.PRIMARY,
    fontWeight: 'bold',
  },
});
