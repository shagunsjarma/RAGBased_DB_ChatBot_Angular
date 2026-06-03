import { Component, OnInit, AfterViewChecked, ElementRef, ViewChild, ViewChildren, QueryList } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ChatService } from '../../services/chat.service';

declare const Plotly: any;

@Component({
  selector: 'app-chat-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="app-layout">
      <!-- 1. LEFT SIDEBAR -->
      <aside class="sidebar glass-panel">
        <div class="sidebar-header">
          <div class="logo">
            <i class="fas fa-brain neon-text-glow"></i>
            <h2>RAG ChatBOT</h2>
          </div>
          <button class="new-chat-btn glowing-btn" (click)="startNewChat()">
            <i class="fas fa-plus"></i> New Conversation
          </button>
        </div>

        <div class="conversations-list">
          <div class="section-title">Recent Chats</div>
          <div class="conversations-scroll">
            <div 
              *ngFor="let chat of conversations" 
              class="conversation-item"
              [class.active]="chat.id === activeConversationId"
              (click)="loadConversation(chat.id)">
              <i class="far fa-comments"></i>
              <span class="chat-title">{{ chat.title || 'Untitled Conversation' }}</span>
              <button class="delete-chat-btn" (click)="deleteConversation($event, chat.id)">
                <i class="far fa-trash-alt"></i>
              </button>
            </div>
            <div *ngIf="conversations.length === 0" class="empty-state">
              No conversations yet.
            </div>
          </div>
        </div>

        <div class="sidebar-footer">
          <div class="user-profile" *ngIf="currentUser">
            <div class="avatar">
              <i class="fas fa-user-astronaut"></i>
            </div>
            <div class="user-info">
              <span class="username">{{ currentUser.full_name || 'Database Analyst' }}</span>
              <span class="email">{{ currentUser.email }}</span>
            </div>
          </div>
          <button class="logout-btn" (click)="logout()">
            <i class="fas fa-sign-out-alt"></i> Logout
          </button>
        </div>
      </aside>

      <!-- 2. MAIN CHAT SECTION -->
      <main class="main-content">
        <div class="chat-container">
          <!-- Chat Feed -->
          <div class="chat-feed" #feedScrollContainer>
            <div *ngIf="messages.length === 0" class="welcome-banner glass-card">
              <i class="fas fa-database welcome-icon neon-text-glow"></i>
              <h2>Intelligent SQL Query Assistant</h2>
              <p>Ask natural language questions to analyze your Chinook database. View generated SQL, interactive dashboards, and statistical forecasting instantly.</p>
              
              <div class="suggested-queries">
                <div class="section-title">Try These Questions</div>
                <div class="suggestions-grid">
                  <button 
                    *ngFor="let q of suggestedQueries" 
                    class="suggestion-chip"
                    (click)="sendSuggestedQuery(q)">
                    {{ q }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Message Log -->
            <div 
              *ngFor="let msg of messages; let lastMsg = last" 
              class="message-wrapper" 
              [class.user-message]="msg.role === 'user'"
              [class.assistant-message]="msg.role === 'assistant'">
              
              <div class="message-bubble glass-card">
                <div class="message-header">
                  <span class="sender-name">
                    <i class="fas" [class.fa-user]="msg.role === 'user'" [class.fa-robot]="msg.role === 'assistant'"></i>
                    {{ msg.role === 'user' ? 'You' : 'Assistant' }}
                  </span>
                  <span class="timestamp">{{ msg.created_at | date:'shortTime' }}</span>
                </div>

                <!-- Text Content -->
                <div class="message-content">
                  <p class="body-text">{{ msg.content }}</p>
                </div>

                <!-- SQL & Data Result Blocks (Only for assistant messages with metadata) -->
                <div class="metadata-block" *ngIf="msg.role === 'assistant' && msg.metadata_json">
                  
                  <!-- SQL Section -->
                  <div class="sql-accordion" *ngIf="msg.metadata_json.sql_query">
                    <button class="accordion-header" (click)="msg._showSQL = !msg._showSQL">
                      <span><i class="fas fa-code"></i> Generated SQL Query</span>
                      <i class="fas" [class.fa-chevron-down]="!msg._showSQL" [class.fa-chevron-up]="msg._showSQL"></i>
                    </button>
                    <div class="accordion-content" *ngIf="msg._showSQL">
                      <div class="sql-code-container">
                        <pre><code>{{ msg.metadata_json.sql_query }}</code></pre>
                        <button class="copy-btn" (click)="copyToClipboard(msg.metadata_json.sql_query)">
                          <i class="far fa-copy"></i> Copy
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Table Results Section -->
                  <div class="results-table-container" *ngIf="msg.metadata_json.query_results?.length > 0">
                    <div class="table-header-bar">
                      <span><i class="fas fa-table"></i> Query Results ({{ msg.metadata_json.query_results.length }} rows)</span>
                    </div>
                    <div class="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th *ngFor="let col of getTableHeaders(msg.metadata_json.query_results)">{{ col }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr *ngFor="let row of msg.metadata_json.query_results | slice:0:10">
                            <td *ngFor="let col of getTableHeaders(msg.metadata_json.query_results)">{{ getCellValue(row, col) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="table-footer-bar" *ngIf="msg.metadata_json.query_results.length > 10">
                      <span>Showing first 10 rows.</span>
                    </div>
                  </div>

                </div>
              </div>

              <!-- Follow Up Suggestions -->
              <div 
                class="follow-ups-container" 
                *ngIf="msg.role === 'assistant' && msg.metadata_json?.follow_up_suggestions?.length > 0 && lastMsg">
                <span class="follow-up-label">Follow-up:</span>
                <button 
                  *ngFor="let followUp of msg.metadata_json.follow_up_suggestions" 
                  class="follow-up-chip"
                  (click)="sendSuggestedQuery(followUp)">
                  {{ followUp }}
                </button>
              </div>

            </div>

            <!-- Loader / Typing bubble -->
            <div class="message-wrapper assistant-message" *ngIf="typing">
              <div class="message-bubble glass-card typing-bubble">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Message Input area -->
          <footer class="chat-input-bar glass-panel">
            <form (ngSubmit)="sendMessage()" class="input-form">
              <input 
                type="text" 
                name="messageText"
                [(ngModel)]="messageText" 
                placeholder="Ask about sales, customers, tracks, or dashboards..." 
                [disabled]="typing"
                autocomplete="off">
              <button type="submit" class="send-btn glowing-btn" [disabled]="typing || !messageText.trim()">
                <i class="fas fa-paper-plane"></i>
              </button>
            </form>
          </footer>
        </div>
      </main>

      <!-- 3. RIGHT PANEL: DASHBOARD & INSIGHTS -->
      <section class="insights-panel glass-panel">
        <div class="panel-header">
          <h3><i class="fas fa-chart-line"></i> Dashboard & Insights</h3>
        </div>

        <div class="panel-content">
          <!-- Visualizations -->
          <div class="insight-section">
            <div class="section-title">Visualizations</div>
            <div class="visualizations-container">
              <div *ngIf="!latestVisualizations || latestVisualizations.length === 0" class="empty-viz-state glass-card">
                <i class="far fa-chart-bar viz-icon"></i>
                <p>Submit a query to generate interactive charts.</p>
              </div>
              <div 
                *ngFor="let viz of latestVisualizations; let i = index" 
                class="chart-card glass-card">
                <div class="chart-title-bar">
                  <span class="chart-title">{{ viz.title || 'Dynamic Chart' }}</span>
                </div>
                <div [id]="'chart-container-' + i" class="plotly-chart-box"></div>
              </div>
            </div>
          </div>

          <!-- Statistical Analysis / AI Insights -->
          <div class="insight-section" *ngIf="latestInsights">
            <div class="section-title">AI Statistical Insights</div>
            <div class="insights-scroll">
              <!-- Summary Card -->
              <div class="insight-card summary-card glass-card">
                <div class="insight-card-header text-purple">
                  <i class="fas fa-compress-alt"></i> Executive Summary
                </div>
                <p>{{ latestInsights.summary }}</p>
              </div>

              <!-- Trends Card -->
              <div class="insight-card trends-card glass-card" *ngIf="latestInsights.trends?.length > 0">
                <div class="insight-card-header text-green">
                  <i class="fas fa-chart-line"></i> Key Trends
                </div>
                <ul>
                  <li *ngFor="let trend of latestInsights.trends">{{ trend }}</li>
                </ul>
              </div>

              <!-- Anomalies Card -->
              <div class="insight-card anomalies-card glass-card" *ngIf="latestInsights.anomalies?.length > 0">
                <div class="insight-card-header text-red">
                  <i class="fas fa-exclamation-circle"></i> Flagged Anomalies
                </div>
                <ul>
                  <li *ngFor="let anomaly of latestInsights.anomalies">{{ anomaly }}</li>
                </ul>
              </div>

              <!-- Recommendations Card -->
              <div class="insight-card recommendations-card glass-card" *ngIf="latestInsights.recommendations?.length > 0">
                <div class="insight-card-header text-cyan">
                  <i class="fas fa-lightbulb"></i> Recommendations
                </div>
                <ul>
                  <li *ngFor="let rec of latestInsights.recommendations">{{ rec }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  `,
  styles: []
})
export class ChatDashboardComponent implements OnInit, AfterViewChecked {
  @ViewChild('feedScrollContainer') private feedScroll!: ElementRef;

  currentUser: any = null;
  conversations: any[] = [];
  messages: any[] = [];
  activeConversationId: number | null = null;
  messageText = '';
  typing = false;
  
  latestVisualizations: any[] = [];
  latestInsights: any = null;

  suggestedQueries = [
    'List top 5 customers by total spending',
    'Show monthly sales trends by year',
    'Count invoices by billing country',
    'List the top 5 tracks in terms of sales',
    'Display total revenue grouped by genre'
  ];

  constructor(
    private authService: AuthService,
    private chatService: ChatService,
    private router: Router
  ) {}

  ngOnInit(): void {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
      return;
    }

    this.authService.getMe().subscribe({
      next: (user) => this.currentUser = user,
      error: () => this.logout()
    });

    this.loadConversationsList();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  loadConversationsList(): void {
    this.chatService.listConversations().subscribe({
      next: (res) => {
        this.conversations = res.conversations || [];
      }
    });
  }

  startNewChat(): void {
    this.activeConversationId = null;
    this.messages = [];
    this.latestVisualizations = [];
    this.latestInsights = null;
  }

  loadConversation(id: number): void {
    this.activeConversationId = id;
    this.chatService.getConversationHistory(id).subscribe({
      next: (res) => {
        // Parse metadata_json for templates
        this.messages = (res.messages || []).map((m: any) => {
          if (m.metadata_json && typeof m.metadata_json === 'string') {
            try {
              m.metadata_json = JSON.parse(m.metadata_json);
            } catch (e) {}
          }
          m._showSQL = false;
          return m;
        });

        // Set visual panel based on last assistant reply
        const assistantMsgs = this.messages.filter(m => m.role === 'assistant');
        if (assistantMsgs.length > 0) {
          const lastMsg = assistantMsgs[assistantMsgs.length - 1];
          this.latestVisualizations = lastMsg.metadata_json?.visualizations || [];
          this.latestInsights = lastMsg.metadata_json?.insights || null;
          this.renderPlotlyCharts();
        } else {
          this.latestVisualizations = [];
          this.latestInsights = null;
        }
      }
    });
  }

  deleteConversation(event: MouseEvent, id: number): void {
    event.stopPropagation();
    this.chatService.deleteConversation(id).subscribe({
      next: () => {
        this.loadConversationsList();
        if (this.activeConversationId === id) {
          this.startNewChat();
        }
      }
    });
  }

  sendMessage(): void {
    const text = this.messageText.trim();
    if (!text || this.typing) return;

    // Push user message immediately
    const userMsg = {
      role: 'user',
      content: text,
      created_at: new Date().toISOString()
    };
    this.messages.push(userMsg);
    this.messageText = '';
    this.typing = true;
    this.scrollToBottom();

    // Call API
    this.chatService.sendMessage(text, this.activeConversationId || undefined).subscribe({
      next: (res) => {
        this.typing = false;
        
        // Structure Response
        const assistantMsg = {
          role: 'assistant',
          content: res.message,
          metadata_json: {
            sql_query: res.sql_query,
            query_results: res.query_results,
            visualizations: res.visualizations,
            insights: res.insights,
            follow_up_suggestions: res.follow_up_suggestions
          },
          created_at: new Date().toISOString(),
          _showSQL: false
        };

        this.messages.push(assistantMsg);
        
        // Set new Active Conversation ID if it was null
        if (!this.activeConversationId && res.conversation_id) {
          this.activeConversationId = res.conversation_id;
        }
        
        this.loadConversationsList();

        // Update Right Panels
        this.latestVisualizations = res.visualizations || [];
        this.latestInsights = res.insights || null;

        // Render charts after Angular completes DOM updates
        this.renderPlotlyCharts();
      },
      error: (err) => {
        this.typing = false;
        const errMsg = {
          role: 'assistant',
          content: `Error: ${err.error?.detail || err.error?.message || 'Failed to get response.'}`,
          created_at: new Date().toISOString()
        };
        this.messages.push(errMsg);
      }
    });
  }

  sendSuggestedQuery(query: string): void {
    this.messageText = query;
    this.sendMessage();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  getTableHeaders(results: any[]): string[] {
    if (!results || results.length === 0) return [];
    return Object.keys(results[0]);
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      alert('SQL query copied to clipboard!');
    });
  }

  renderPlotlyCharts(): void {
    if (this.latestVisualizations.length === 0) return;
    
    // Defer execution slightly to let DOM elements render
    setTimeout(() => {
      this.latestVisualizations.forEach((viz, index) => {
        const containerId = `chart-container-${index}`;
        const container = document.getElementById(containerId);
        if (!container) return;

        // Extract layout config & values
        const config = viz.chart_config || {};
        const chartType = viz.chart_type || 'bar';
        const xCol = config.x_column;
        const yCol = config.y_column;

        // Fetch query rows (extract from latest assistant reply)
        const assistantMsgs = this.messages.filter(m => m.role === 'assistant');
        if (assistantMsgs.length === 0) return;
        const latestReply = assistantMsgs[assistantMsgs.length - 1];
        const rows = latestReply.metadata_json?.query_results || [];

        if (rows.length === 0) return;

        const xValues = rows.map((r: any) => r[xCol]);
        const yValues = rows.map((r: any) => r[yCol]);

        let trace: any = {};
        const colors = ["#8b5cf6", "#06b6d4", "#6366f1", "#10b981", "#f59e0b"];

        if (chartType === 'line') {
          trace = {
            x: xValues,
            y: yValues,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: colors[0], width: 3 },
            marker: { size: 6, color: colors[1] }
          };
        } else if (chartType === 'scatter') {
          trace = {
            x: xValues,
            y: yValues,
            type: 'scatter',
            mode: 'markers',
            marker: { size: 10, color: colors[2], opacity: 0.7 }
          };
        } else if (chartType === 'pie') {
          trace = {
            labels: xValues,
            values: yValues,
            type: 'pie',
            hole: 0.4,
            marker: { colors: colors }
          };
        } else if (chartType === 'funnel') {
          trace = {
            y: xValues,
            x: yValues,
            type: 'funnel',
            marker: { color: colors[3] }
          };
        } else if (chartType === 'treemap') {
          trace = {
            type: 'treemap',
            labels: xValues,
            parents: xValues.map(() => ''),
            values: yValues,
            marker: { colors: colors }
          };
        } else {
          // Default Bar
          trace = {
            x: xValues,
            y: yValues,
            type: 'bar',
            marker: {
              color: colors[0],
              line: { width: 0 }
            }
          };
        }

        const layout = {
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          font: { color: '#94a3b8', family: 'Inter, sans-serif', size: 11 },
          xaxis: { 
            gridcolor: '#1e293b', 
            zeroline: false,
            tickangle: xValues.length > 8 ? -30 : 0
          },
          yaxis: { 
            gridcolor: '#1e293b', 
            zeroline: false 
          },
          margin: { l: 45, r: 15, t: 20, b: 40 },
          showlegend: chartType === 'pie'
        };

        Plotly.newPlot(containerId, [trace], layout, { responsive: true, displayModeBar: false });
      });
    }, 150);
  }

  getCellValue(row: any, col: string): any {
    return row ? row[col] : '';
  }

  private scrollToBottom(): void {
    try {
      this.feedScroll.nativeElement.scrollTop = this.feedScroll.nativeElement.scrollHeight;
    } catch (err) {}
  }
}
