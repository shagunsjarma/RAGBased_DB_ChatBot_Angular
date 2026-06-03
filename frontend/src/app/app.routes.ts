import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { ChatDashboardComponent } from './components/chat-dashboard/chat-dashboard.component';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'chat', component: ChatDashboardComponent },
  { path: '**', redirectTo: 'login' }
];
