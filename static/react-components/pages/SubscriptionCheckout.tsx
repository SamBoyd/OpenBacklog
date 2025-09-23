import React from 'react';
import { CheckoutProvider } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { useNavigate } from 'react-router';
import SubscriptionCheckout from '#components/billing/SubscriptionCheckout';
import AppBackground from '#components/AppBackground';

// Initialize Stripe with the publishable key
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');

/**
 * SubscriptionCheckout page component
 * Provides the full page layout for subscription checkout with Stripe Elements context
 * @returns {React.ReactElement} The subscription checkout page
 */
const SubscriptionCheckoutPage: React.FC = () => {
  const navigate = useNavigate();

  /**
   * Handle successful subscription completion
   */
  const handleSuccess = () => {
    // Navigate to billing/subscription/complete page (to be created)
    navigate('/workspace/billing/subscription/complete');
  };

  /**
   * Handle checkout cancellation
   */
  const handleCancel = () => {
    // Navigate back to billing page
    navigate('/workspace/billing');
  };

  const fetchClientSecret = () => {
    return fetch('/api/create-checkout-session', { method: 'POST' })
      .then((response) => response.json())
      .then((json) => {
        // Handle redirect responses for users with existing subscriptions or closed accounts
        if (json.redirect) {
          // Navigate to the specified URL (typically /workspace)
          navigate(json.redirect_url);
          // Throw to prevent further processing
          throw new Error('Redirecting user');
        }
        return json.checkoutSessionClientSecret;
      })
      .catch((error) => {
        // Only re-throw if it's not our redirect "error"
        if (error.message !== 'Redirecting user') {
          throw error;
        }
      });
  };

  return (
    <CheckoutProvider
      stripe={stripePromise}
      options={{
        fetchClientSecret,
        elementsOptions: {
          appearance: {
            theme: 'night'
          }
        },
      }}
    >
      <AppBackground>
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <div className="w-full max-w-lg">
            <SubscriptionCheckout
              onSuccess={handleSuccess}
              onCancel={handleCancel}
            />
          </div>
        </div>
      </AppBackground>
    </CheckoutProvider>
  );
};

export default SubscriptionCheckoutPage;