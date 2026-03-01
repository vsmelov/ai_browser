/**
 * Fallback env.ts for build when zod is undefined in vite-node context.
 * Used by build_ponyai_extension.sh: copied to apps/agent/lib/env.ts before wxt build, then restored.
 */
// @ts-expect-error import.meta.env is injected by Vite
const raw: Record<string, unknown> = typeof import.meta !== 'undefined' && import.meta.env != null ? import.meta.env : {}

export const env = {
  VITE_BROWSEROS_SERVER_PORT: raw.VITE_BROWSEROS_SERVER_PORT != null ? Number(raw.VITE_BROWSEROS_SERVER_PORT) : undefined,
  VITE_PUBLIC_POSTHOG_KEY: typeof raw.VITE_PUBLIC_POSTHOG_KEY === 'string' ? raw.VITE_PUBLIC_POSTHOG_KEY : undefined,
  VITE_PUBLIC_POSTHOG_HOST: typeof raw.VITE_PUBLIC_POSTHOG_HOST === 'string' ? raw.VITE_PUBLIC_POSTHOG_HOST : undefined,
  VITE_PUBLIC_SENTRY_DSN: typeof raw.VITE_PUBLIC_SENTRY_DSN === 'string' ? raw.VITE_PUBLIC_SENTRY_DSN : undefined,
  VITE_PUBLIC_BROWSEROS_API: typeof raw.VITE_PUBLIC_BROWSEROS_API === 'string' ? raw.VITE_PUBLIC_BROWSEROS_API : 'https://api.browseros.com',
  PROD: raw.PROD === true || raw.MODE === 'production',
}
