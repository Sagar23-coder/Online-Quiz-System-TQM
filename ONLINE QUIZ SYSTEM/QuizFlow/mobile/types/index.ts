export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Quiz {
  id: number;
  title: string;
  description?: string;
  instructions?: string;
  join_code?: string;
  is_public?: boolean;
  max_attempts?: number;
  release_results_immediately?: boolean;
  results_released?: boolean;
  duration_minutes: number;
  passing_percentage: number;
  total_marks: number;
  question_count: number;
}

export interface Question {
  id: number;
  quiz_id: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  marks: number;
  order_index: number;
}

export interface AttemptStartData {
  attempt_id: number;
  quiz_id: number;
  quiz_title: string;
  duration_minutes: number;
  start_time: string;
  deadline_time: string;
  questions: Question[];
  saved_answers: Record<string, string | null>;
}

export interface QuestionReview {
  question_id: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  selected_option: string | null;
  correct_option: string;
  is_correct: boolean;
  marks_awarded: number;
  max_marks: number;
  explanation?: string;
}

export interface AttemptResult {
  attempt_id: number;
  quiz_id: number;
  quiz_title: string;
  student_name: string;
  status: string;
  start_time: string;
  end_time?: string;
  deadline_time: string;
  score_obtained: number;
  total_marks: number;
  percentage: number;
  passing_percentage: number;
  is_passed: boolean;
  results_released?: boolean;
  total_questions: number;
  correct_count: number;
  incorrect_count: number;
  unattempted_count: number;
  review?: QuestionReview[];
}

export interface AttemptSummary {
  attempt_id: number;
  quiz_id: number;
  quiz_title: string;
  status: string;
  start_time: string;
  end_time?: string;
  score_obtained: number;
  total_marks: number;
  percentage: number;
  is_passed: boolean;
}

export type RootStackParamList = {
  Auth: undefined;
  MainTabs: undefined;
  QuizDetail: { quiz: Quiz };
  QuizActive: { attempt: AttemptStartData };
  Result: { attemptId: number };
};

export type MainTabParamList = {
  Dashboard: undefined;
  History: undefined;
  Profile: undefined;
};

