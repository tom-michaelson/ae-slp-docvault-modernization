import { Routes } from '@angular/router';

import { HomeComponent } from './pages/home/home.component';
import { BasketComponent } from './pages/basket/basket.component';

export const routes: Routes = [
  { path: '', component: HomeComponent, pathMatch: 'full' },
  { path: 'basket', component: BasketComponent },
  { path: '**', redirectTo: '' },
];
