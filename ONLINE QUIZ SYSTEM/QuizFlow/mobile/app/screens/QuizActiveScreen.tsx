import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { apiService } from '../../services/api';
import { AttemptStartData } from '../../types';
import { Theme } from '../../theme';

export const QuizActiveScreen = ({ route, navigation }: { route: any; navigation: any }) => {
  const { attempt } = route.params as { attempt: AttemptStartData };
  const questions = attempt.questions;

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string | null>>(() => {
    const initial: Record<number, string | null> = {};
    if (attempt.saved_answers) {
      Object.entries(attempt.saved_answers).forEach(([k, v]) => {
        initial[parseInt(k, 10)] = v;
      });
    }
    return initial;
  });

  const [timeLeft, setTimeLeft] = useState<string>('--:--');
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<any>(null);

  const deadline = new Date(attempt.deadline_time).getTime();

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date().getTime();
      const diff = deadline - now;

      if (diff <= 0) {
        setTimeLeft('00:00');
        clearInterval(timerRef.current);
        handleAutoSubmit();
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeLeft(
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      );
    };

    updateTimer();
    timerRef.current = setInterval(updateTimer, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleSelectOption = (letter: string) => {
    const currentQ = questions[currentIndex];
    const newAnswers = { ...answers, [currentQ.id]: letter };
    setAnswers(newAnswers);

    // Autosave to backend
    apiService.saveAnswer(attempt.attempt_id, currentQ.id, letter);
  };

  const handleAutoSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    const res = await apiService.finishQuiz(attempt.attempt_id);
    if (res.success && res.data) {
      navigation.replace('Result', { attemptId: attempt.attempt_id });
    } else {
      navigation.replace('Result', { attemptId: attempt.attempt_id });
    }
  };

  const confirmSubmit = () => {
    const answeredCount = Object.values(answers).filter(Boolean).length;
    const unanswered = questions.length - answeredCount;

    let msg = 'Are you ready to submit your assessment?';
    if (unanswered > 0) {
      msg = `You have ${unanswered} unanswered question(s). Are you sure you want to finish and submit now?`;
    }

    Alert.alert('Submit Assessment', msg, [
      { text: 'Review Questions', style: 'cancel' },
      { text: 'Submit Exam', style: 'destructive', onPress: handleAutoSubmit },
    ]);
  };

  const currentQ = questions[currentIndex];
  const selectedOpt = answers[currentQ?.id] || null;

  return (
    <View style={styles.container}>
      {/* Top Header Bar */}
      <View style={styles.topBar}>
        <View style={styles.topBarLeft}>
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>ASSESSMENT EXAM</Text>
          </View>
          <Text style={styles.quizName} numberOfLines={1}>
            {attempt.quiz_title}
          </Text>
        </View>

        {/* Circular / Rounded Timer Gauge Pill */}
        <View style={styles.timerBadge}>
          <Text style={styles.timerIcon}>⏱</Text>
          <Text style={styles.timerValue}>{timeLeft}</Text>
        </View>
      </View>

      {/* Horizontal Question Navigator Palette */}
      <View style={styles.paletteContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.paletteScroll}>
          {questions.map((q, idx) => {
            const isAnswered = Boolean(answers[q.id]);
            const isCurrent = idx === currentIndex;
            return (
              <TouchableOpacity
                key={q.id}
                style={[
                  styles.paletteItem,
                  isAnswered && styles.paletteAnswered,
                  isCurrent && styles.paletteCurrent,
                ]}
                onPress={() => setCurrentIndex(idx)}
              >
                <Text
                  style={[
                    styles.paletteText,
                    isAnswered && styles.paletteAnsweredText,
                    isCurrent && styles.paletteCurrentText,
                  ]}
                >
                  {idx + 1}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Question Card */}
      <ScrollView style={styles.scrollArea} contentContainerStyle={styles.cardContent}>
        <View style={styles.questionCard}>
          <View style={styles.qHeader}>
            <View style={styles.qBadge}>
              <Text style={styles.qBadgeText}>
                Question {currentIndex + 1} of {questions.length}
              </Text>
            </View>
            <View style={styles.marksBadge}>
              <Text style={styles.marksText}>{currentQ.marks} Mark(s)</Text>
            </View>
          </View>

          <Text style={styles.qText}>{currentQ.question_text}</Text>

          {/* Interactive Option Cards */}
          <View style={styles.optionsList}>
            {[
              { opt: 'A', text: currentQ.option_a },
              { opt: 'B', text: currentQ.option_b },
              { opt: 'C', text: currentQ.option_c },
              { opt: 'D', text: currentQ.option_d },
            ].map((item) => {
              const isSelected = selectedOpt === item.opt;
              return (
                <TouchableOpacity
                  key={item.opt}
                  activeOpacity={0.7}
                  style={[styles.optionCard, isSelected && styles.optionCardSelected]}
                  onPress={() => handleSelectOption(item.opt)}
                >
                  <View style={[styles.letterCircle, isSelected && styles.letterCircleSelected]}>
                    <Text style={[styles.letterText, isSelected && styles.letterTextSelected]}>
                      {item.opt}
                    </Text>
                  </View>
                  <Text style={[styles.optionText, isSelected && styles.optionTextSelected]}>
                    {item.text}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </ScrollView>

      {/* Bottom Action Bar */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.navBtn, currentIndex === 0 && styles.navBtnDisabled]}
          disabled={currentIndex === 0}
          onPress={() => setCurrentIndex((prev) => prev - 1)}
        >
          <Text style={styles.navBtnText}>◀ Back</Text>
        </TouchableOpacity>

        <View style={styles.pageIndicator}>
          <Text style={styles.pageIndicatorText}>
            {currentIndex + 1} / {questions.length}
          </Text>
        </View>

        {currentIndex < questions.length - 1 ? (
          <TouchableOpacity
            style={[styles.navBtn, styles.navBtnPrimary]}
            onPress={() => setCurrentIndex((prev) => prev + 1)}
          >
            <Text style={styles.navBtnPrimaryText}>Next ▶</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.navBtn, styles.submitBtn]}
            onPress={confirmSubmit}
            disabled={submitting}
          >
            {submitting ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.submitBtnText}>Submit Exam ✓</Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.BG_MAIN,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
    backgroundColor: Theme.BG_CARD,
    borderBottomWidth: 1,
    borderBottomColor: Theme.BORDER,
  },
  topBarLeft: {
    flex: 1,
    marginRight: 10,
  },
  typeBadge: {
    alignSelf: 'flex-start',
    backgroundColor: Theme.PRIMARY_LIGHT,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 4,
  },
  typeBadgeText: {
    color: Theme.PRIMARY,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  quizName: {
    fontSize: 15,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
  },
  timerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Theme.PURPLE_LIGHT,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Theme.PURPLE,
  },
  timerIcon: {
    fontSize: 14,
    marginRight: 4,
  },
  timerValue: {
    color: Theme.PURPLE,
    fontSize: 14,
    fontWeight: '700',
  },
  paletteContainer: {
    backgroundColor: Theme.BG_CARD,
    borderBottomWidth: 1,
    borderBottomColor: Theme.BORDER,
    paddingVertical: 8,
  },
  paletteScroll: {
    paddingHorizontal: 14,
    gap: 8,
  },
  paletteItem: {
    width: 34,
    height: 34,
    borderRadius: 8,
    backgroundColor: Theme.BG_MAIN,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    justifyContent: 'center',
    alignItems: 'center',
  },
  paletteAnswered: {
    backgroundColor: Theme.SUCCESS_LIGHT,
    borderColor: Theme.SUCCESS,
  },
  paletteCurrent: {
    borderColor: Theme.PRIMARY,
    borderWidth: 2,
    backgroundColor: Theme.PRIMARY_LIGHT,
  },
  paletteText: {
    color: Theme.TEXT_MUTED,
    fontSize: 13,
    fontWeight: 'bold',
  },
  paletteAnsweredText: {
    color: Theme.SUCCESS,
  },
  paletteCurrentText: {
    color: Theme.PRIMARY,
  },
  scrollArea: {
    flex: 1,
  },
  cardContent: {
    padding: 16,
  },
  questionCard: {
    backgroundColor: Theme.BG_CARD,
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  qHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  qBadge: {
    backgroundColor: Theme.PRIMARY_LIGHT,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  qBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Theme.PRIMARY,
  },
  marksBadge: {
    backgroundColor: Theme.BG_MAIN,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: Theme.BORDER,
  },
  marksText: {
    fontSize: 12,
    color: Theme.TEXT_MUTED,
    fontWeight: '600',
  },
  qText: {
    fontSize: 16,
    fontWeight: '600',
    color: Theme.TEXT_MAIN,
    lineHeight: 23,
    marginBottom: 18,
  },
  optionsList: {
    gap: 10,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Theme.BG_CARD,
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: Theme.BORDER,
  },
  optionCardSelected: {
    borderColor: Theme.PURPLE,
    backgroundColor: Theme.PURPLE_LIGHT,
    borderWidth: 1.5,
  },
  letterCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Theme.BG_MAIN,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  letterCircleSelected: {
    backgroundColor: Theme.PURPLE,
    borderColor: Theme.PURPLE,
  },
  letterText: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Theme.TEXT_MUTED,
  },
  letterTextSelected: {
    color: '#FFFFFF',
  },
  optionText: {
    fontSize: 14,
    color: Theme.TEXT_MAIN,
    flex: 1,
    lineHeight: 20,
  },
  optionTextSelected: {
    color: Theme.PURPLE,
    fontWeight: '600',
  },
  bottomBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    backgroundColor: Theme.BG_CARD,
    borderTopWidth: 1,
    borderTopColor: Theme.BORDER,
  },
  pageIndicator: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: Theme.BG_MAIN,
  },
  pageIndicatorText: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Theme.TEXT_MUTED,
  },
  navBtn: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 8,
    backgroundColor: Theme.BG_MAIN,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    minWidth: 84,
    alignItems: 'center',
  },
  navBtnDisabled: {
    opacity: 0.35,
  },
  navBtnText: {
    color: Theme.TEXT_MAIN,
    fontSize: 13,
    fontWeight: '600',
  },
  navBtnPrimary: {
    backgroundColor: Theme.PRIMARY,
    borderColor: Theme.PRIMARY,
  },
  navBtnPrimaryText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  submitBtn: {
    backgroundColor: Theme.SUCCESS,
    borderColor: Theme.SUCCESS,
  },
  submitBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
});
