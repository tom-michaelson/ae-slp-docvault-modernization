import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <footer class="eshop-footer">
      <div class="container footer-inner">
        <span>e-ShopOnWeb. All rights reserved</span>
      </div>
    </footer>
  `,
  styles: [
    `
      .eshop-footer {
        background: var(--eshop-footer);
        color: var(--eshop-footer-text);
        padding: 2rem 0;
        margin-top: auto;
      }
      .footer-inner {
        text-align: center;
        letter-spacing: 0.05em;
      }
    `,
  ],
})
export class FooterComponent {}
