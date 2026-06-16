import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-hero-banner',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="hero">
      <div class="container hero-inner">
        <h1 class="hero-heading">
          <span class="line-1">ALL <em>T-SHIRTS</em></span>
          <span class="line-2">ON SALE</span>
          <span class="line-3">THIS WEEKEND</span>
        </h1>
      </div>
    </section>
  `,
  styles: [
    `
      .hero {
        background: linear-gradient(135deg, #2a6f9c 0%, #4b8db8 100%);
        color: #fff;
        height: 260px;
        display: flex;
        align-items: center;
        overflow: hidden;
      }
      .hero-inner {
        width: 100%;
      }
      .hero-heading {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.05;
        letter-spacing: 0.02em;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
      }
      em {
        color: var(--eshop-green);
        font-style: normal;
      }
      .line-3 {
        color: var(--eshop-teal);
      }
    `,
  ],
})
export class HeroBannerComponent {}
