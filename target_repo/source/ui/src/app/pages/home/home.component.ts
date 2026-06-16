import { ChangeDetectionStrategy, Component } from '@angular/core';

/**
 * Homepage catalog list — placeholder.
 * Implementation will be generated from
 * `docs/entry-points/ui-features/homepage-catalog-list/`.
 */
@Component({
  selector: 'app-home',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="placeholder">
      <h2>Home</h2>
      <p>Catalog grid will live here.</p>
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
export class HomeComponent {}
