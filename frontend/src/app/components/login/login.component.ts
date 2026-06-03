import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-container">
      <div class="glow-sphere sphere-1"></div>
      <div class="glow-sphere sphere-2"></div>
      
      <div class="glass-card login-card">
        <div class="card-header">
          <div class="logo">
            <i class="fas fa-brain neon-text-glow"></i>
            <h2>RAG ChatBOT</h2>
          </div>
          <p class="subtitle">Natural Language SQL & Visualization Hub</p>
        </div>

        <!-- Toggle Tabs -->
        <div class="tab-container">
          <button [class.active]="isLoginMode" (click)="setMode(true)">Sign In</button>
          <button [class.active]="!isLoginMode" (click)="setMode(false)">Register</button>
        </div>

        <form (ngSubmit)="onSubmit()" #authForm="ngForm" class="auth-form">
          <div class="error-banner" *ngIf="errorMessage">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ errorMessage }}</span>
          </div>

          <div class="success-banner" *ngIf="successMessage">
            <i class="fas fa-check-circle"></i>
            <span>{{ successMessage }}</span>
          </div>

          <!-- Full Name (Only for registration) -->
          <div class="input-group" *ngIf="!isLoginMode">
            <label for="fullName">Full Name</label>
            <div class="input-wrapper">
              <i class="fas fa-user input-icon"></i>
              <input 
                type="text" 
                id="fullName" 
                name="fullName" 
                [(ngModel)]="authData.fullName" 
                placeholder="John Doe"
                required>
            </div>
          </div>

          <!-- Email -->
          <div class="input-group">
            <label for="email">Email Address</label>
            <div class="input-wrapper">
              <i class="fas fa-envelope input-icon"></i>
              <input 
                type="email" 
                id="email" 
                name="email" 
                [(ngModel)]="authData.email" 
                placeholder="name@company.com"
                required>
            </div>
          </div>

          <!-- Password -->
          <div class="input-group">
            <label for="password">Password</label>
            <div class="input-wrapper">
              <i class="fas fa-lock input-icon"></i>
              <input 
                type="password" 
                id="password" 
                name="password" 
                [(ngModel)]="authData.password" 
                placeholder="••••••••"
                required>
            </div>
          </div>

          <button type="submit" class="submit-btn glowing-btn" [disabled]="loading">
            <span *ngIf="!loading">{{ isLoginMode ? 'Sign In' : 'Create Account' }}</span>
            <span *ngIf="loading" class="spinner"><i class="fas fa-circle-notch fa-spin"></i> Loading...</span>
          </button>
        </form>
      </div>
    </div>
  `,
  styles: []
})
export class LoginComponent {
  isLoginMode = true;
  loading = false;
  errorMessage = '';
  successMessage = '';
  authData = {
    email: '',
    password: '',
    fullName: ''
  };

  constructor(private authService: AuthService, private router: Router) {
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/chat']);
    }
  }

  setMode(isLogin: boolean): void {
    this.isLoginMode = isLogin;
    this.errorMessage = '';
    this.successMessage = '';
  }

  onSubmit(): void {
    if (!this.authData.email || !this.authData.password) {
      this.errorMessage = 'Please fill in all required fields.';
      return;
    }

    if (!this.isLoginMode && this.authData.password.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters long.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    if (this.isLoginMode) {
      this.authService.login({
        email: this.authData.email,
        password: this.authData.password
      }).subscribe({
        next: () => {
          this.loading = false;
          this.router.navigate(['/chat']);
        },
        error: (err) => {
          this.loading = false;
          this.errorMessage = this.parseError(err);
        }
      });
    } else {
      this.authService.register({
        email: this.authData.email,
        password: this.authData.password,
        full_name: this.authData.fullName || null
      }).subscribe({
        next: () => {
          this.loading = false;
          this.successMessage = 'Registration successful! You can now sign in.';
          this.isLoginMode = true;
          this.authData.password = '';
        },
        error: (err) => {
          this.loading = false;
          this.errorMessage = this.parseError(err);
        }
      });
    }
  }

  private parseError(err: any): string {
    if (!err) return 'An unknown error occurred.';
    if (err.status === 0) {
      return 'Cannot connect to backend server. Make sure the FastAPI server is running on port 8000.';
    }
    const errorObj = err.error;
    if (errorObj) {
      if (typeof errorObj.detail === 'string') {
        return errorObj.detail;
      } else if (Array.isArray(errorObj.detail)) {
        return errorObj.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
      } else if (errorObj.message) {
        return errorObj.message;
      } else if (errorObj.errors && Array.isArray(errorObj.errors)) {
        return errorObj.errors.join(', ');
      }
    }
    return err.message || 'An unexpected error occurred.';
  }
}
