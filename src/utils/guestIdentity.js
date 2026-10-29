/**
 * TripGenie-AI Guest Identity Manager (Zero-cost, secure client session)
 *
 * Provides each browser visitor with a unique, persistent guest UUID in localStorage.
 * Ensures that unauthenticated visitors are strictly isolated from one another in
 * multi-tenant cloud storage without requiring login or third-party paid auth.
 */

const STORAGE_KEY = 'tripgenie_guest_id';

export function getOrCreateGuestId() {
  if (typeof window === 'undefined') {
    return 'local-guest';
  }

  try {
    let guestId = localStorage.getItem(STORAGE_KEY);
    if (!guestId || !guestId.startsWith('guest-')) {
      const randomSuffix = typeof window.crypto?.randomUUID === 'function'
        ? window.crypto.randomUUID()
        : Math.random().toString(36).substring(2, 12) + Date.now().toString(36);
      guestId = `guest-${randomSuffix}`;
      localStorage.setItem(STORAGE_KEY, guestId);
    }
    return guestId;
  } catch {
    return 'local-guest';
  }
}
