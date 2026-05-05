import { createRouter } from '@tanstack/react-router';
import { rootRoute } from './__root';
import { indexRoute } from './index';
import { chatRoute } from './chat.$sessionId';

const routeTree = rootRoute.addChildren([indexRoute, chatRoute]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
