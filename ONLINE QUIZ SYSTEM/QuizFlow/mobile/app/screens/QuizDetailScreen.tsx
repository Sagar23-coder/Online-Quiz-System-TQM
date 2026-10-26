import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { apiService } from '../../services/api';
import { Quiz } from '../../types';
import { Theme } from '../../theme';

export const QuizDetailScreen = ({ route, navigation }: { route: any; navigation: any }) => {
  const { quiz } = route.params as { quiz: Quiz };
  const [starting, setStarting] = useState(false);

  const handleStartQuiz = async () => {
    setStarting(true);
    const res = await apiService.startQuiz(quiz.id);
    setStarting(false);

    if (res.success && res.data) {
      navigation.replace('QuizActive', { attempt: res.data });
    } else {
      Alert.alert('Cannot Start Quiz', res.error || 'Failed to initiate attempt.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <View style={styles.badgeRow}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>OFFICIAL ASSESSMENT</Text>
          </View>
        </View>

        <Text style={styles.title}>{quiz.title}</Text>
        <Text style={styles.desc}>{quiz.description || 'Comprehensive evaluation covering key competencies.'}</Text>

        <View style={styles.infoBox}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>⏱ Duration Limit</Text>
            <Text style={styles.infoVal}>{quiz.duration_minutes} Minutes</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>❓ Total Questions</Text>
            <Text style={styles.infoVal}>{quiz.question_count} Questions</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>🎯 Maximum Marks</Text>
            <Text style={styles.infoVal}>{quiz.total_marks} Marks</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>🏆 Required to Pass</Text>
            <Text style={styles.infoVal}>{quiz.passing_percentage}%</Text>
          </View>
        </View>

        <Text style={styles.ruleTitle}>Assessment Guidelines & Rules:</Text>
        <View style={styles.rulesList}>
          <Text style={styles.ruleItem}>• The server countdown timer starts as soon as you tap "Begin Assessment".</Text>
          <Text style={styles.ruleItem}>• Selected answers are autosaved securely to the cloud in real-time.</Text>
          <Text style={styles.ruleItem}>• If time expires, the assessment will automatically finalize and submit.</Text>
          <Text style={styles.ruleItem}>• You can move between questions freely before final submission.</Text>
        </View>

        <TouchableOpacity
          style={styles.startBtn}
          activeOpacity={0.8}
          onPress={handleStartQuiz}
          disabled={starting}
        >
          {starting ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.startBtnText}>Begin Assessment Now →</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.cancelBtn}
          activeOpacity={0.8}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.cancelBtnText}>← Return to Assessments</Text>
        </TouchableOpacity>
      </View>
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
  },
  card: {
    backgroundColor: Theme.BG_CARD,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  badgeRow: {
    marginBottom: 8,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: Theme.PRIMARY_LIGHT,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: {
    color: Theme.PRIMARY,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
    marginBottom: 6,
  },
  desc: {
    fontSize: 13,
    color: Theme.TEXT_MUTED,
    lineHeight: 19,
    marginBottom: 20,
  },
  infoBox: {
    backgroundColor: Theme.BG_MAIN,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    marginBottom: 20,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  divider: {
    height: 1,
    backgroundColor: Theme.BORDER,
  },
  infoLabel: {
    color: Theme.TEXT_MUTED,
    fontSize: 13,
    fontWeight: '500',
  },
  infoVal: {
    color: Theme.TEXT_MAIN,
    fontSize: 13,
    fontWeight: '700',
  },
  ruleTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
    marginBottom: 10,
  },
  rulesList: {
    marginBottom: 24,
    gap: 6,
  },
  ruleItem: {
    color: Theme.TEXT_MUTED,
    fontSize: 12,
    lineHeight: 18,
  },
  startBtn: {
    backgroundColor: Theme.PRIMARY,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    shadowColor: Theme.PRIMARY,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 3,
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: 'bold',
  },
  cancelBtn: {
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 10,
  },
  cancelBtnText: {
    color: '#334155',
    fontSize: 14,
    fontWeight: '700',
  },
});
