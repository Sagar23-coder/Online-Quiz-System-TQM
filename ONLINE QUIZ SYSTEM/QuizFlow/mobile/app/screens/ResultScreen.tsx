import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { apiService } from '../../services/api';
import { AttemptResult } from '../../types';
import { Theme } from '../../theme';

export const ResultScreen = ({ route, navigation }: { route: any; navigation: any }) => {
  const { attemptId } = route.params as { attemptId: number };
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchResult = async () => {
      const res = await apiService.getResult(attemptId);
      if (res.success && res.data) {
        setResult(res.data);
      }
      setLoading(false);
    };
    fetchResult();
  }, [attemptId]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Theme.PRIMARY} />
        <Text style={styles.loadingText}>Grading assessment answers...</Text>
      </View>
    );
  }

  if (!result) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Unable to load attempt results.</Text>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.navigate('MainTabs')}>
          <Text style={styles.backBtnText}>Return to Dashboard</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isPass = result.is_passed;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      {/* Banner Card */}
      <View style={[styles.bannerCard, isPass ? styles.bannerPass : styles.bannerFail]}>
        <Text style={[styles.bannerVerdict, isPass ? styles.verdictPass : styles.verdictFail]}>
          {isPass ? 'CONGRATULATIONS! YOU PASSED' : 'ASSESSMENT NOT PASSED'}
        </Text>
        <Text style={styles.scoreText}>
          {result.score_obtained} / {result.total_marks} Marks ({result.percentage}%)
        </Text>
        <Text style={styles.reqText}>Passing Threshold Required: {result.passing_percentage}%</Text>

        <View style={styles.statsRow}>
          <View style={styles.statCol}>
            <Text style={[styles.statNum, { color: Theme.SUCCESS }]}>{result.correct_count}</Text>
            <Text style={styles.statLabel}>Correct</Text>
          </View>
          <View style={styles.statCol}>
            <Text style={[styles.statNum, { color: Theme.DANGER }]}>{result.incorrect_count}</Text>
            <Text style={styles.statLabel}>Incorrect</Text>
          </View>
          <View style={styles.statCol}>
            <Text style={[styles.statNum, { color: Theme.TEXT_MUTED }]}>{result.unattempted_count}</Text>
            <Text style={styles.statLabel}>Skipped</Text>
          </View>
        </View>
      </View>

      <TouchableOpacity
        style={styles.backDashboardBtn}
        activeOpacity={0.8}
        onPress={() => navigation.navigate('MainTabs')}
      >
        <Text style={styles.backDashboardBtnText}>← Return to Student Dashboard</Text>
      </TouchableOpacity>

      {/* Detailed Solutions or Held Banner */}
      {result.results_released === false ? (
        <View style={styles.heldCard}>
          <Text style={styles.heldTitle}>🔒 Solutions Review Pending</Text>
          <Text style={styles.heldText}>
            The quiz organizer has configured answer explanations to be released after evaluation. Your attempt has been safely saved. Solutions will appear here once released by the instructor.
          </Text>
        </View>
      ) : (
        <>
          <Text style={styles.reviewHeading}>Question Solutions & Explanations</Text>

          {result.review?.map((item, idx) => {
            const isCorrect = item.is_correct;
            const isSkipped = item.selected_option === null;

            return (
              <View key={item.question_id} style={styles.qReviewCard}>
                <View style={styles.qReviewHeader}>
                  <Text style={styles.qReviewNum}>Q{idx + 1}.</Text>
                  <View
                    style={[
                      styles.badge,
                      isSkipped ? styles.badgeSkipped : isCorrect ? styles.badgeCorrect : styles.badgeIncorrect,
                    ]}
                  >
                    <Text
                      style={[
                        styles.badgeText,
                        isSkipped
                          ? styles.badgeTextSkipped
                          : isCorrect
                          ? styles.badgeTextCorrect
                          : styles.badgeTextIncorrect,
                      ]}
                    >
                      {isSkipped
                        ? 'SKIPPED (0 Marks)'
                        : isCorrect
                        ? `CORRECT (+${item.marks_awarded} Marks)`
                        : 'INCORRECT (0 Marks)'}
                    </Text>
                  </View>
                </View>

                <Text style={styles.qReviewText}>{item.question_text}</Text>

                {/* Options */}
                {[
                  { opt: 'A', text: item.option_a },
                  { opt: 'B', text: item.option_b },
                  { opt: 'C', text: item.option_c },
                  { opt: 'D', text: item.option_d },
                ].map((o) => {
                  const isCorrectOpt = o.opt === item.correct_option;
                  const isUserOpt = o.opt === item.selected_option;

                  return (
                    <View
                      key={o.opt}
                      style={[
                        styles.optRow,
                        isCorrectOpt && styles.optCorrect,
                        isUserOpt && !isCorrect && styles.optUserIncorrect,
                      ]}
                    >
                      <Text
                        style={[
                          styles.optRowText,
                          isCorrectOpt && styles.optCorrectText,
                          isUserOpt && !isCorrect && styles.optUserIncorrectText,
                        ]}
                      >
                        ({o.opt}) {o.text}
                        {isCorrectOpt ? '  ✓ Correct Answer' : ''}
                        {isUserOpt && !isCorrect ? '  ✗ Your Selection' : ''}
                      </Text>
                    </View>
                  );
                })}

                {item.explanation ? (
                  <View style={styles.expBox}>
                    <Text style={styles.expTitle}>Explanation:</Text>
                    <Text style={styles.expText}>{item.explanation}</Text>
                  </View>
                ) : null}
              </View>
            );
          })}

          <TouchableOpacity
            style={[styles.backDashboardBtn, { marginTop: 16 }]}
            activeOpacity={0.8}
            onPress={() => navigation.navigate('MainTabs')}
          >
            <Text style={styles.backDashboardBtnText}>← Return to Student Dashboard</Text>
          </TouchableOpacity>
        </>
      )}
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
    paddingBottom: 36,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: Theme.TEXT_MUTED,
  },
  errorText: {
    color: Theme.DANGER,
    fontSize: 15,
    marginBottom: 16,
  },
  backBtn: {
    backgroundColor: Theme.PRIMARY,
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 8,
  },
  backBtnText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  bannerCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 14,
    borderWidth: 1,
  },
  bannerPass: {
    backgroundColor: Theme.SUCCESS_LIGHT,
    borderColor: Theme.SUCCESS,
  },
  bannerFail: {
    backgroundColor: Theme.DANGER_LIGHT,
    borderColor: Theme.DANGER,
  },
  bannerVerdict: {
    fontSize: 14,
    fontWeight: 'bold',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  verdictPass: {
    color: Theme.SUCCESS,
  },
  verdictFail: {
    color: Theme.DANGER,
  },
  scoreText: {
    fontSize: 22,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
  },
  reqText: {
    fontSize: 12,
    color: Theme.TEXT_MUTED,
    marginTop: 2,
    marginBottom: 14,
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 8,
    justifyContent: 'space-around',
  },
  statCol: {
    alignItems: 'center',
    flex: 1,
  },
  statNum: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 11,
    color: Theme.TEXT_MUTED,
    marginTop: 2,
  },
  backDashboardBtn: {
    backgroundColor: Theme.PRIMARY,
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
    marginBottom: 20,
  },
  backDashboardBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  reviewHeading: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
    marginBottom: 12,
  },
  qReviewCard: {
    backgroundColor: Theme.BG_CARD,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    marginBottom: 12,
  },
  qReviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  qReviewNum: {
    fontSize: 14,
    fontWeight: 'bold',
    color: Theme.PRIMARY,
  },
  badge: {
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  badgeCorrect: {
    backgroundColor: Theme.SUCCESS_LIGHT,
  },
  badgeTextCorrect: {
    color: Theme.SUCCESS,
    fontSize: 11,
    fontWeight: 'bold',
  },
  badgeIncorrect: {
    backgroundColor: Theme.DANGER_LIGHT,
  },
  badgeTextIncorrect: {
    color: Theme.DANGER,
    fontSize: 11,
    fontWeight: 'bold',
  },
  badgeSkipped: {
    backgroundColor: Theme.BG_MAIN,
  },
  badgeTextSkipped: {
    color: Theme.TEXT_MUTED,
    fontSize: 11,
    fontWeight: 'bold',
  },
  qReviewText: {
    fontSize: 15,
    fontWeight: '600',
    color: Theme.TEXT_MAIN,
    lineHeight: 21,
    marginBottom: 12,
  },
  optRow: {
    backgroundColor: Theme.BG_MAIN,
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    marginBottom: 6,
  },
  optCorrect: {
    backgroundColor: Theme.SUCCESS_LIGHT,
    borderColor: Theme.SUCCESS,
  },
  optUserIncorrect: {
    backgroundColor: Theme.DANGER_LIGHT,
    borderColor: Theme.DANGER,
  },
  optRowText: {
    fontSize: 13,
    color: Theme.TEXT_MAIN,
  },
  optCorrectText: {
    color: Theme.SUCCESS,
    fontWeight: 'bold',
  },
  optUserIncorrectText: {
    color: Theme.DANGER,
    fontWeight: 'bold',
  },
  expBox: {
    backgroundColor: Theme.PURPLE_LIGHT,
    borderRadius: 8,
    padding: 10,
    marginTop: 8,
    borderWidth: 1,
    borderColor: Theme.PURPLE,
  },
  expTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Theme.PURPLE,
    marginBottom: 2,
  },
  expText: {
    fontSize: 12,
    color: Theme.TEXT_MAIN,
    lineHeight: 17,
  },
  heldCard: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: Theme.WARNING,
  },
  heldTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#92400E',
    marginBottom: 6,
  },
  heldText: {
    fontSize: 13,
    color: '#92400E',
    lineHeight: 18,
  },
});
