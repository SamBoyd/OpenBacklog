import { fn } from '@storybook/test';
import type { UsePaymentFormReturn } from './usePaymentForm';

/**
 * Mock implementation of usePaymentForm for Storybook
 * Provides different validation states for testing UI
 */
export const usePaymentForm = fn((): UsePaymentFormReturn => ({
  cardComplete: true,
  addressComplete: true,
  acceptedTerms: true,
  expressCheckoutReady: false,
  isFormValid: true,
  setCardComplete: fn((complete: boolean) => {
    console.log('Mock setting card complete:', complete);
  }),
  setAddressComplete: fn((complete: boolean) => {
    console.log('Mock setting address complete:', complete);
  }),
  setAcceptedTerms: fn((accepted: boolean) => {
    console.log('Mock setting terms accepted:', accepted);
  }),
  setExpressCheckoutReady: fn((ready: boolean) => {
    console.log('Mock setting express checkout ready:', ready);
  }),
  setCardError: fn((error: string | null) => {
    console.log('Mock setting card error:', error);
  }),
  validateForm: fn(() => {
    console.log('Mock validating form');
    return true;
  }),
})).mockName('usePaymentForm');

/**
 * Mock for incomplete card state
 */
export const usePaymentFormIncompleteCard = fn((): UsePaymentFormReturn => ({
  cardComplete: false,
  addressComplete: true,
  acceptedTerms: true,
  expressCheckoutReady: false,
  isFormValid: false,
  setCardComplete: fn(),
  setAddressComplete: fn(),
  setAcceptedTerms: fn(),
  setExpressCheckoutReady: fn(),
  setCardError: fn(),
  validateForm: fn(() => false),
})).mockName('usePaymentFormIncompleteCard');

/**
 * Mock for incomplete address state
 */
export const usePaymentFormIncompleteAddress = fn((): UsePaymentFormReturn => ({
  cardComplete: true,
  addressComplete: false,
  acceptedTerms: true,
  expressCheckoutReady: false,
  isFormValid: false,
  setCardComplete: fn(),
  setAddressComplete: fn(),
  setAcceptedTerms: fn(),
  setExpressCheckoutReady: fn(),
  setCardError: fn(),
  validateForm: fn(() => false),
})).mockName('usePaymentFormIncompleteAddress');

/**
 * Mock for terms not accepted state
 */
export const usePaymentFormTermsNotAccepted = fn((): UsePaymentFormReturn => ({
  cardComplete: true,
  addressComplete: true,
  acceptedTerms: false,
  expressCheckoutReady: false,
  isFormValid: false,
  setCardComplete: fn(),
  setAddressComplete: fn(),
  setAcceptedTerms: fn(),
  setExpressCheckoutReady: fn(),
  setCardError: fn(),
  validateForm: fn(() => false),
})).mockName('usePaymentFormTermsNotAccepted');

/**
 * Mock for completely invalid form state
 */
export const usePaymentFormInvalid = fn((): UsePaymentFormReturn => ({
  cardComplete: false,
  addressComplete: false,
  acceptedTerms: false,
  expressCheckoutReady: false,
  isFormValid: false,
  setCardComplete: fn(),
  setAddressComplete: fn(),
  setAcceptedTerms: fn(),
  setExpressCheckoutReady: fn(),
  setCardError: fn(),
  validateForm: fn(() => false),
})).mockName('usePaymentFormInvalid');

/**
 * Mock for express checkout ready state
 */
export const usePaymentFormExpressCheckoutReady = fn((): UsePaymentFormReturn => ({
  cardComplete: false,
  addressComplete: false,
  acceptedTerms: true,
  expressCheckoutReady: true,
  isFormValid: true,
  setCardComplete: fn(),
  setAddressComplete: fn(),
  setAcceptedTerms: fn(),
  setExpressCheckoutReady: fn(),
  setCardError: fn(),
  validateForm: fn(() => true),
})).mockName('usePaymentFormExpressCheckoutReady');