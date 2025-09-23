/**
 * Test file to verify the user-scoped caching functionality in useBillingUsage
 * This focuses specifically on the caching behavior we added
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SafeStorage } from './useUserPreferences';

// Mock getCurrentUserId to control user context
vi.mock('#api/jwt', () => ({
  getCurrentUserId: vi.fn(),
}));

describe('SafeStorage User-Scoped Caching', () => {
  const mockUserId1 = 'user-123';
  const mockUserId2 = 'user-456';
  const mockUserAccountDetails = {
    balanceCents: 1000,
    status: 'ACTIVE',
    onboardingCompleted: true,
  };

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    // Clean up after each test
    localStorage.clear();
  });

  describe('User-scoped caching', () => {
    it('should store and retrieve user-scoped data correctly', () => {
      const validator = (value: unknown): value is typeof mockUserAccountDetails =>
        typeof value === 'object' && value !== null && 'balanceCents' in value;

      // Store data for user 1
      SafeStorage.safeSetUserScoped(
        'userAccountDetails',
        mockUserId1,
        mockUserAccountDetails,
        60000 // 1 minute TTL
      );

      // Retrieve data for user 1
      const retrieved = SafeStorage.safeGetUserScoped(
        'userAccountDetails',
        mockUserId1,
        validator,
        null
      );

      expect(retrieved).toEqual(mockUserAccountDetails);

      // Different user should not see the data
      const differentUser = SafeStorage.safeGetUserScoped(
        'userAccountDetails',
        mockUserId2,
        validator,
        null
      );

      expect(differentUser).toBeNull();
    });

    it('should handle TTL expiration correctly', () => {
      const validator = (value: unknown): value is typeof mockUserAccountDetails =>
        typeof value === 'object' && value !== null && 'balanceCents' in value;

      // Store data with very short TTL (1ms)
      SafeStorage.safeSetUserScoped(
        'userAccountDetails',
        mockUserId1,
        mockUserAccountDetails,
        1 // 1ms TTL
      );

      // Wait for expiration
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          const retrieved = SafeStorage.safeGetUserScoped(
            'userAccountDetails',
            mockUserId1,
            validator,
            null
          );

          expect(retrieved).toBeNull();
          resolve();
        }, 10); // Wait 10ms for expiration
      });
    });

    it('should clear user cache correctly', () => {
      const validator = (value: unknown): value is typeof mockUserAccountDetails =>
        typeof value === 'object' && value !== null && 'balanceCents' in value;

      // Store data for both users
      SafeStorage.safeSetUserScoped('userAccountDetails', mockUserId1, mockUserAccountDetails);
      SafeStorage.safeSetUserScoped('userAccountDetails', mockUserId2, mockUserAccountDetails);

      // Verify both are stored
      expect(SafeStorage.safeGetUserScoped('userAccountDetails', mockUserId1, validator, null))
        .toEqual(mockUserAccountDetails);
      expect(SafeStorage.safeGetUserScoped('userAccountDetails', mockUserId2, validator, null))
        .toEqual(mockUserAccountDetails);

      // Clear cache for user 1
      SafeStorage.clearUserCache(mockUserId1);

      // User 1's cache should be cleared, user 2's should remain
      expect(SafeStorage.safeGetUserScoped('userAccountDetails', mockUserId1, validator, null))
        .toBeNull();
      expect(SafeStorage.safeGetUserScoped('userAccountDetails', mockUserId2, validator, null))
        .toEqual(mockUserAccountDetails);
    });

    it('should handle null user IDs gracefully', () => {
      const validator = (value: unknown): value is typeof mockUserAccountDetails =>
        typeof value === 'object' && value !== null && 'balanceCents' in value;

      // Attempting to store/retrieve with null user ID should return default values
      SafeStorage.safeSetUserScoped('userAccountDetails', null, mockUserAccountDetails);
      const retrieved = SafeStorage.safeGetUserScoped('userAccountDetails', null, validator, null);

      expect(retrieved).toBeNull();
    });

    it('should clear expired cache entries', () => {
      // Store some expired and non-expired data
      SafeStorage.safeSetWithTTL('expiredData', 'expired', 1); // 1ms TTL
      SafeStorage.safeSetWithTTL('validData', 'valid', 60000); // 1 minute TTL

      return new Promise<void>((resolve) => {
        setTimeout(() => {
          // Run the cleanup
          SafeStorage.clearExpiredCache();

          // Verify expired data is removed and valid data remains
          expect(localStorage.getItem('expiredData')).toBeNull();
          expect(localStorage.getItem('validData')).not.toBeNull();
          resolve();
        }, 10); // Wait for expiration
      });
    });
  });

  describe('Cache key format', () => {
    it('should generate correct cache keys', () => {
      SafeStorage.safeSetUserScoped('testKey', 'user123', 'testValue');
      
      // Check that the key follows the expected format
      const expectedKey = 'testKey-user123';
      expect(localStorage.getItem(expectedKey)).not.toBeNull();
    });
  });
});