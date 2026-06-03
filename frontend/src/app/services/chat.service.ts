import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = window.location.origin.includes('localhost:4200')
    ? 'http://localhost:8000/api/v1/chat'
    : '/api/v1/chat';

  constructor(private http: HttpClient) {}

  sendMessage(message: string, conversationId?: number): Observable<any> {
    const payload: any = { message };
    if (conversationId) {
      payload.conversation_id = conversationId;
    }
    return this.http.post(`${this.apiUrl}`, payload);
  }

  listConversations(page = 1, pageSize = 20): Observable<any> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get(`${this.apiUrl}/conversations`, { params });
  }

  getConversationHistory(conversationId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/conversations/${conversationId}`);
  }

  deleteConversation(conversationId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/conversations/${conversationId}`);
  }
}
