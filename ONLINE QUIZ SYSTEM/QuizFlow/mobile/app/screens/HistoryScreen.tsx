import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { apiService } from '../../services/api';
import { AttemptSummary } from '../../types';
import { Theme } from '../../theme';

export const HistoryScreen = ({ navigation }: { navigation: any }) => {
  const [history, setHistory] = useState<AttemptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadHistory = async () => {
    const res = await apiService.getMyHistory();
    if (res.success && res.data) {
      setHistory(res.data);
    }
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadHistory();
  };

  const renderItem = ({ item }: { item: AttemptSummary }) => {
    const isPass = item.is_passed;
    return (
      <View style={styles.card}>
        <View style={styles.row}>
          <View style={styles.left}>
            <Text style={styles.title}>{item.quiz_title}</Text>
            <Text style={styles.scoreText}>
              Score: {item.score_obtained} / {item.total_marks} ({item.percentage}%)
            </Text>
          </View>

          <View
            style={[
              styles.badge,
              isPass ? styles.badgePass : styles.badgeFail,
            ]}
          >
            <Text style={[styles.badgeText, isPass ? styles.badgeTextPass : styles.badgeTextFail]}>
              {isPass ? 'PASSED' : 'NOT PASSED'}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.reviewBtn}
          activeOpacity={0.8}
          onPress={() => navigation.navigate('Result', { attemptId: item.attempt_id })}
        >
          <Text style={styles.reviewBtnText}>Review Solutions & Score Breakdown →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Attempt History</Text>
        <Text style={styles.headerSub}>Review your past assessment scores and answers</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Theme.PRIMARY} />
        </View>
      ) : (
        <FlatList
          data={history}
          keyExtractor={(item) => item.attempt_id.toString()}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Theme.PRIMARY} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyIcon}>📊</Text>
              <Text style={styles.emptyTitle}>No Attempts Recorded</Text>
              <Text style={styles.emptyText}>Complete a quiz from the dashboard to see your history.</Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.BG_MAIN,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
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
  list: {
    padding: 16,
    paddingTop: 8,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
  },
  card: {
    backgroundColor: Theme.BG_CARD,
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Theme.BORDER,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  left: {
    flex: 1,
    marginRight: 10,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Theme.TEXT_MAIN,
  },
  scoreText: {
    fontSize: 13,
    color: Theme.TEXT_MUTED,
    marginTop: 4,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgePass: {
    backgroundColor: Theme.SUCCESS_LIGHT,
    borderWidth: 1,
    borderColor: Theme.SUCCESS,
  },
  badgeFail: {
    backgroundColor: Theme.DANGER_LIGHT,
    borderWidth: 1,
    borderColor: Theme.DANGER,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  badgeTextPass: {
    color: Theme.SUCCESS,
  },
  badgeTextFail: {
    color: Theme.DANGER,
  },
  reviewBtn: {
    backgroundColor: Theme.PRIMARY_LIGHT,
    borderRadius: 8,
    paddingVertical: 9,
    alignItems: 'center',
  },
  reviewBtnText: {
    color: Theme.PRIMARY,
    fontSize: 13,
    fontWeight: '700',
  },
  emptyIcon: {
    fontSize: 36,
    marginBottom: 10,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Theme.TEXT_MAIN,
    marginBottom: 4,
  },
  emptyText: {
    color: Theme.TEXT_MUTED,
    fontSize: 13,
    textAlign: 'center',
  },
});
