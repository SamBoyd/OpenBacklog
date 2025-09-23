import { UserAccountStatus, isUserOnboarded } from './userAccountStatus';

describe('UserAccountStatus', () => {
    describe('isUserOnboarded', () => {
        it('should return false for NEW status', () => {
            expect(isUserOnboarded(UserAccountStatus.NEW)).toBe(false);
        });

        it('should return true for ACTIVE status', () => {
            expect(isUserOnboarded(UserAccountStatus.ACTIVE_SUBSCRIPTION)).toBe(true);
        });

        it('should return true for SUSPENDED status', () => {
            expect(isUserOnboarded(UserAccountStatus.SUSPENDED)).toBe(true);
        });

        it('should return true for CLOSED status', () => {
            expect(isUserOnboarded(UserAccountStatus.CLOSED)).toBe(true);
        });

        it('should return true for NO_SUBSCRIPTION status', () => {
            expect(isUserOnboarded(UserAccountStatus.NO_SUBSCRIPTION)).toBe(true);
        });

        it('should return true for METERED_BILLING status', () => {
            expect(isUserOnboarded(UserAccountStatus.METERED_BILLING)).toBe(true);
        });
    });
}); 