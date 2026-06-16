import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="eshop-header">
      <div class="container header-row">
        <a class="logo" routerLink="/">
          <span class="bracket">[e</span><span class="brand-top">SHOP</span
          ><span class="bracket">]</span>
          <span class="brand-bottom">OnWeb</span>
        </a>

        <nav class="header-nav">
          <a class="login-link" routerLink="/login">LOGIN</a>
          <a class="basket-link" routerLink="/basket" aria-label="Basket">
            <span class="basket-icon" aria-hidden="true">🛒</span>
            <span class="basket-count">{{ basketCount() }}</span>
          </a>
        </nav>
      </div>
    </header>
  `,
  styles: [
    `
      .eshop-header {
        background: #fff;
        border-bottom: 1px solid var(--eshop-muted);
      }
      .header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
      }
      .logo {
        display: inline-flex;
        align-items: baseline;
        gap: 0.35rem;
        font-weight: 700;
        font-size: 1.5rem;
        color: var(--eshop-text);
        text-decoration: none;
      }
      .bracket {
        color: var(--eshop-teal);
      }
      .brand-top {
        color: var(--eshop-teal);
      }
      .brand-bottom {
        font-size: 1rem;
        color: var(--eshop-text);
        margin-left: -0.25rem;
      }
      .header-nav {
        display: flex;
        align-items: center;
        gap: 2rem;
      }
      .login-link {
        color: var(--eshop-text);
        font-weight: 600;
        letter-spacing: 0.05em;
        text-decoration: none;
      }
      .basket-link {
        position: relative;
        display: inline-flex;
        align-items: center;
        color: var(--eshop-text);
        text-decoration: none;
      }
      .basket-icon {
        font-size: 1.75rem;
      }
      .basket-count {
        position: absolute;
        top: -0.35rem;
        right: -0.75rem;
        min-width: 1.5rem;
        height: 1.5rem;
        padding: 0 0.35rem;
        border-radius: 999px;
        background: var(--eshop-green);
        color: #fff;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }
    `,
  ],
})
export class HeaderComponent {
  /** Number rendered in the basket badge. Host sets this from BasketService when wired. */
  readonly basketCount = input<number>(0);
}
