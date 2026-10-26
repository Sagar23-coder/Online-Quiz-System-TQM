import { networkConfig } from './config';
import { User, Quiz, AttemptStartData, AttemptResult, AttemptSummary } from '../types';

class ApiService {
  private token: string | null = null;
  private currentUser: User | null = null;

  setToken(t: string | null) {
    this.token = t;
  }

  getToken(): string | null {
    return this.token;
  }

  setUser(u: User | null) {
    this.currentUser = u;
  }

  getUser(): User | null {
    return this.currentUser;
  }

  private async request<T>(
    path: string,
    method: string = 'GET',
    body?: any
  ): Promise<{ success: boolean; data?: T; error?: string }> {
    const url = `${networkConfig.apiUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      const json = await response.json().catch(() => null);

      if (response.ok) {
        return { success: true, data: json };
      } else {
        const errorMsg = json?.detail || `Error (${response.status}): ${response.statusText}`;
        return { success: false, error: typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg) };
      }
    } catch (err: any) {
      return {
        success: false,
        error: `Network request failed. Ensure backend is running at ${networkConfig.apiUrl}. Details: ${err.message}`,
      };
    }
  }

  async checkHealth() {
    return this.request<{ status: string; database: string }>('/health');
  }

  async login(email: string, password: string) {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', 'POST', {
      email,
      password,
    });
    if (res.success && res.data) {
      this.setToken(res.data.access_token);
      this.setUser(res.data.user);
    }
    return res;
  }

  async register(
    email: string,
    full_name: string,
    password: string,
    confirm_password: string,
    role: string = 'participant'
  ) {
    return this.request<User>('/auth/register', 'POST', {
      email,
      full_name,
      password,
      confirm_password,
      role,
    });
  }

  logout() {
    this.token = null;
    this.currentUser = null;
  }

  async getPublishedQuizzes() {
    return this.request<Quiz[]>('/quizzes');
  }

  async getQuizByCode(joinCode: string) {
    return this.request<Quiz>(`/quizzes/by-code/${joinCode.trim().toUpperCase()}`);
  }

  async joinQuizByCode(joinCode: string) {
    return this.request<Quiz>('/quizzes/join-by-code', 'POST', {
      join_code: joinCode.trim().toUpperCase(),
    });
  }

  async getQuizDetails(quizId: number) {
    return this.request<Quiz>(`/quizzes/${quizId}`);
  }

  async startQuiz(quizId: number) {
    return this.request<AttemptStartData>(`/attempts/quizzes/${quizId}/start`, 'POST');
  }

  async saveAnswer(attemptId: number, questionId: number, selectedOption: string | null) {
    return this.request<{ saved: boolean }>(`/attempts/${attemptId}/answers`, 'POST', {
      question_id: questionId,
      selected_option: selectedOption,
    });
  }

  async finishQuiz(attemptId: number) {
    return this.request<AttemptResult>(`/attempts/${attemptId}/finish`, 'POST');
  }

  async getResult(attemptId: number) {
    return this.request<AttemptResult>(`/attempts/${attemptId}/result`);
  }

  async getMyHistory() {
    return this.request<AttemptSummary[]>('/attempts/my-history');
  }
}

export const apiService = new ApiService();

