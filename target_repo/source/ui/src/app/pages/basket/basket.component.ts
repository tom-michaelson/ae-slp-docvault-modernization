import { ChangeDetectionStrategy, Component } from '@angular/core';

/**
 * Basket view page — placeholder.
 * Implementation will be generated from
 * `docs/entry-points/ui-features/basket-view-page/`.
 */
@Component({
  selector: 'app-basket',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="placeholder">
      <h2>Basket</h2>
      <p>Basket items, quantity controls, and checkout CTA will live here.</p>
    </section>
  `,
  styles: [
    `
      .placeholder {
        padding: 2rem 0;
      }
      h2 {
        margin: 0 0 0.5rem;
      }
      p {
        color: #666;
      }
    `,
  ],
})
export class BasketComponent {}
